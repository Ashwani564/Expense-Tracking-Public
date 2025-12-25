"""
Extract transactions from Chase PDF statements using Gemini API.
Processes all PDFs in PDF/2040 and PDF/7557 folders.

Uses the new Google Gen AI SDK with Gemini 3 Flash Preview model.
Documentation: https://ai.google.dev/gemini-api/docs
"""

import os
import csv
import json
from google import genai
from google.genai import types
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API client
GEMINI_API_KEY = os.getenv("GEMINI_API")
client = genai.Client(api_key=GEMINI_API_KEY)

# Model to use - Gemini 3 Flash Preview
MODEL_NAME = "gemini-3-flash-preview"

EXTRACTION_PROMPT = """
Extract ALL credit card transactions from this bank statement PDF.

For each transaction, extract:
1. Transaction Date (in YYYY-MM-DD format)
2. Description (merchant name and location)
3. Amount (as a positive number for purchases, include cents)
4. Category (infer from merchant: Dining, Gas, Merchandise, Entertainment, Travel, Services, Healthcare, Other)

IMPORTANT:
- Include ALL transactions, don't skip any
- Convert dates to YYYY-MM-DD format
- For amounts, use positive numbers for purchases/debits
- Skip payment transactions (like "AUTOMATIC PAYMENT - THANK YOU")
- Skip any fees or interest charges

Return the data as a JSON array with objects having these exact keys:
- "date": "YYYY-MM-DD"
- "description": "merchant description"
- "amount": numeric value (no $ sign)
- "category": "category name"

Example output:
[
    {"date": "2025-01-15", "description": "SHELL OIL 523769600 STARKVILLE MS", "amount": 45.23, "category": "Gas"},
    {"date": "2025-01-16", "description": "WALMART STORE #112", "amount": 67.89, "category": "Merchandise"}
]

Return ONLY the JSON array, no other text.
"""


def try_fix_truncated_json(json_str: str) -> str:
    """Attempt to fix truncated JSON by closing open brackets."""
    # Count open brackets
    open_braces = json_str.count('{') - json_str.count('}')
    open_brackets = json_str.count('[') - json_str.count(']')
    
    # If we're in the middle of a string, try to close it
    # Find if there's an unclosed string
    in_string = False
    escaped = False
    for char in json_str:
        if escaped:
            escaped = False
            continue
        if char == '\\':
            escaped = True
            continue
        if char == '"':
            in_string = not in_string
    
    fixed = json_str
    
    # Close unclosed string
    if in_string:
        fixed += '"'
    
    # Remove trailing comma if present after the last complete value
    fixed = fixed.rstrip()
    if fixed.endswith(','):
        fixed = fixed[:-1]
    
    # Close any open braces
    fixed += '}' * open_braces
    
    # Close any open brackets
    fixed += ']' * open_brackets
    
    return fixed


def extract_transactions_from_pdf(pdf_path: str, retry_count: int = 0) -> list[dict]:
    """Extract transactions from a single PDF using Gemini."""
    print(f"Processing: {pdf_path}")
    
    # Read the PDF file
    file_path = Path(pdf_path)
    
    # Upload the PDF using the Files API
    uploaded_file = client.files.upload(file=file_path)
    
    # Generate content with the PDF
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[uploaded_file, EXTRACTION_PROMPT],
        config=types.GenerateContentConfig(
            temperature=0.1,
            max_output_tokens=65536,  # Large token limit for multi-page statements
        )
    )
    
    # Parse the response
    response_text = response.text.strip()
    
    # Clean up the response - remove markdown code blocks if present
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        # Remove first line (```json) and last line (```)
        if lines[-1].strip() == "```":
            response_text = "\n".join(lines[1:-1])
        else:
            response_text = "\n".join(lines[1:])
    
    # Also handle if ``` is at the end without newline
    if response_text.endswith("```"):
        response_text = response_text[:-3]
    
    try:
        transactions = json.loads(response_text)
        print(f"  Found {len(transactions)} transactions")
        return transactions
    except json.JSONDecodeError as e:
        print(f"  Warning: JSON parsing issue, attempting to fix...")
        
        # Try to fix truncated JSON
        try:
            fixed_json = try_fix_truncated_json(response_text)
            transactions = json.loads(fixed_json)
            print(f"  Fixed! Found {len(transactions)} transactions")
            return transactions
        except json.JSONDecodeError:
            pass
        
        # Retry once if we haven't already
        if retry_count < 1:
            print(f"  Retrying extraction...")
            return extract_transactions_from_pdf(pdf_path, retry_count + 1)
        
        print(f"  Error parsing JSON: {e}")
        print(f"  Response was: {response_text[:500]}...")
        return []


def process_all_pdfs(base_dir: str) -> list[dict]:
    """Process all Chase PDFs and return combined transactions."""
    all_transactions = []
    
    pdf_folders = ["PDF/2040", "PDF/7557"]
    
    for folder in pdf_folders:
        folder_path = Path(base_dir) / folder
        if not folder_path.exists():
            print(f"Warning: Folder {folder_path} does not exist")
            continue
            
        card_suffix = folder.split("/")[1]  # "2040" or "7557"
        
        for pdf_file in sorted(folder_path.glob("*.pdf")):
            transactions = extract_transactions_from_pdf(str(pdf_file))
            
            # Add card identifier and source to each transaction
            for txn in transactions:
                txn["card"] = f"Chase-{card_suffix}"
                txn["source"] = pdf_file.name
            
            all_transactions.extend(transactions)
    
    return all_transactions


def save_to_csv(transactions: list[dict], output_path: str):
    """Save transactions to CSV file."""
    if not transactions:
        print("No transactions to save")
        return
    
    # Sort by date
    transactions.sort(key=lambda x: x.get("date", ""))
    
    fieldnames = ["date", "description", "amount", "category", "card", "source"]
    
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(transactions)
    
    print(f"Saved {len(transactions)} transactions to {output_path}")


def main():
    """Main function to extract Chase transactions."""
    base_dir = Path(__file__).parent.parent
    output_dir = base_dir / "csv"
    output_dir.mkdir(exist_ok=True)
    
    print("=" * 60)
    print("Extracting Chase Credit Card Transactions")
    print("=" * 60)
    
    # Process all PDFs
    transactions = process_all_pdfs(str(base_dir))
    
    # Save to CSV
    output_path = output_dir / "Chase_Extracted_Transactions.csv"
    save_to_csv(transactions, str(output_path))
    
    print("\nDone!")
    print(f"Total transactions extracted: {len(transactions)}")


if __name__ == "__main__":
    main()
