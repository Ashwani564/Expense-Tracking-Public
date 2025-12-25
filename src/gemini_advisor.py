"""
Gemini Financial Advisor - Analyzes expense charts and provides personalized advice.
Uses Google Gemini API to review spending patterns and create a survival budget plan.
"""

import os
import base64
from pathlib import Path
from google import genai
from google.genai import types
import pandas as pd
from dotenv import load_dotenv


def encode_image(image_path: str) -> str:
    """Encode image to base64."""
    with open(image_path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


def load_transaction_summary(csv_path: str) -> dict:
    """Load and summarize transaction data."""
    df = pd.read_csv(csv_path)
    df["date"] = pd.to_datetime(df["date"])
    
    # Calculate key metrics
    total_spending = df["amount"].sum()
    months_covered = (df["date"].max() - df["date"].min()).days / 30
    monthly_avg = total_spending / max(months_covered, 1)
    
    # Category breakdown
    category_totals = df.groupby("label")["amount"].sum().sort_values(ascending=False)
    
    # Top spending categories
    top_categories = category_totals.head(15).to_dict()
    
    # Calculate monthly averages for key categories
    monthly_category_avg = {cat: amt / max(months_covered, 1) for cat, amt in top_categories.items()}
    
    return {
        "total_spending": total_spending,
        "months_covered": months_covered,
        "monthly_average": monthly_avg,
        "top_categories": top_categories,
        "monthly_category_avg": monthly_category_avg,
        "transaction_count": len(df),
        "date_range": f"{df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}"
    }


def get_financial_advice(income: float = 900, rent: float = 450):
    """Get personalized financial advice from Gemini based on spending analysis."""
    
    base_dir = Path(__file__).parent.parent
    csv_path = base_dir / "csv" / "All_Transactions_Merged.csv"
    charts_dir = base_dir / "overall_diagrams"
    
    # Load transaction summary
    print("Loading transaction data...")
    summary = load_transaction_summary(str(csv_path))
    
    # Collect all chart images
    print("Loading expense charts...")
    chart_files = list(charts_dir.glob("*.png"))
    
    # Initialize Gemini client
    # Load from .env file
    load_dotenv(base_dir / ".env")
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API")
    if not api_key:
        # Try reading directly from .env file
        env_file = base_dir / ".env"
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    if line.startswith("GEMINI_API"):
                        api_key = line.split("=")[1].strip()
                        break
    
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment or .env file")
    
    client = genai.Client(api_key=api_key)
    
    # Build the prompt
    remaining_budget = income - rent
    
    prompt = f"""You are a compassionate and practical financial advisor helping a graduate student survive on a very tight budget.

## FINANCIAL SITUATION:
- **Monthly Income:** ${income:.2f}
- **Rent:** ${rent:.2f} (fixed, non-negotiable)
- **Remaining for ALL other expenses:** ${remaining_budget:.2f}

## SPENDING DATA ANALYSIS:
Based on the attached expense charts and transaction data:

- **Total Spending Analyzed:** ${summary['total_spending']:.2f}
- **Period Covered:** {summary['date_range']} ({summary['months_covered']:.1f} months)
- **Current Monthly Average Spending:** ${summary['monthly_average']:.2f}
- **Total Transactions:** {summary['transaction_count']}

### Top Spending Categories (Total & Monthly Average):
"""
    
    for cat, total in summary['top_categories'].items():
        monthly = summary['monthly_category_avg'][cat]
        prompt += f"- **{cat}:** ${total:.2f} total (${monthly:.2f}/month avg)\n"
    
    prompt += f"""

## YOUR TASK:
Analyze the attached expense charts showing my spending patterns. Based on this data and my ${remaining_budget:.2f}/month budget (after rent), provide:

### 1. REALITY CHECK
- Am I currently overspending? By how much?
- What's my biggest problem area?
- What expenses are absolutely killing my budget?

### 2. SURVIVAL BUDGET PLAN
Create a realistic monthly budget for ${remaining_budget:.2f} that covers essentials:
- Food (groceries vs eating out)
- Transportation
- Utilities (electricity)
- Phone
- Health insurance
- Personal care
- Emergency buffer

### 3. IMMEDIATE CUTS TO MAKE
List specific expenses from my data that I should:
- **ELIMINATE completely** (with estimated monthly savings)
- **REDUCE significantly** (with target amounts)
- **Keep but optimize** (with tips)

### 4. SPECIFIC WARNINGS
Based on my charts:
- Call out my worst spending habits by name
- Be brutally honest about vending machines, gas station snacks, DoorDash, etc.
- Tell me the hard truth about what I need to stop doing

### 5. WEEKLY SPENDING ALLOWANCE
Break down my ${remaining_budget:.2f}/month into:
- Weekly cash allowance for discretionary spending
- Which expenses should be on autopay vs cash-only

### 6. 30-DAY CHALLENGE
Give me a specific 30-day challenge to get my spending under control.

Be direct, specific, and reference actual numbers from my spending data. Don't sugarcoat anything - I need to hear the truth to survive.
"""

    # Build content parts with images
    content_parts = [types.Part.from_text(text=prompt)]
    
    # Add chart images (limit to most important ones to stay within token limits)
    priority_charts = [
        "Category_Breakdown.png",
        "Other_Categories_Breakdown.png",
        "Monthly_Spending_Trends.png",
        "Restaurant_Breakdown.png",
        "Vending_Machine_Analysis.png",
        "Gas_Station_Analysis.png",
        "Summary_Dashboard.png"
    ]
    
    for chart_name in priority_charts:
        chart_path = charts_dir / chart_name
        if chart_path.exists():
            print(f"  Adding chart: {chart_name}")
            image_data = encode_image(str(chart_path))
            content_parts.append(
                types.Part.from_bytes(
                    data=base64.standard_b64decode(image_data),
                    mime_type="image/png"
                )
            )
    
    print("\nConsulting Gemini Financial Advisor...")
    print("=" * 60)
    
    # Call Gemini API
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[types.Content(role="user", parts=content_parts)],
        config=types.GenerateContentConfig(
            temperature=0.7,
            max_output_tokens=4000,
        )
    )
    
    advice = response.text
    
    # Print the advice
    print("\n" + "=" * 60)
    print("💰 GEMINI FINANCIAL ADVISOR REPORT 💰")
    print("=" * 60)
    print(f"\nBudget: ${income}/month income | ${rent} rent | ${remaining_budget} remaining")
    print("=" * 60 + "\n")
    print(advice)
    
    # Save the advice to a file
    output_path = base_dir / "financial_advice.md"
    with open(output_path, "w") as f:
        f.write(f"# Financial Advisor Report\n\n")
        f.write(f"**Generated:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write(f"## Budget Overview\n")
        f.write(f"- Monthly Income: ${income:.2f}\n")
        f.write(f"- Rent: ${rent:.2f}\n")
        f.write(f"- Remaining Budget: ${remaining_budget:.2f}\n\n")
        f.write(f"---\n\n")
        f.write(advice)
    
    print(f"\n{'=' * 60}")
    print(f"📄 Full report saved to: {output_path}")
    print("=" * 60)
    
    return advice


def main():
    """Main function to run the financial advisor."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Gemini Financial Advisor")
    parser.add_argument("--income", type=float, default=900, help="Monthly income (default: 900)")
    parser.add_argument("--rent", type=float, default=450, help="Monthly rent (default: 450)")
    args = parser.parse_args()
    
    try:
        get_financial_advice(income=args.income, rent=args.rent)
    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()
