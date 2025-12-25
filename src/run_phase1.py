"""
Main script to run the complete Phase 1 pipeline.
1. Extract transactions from Chase PDFs using Gemini
2. Merge all CSVs (CapitalOne, Discover, Chase)
3. Generate trip expense diagrams
4. Generate overall expense diagrams
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from extract_chase_transactions import main as extract_chase
from merge_transactions import main as merge_all
from generate_trip_diagrams import main as generate_trip_diagrams
from generate_overall_diagrams import main as generate_overall_diagrams


def main():
    """Run the complete Phase 1 pipeline."""
    print("=" * 70)
    print("   CREDIT CARD EXPENSE TRACKER - PHASE 1")
    print("=" * 70)
    
    print("\n" + "=" * 70)
    print("   STEP 1: Extract Chase Transactions from PDFs")
    print("=" * 70 + "\n")
    extract_chase()
    
    print("\n" + "=" * 70)
    print("   STEP 2: Merge All Transactions")
    print("=" * 70 + "\n")
    merge_all()
    
    print("\n" + "=" * 70)
    print("   STEP 3: Generate Trip Expense Diagrams")
    print("=" * 70 + "\n")
    generate_trip_diagrams()
    
    print("\n" + "=" * 70)
    print("   STEP 4: Generate Overall Expense Diagrams")
    print("=" * 70 + "\n")
    generate_overall_diagrams()
    
    print("\n" + "=" * 70)
    print("   PHASE 1 COMPLETE!")
    print("=" * 70)
    print("\nOutput files:")
    print("  - csv/Chase_Extracted_Transactions.csv")
    print("  - csv/All_Transactions_Merged.csv")
    print("  - trip_diagrams/*.png (trip expense charts)")
    print("  - overall_diagrams/*.png (overall expense analysis)")


if __name__ == "__main__":
    main()
