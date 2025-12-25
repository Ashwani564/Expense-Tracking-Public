"""
Generate expense diagrams for specific trips.
Creates visualizations for each trip with breakdown by category.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from pathlib import Path
from datetime import datetime, timedelta


# Define trips with date ranges
TRIPS = {
    "NYC Trip": {
        "start": "2025-07-01",
        "end": "2025-07-07",
        "description": "New York City - July 1-7, 2025"
    },
    "Atlanta (August)": {
        "start": "2025-08-16",
        "end": "2025-08-16",
        "description": "Atlanta - August 16, 2025 (Same Day)"
    },
    "Dallas Trip": {
        "start": "2025-10-03",
        "end": "2025-10-05",
        "description": "Dallas - October 3-5, 2025"
    },
    "North Carolina": {
        "start": "2025-10-16",
        "end": "2025-10-19",
        "description": "North Carolina - October 16-19, 2025"
    },
    "Memphis (October)": {
        "start": "2025-10-20",
        "end": "2025-10-20",
        "description": "Memphis - October 20, 2025 (Same Day)"
    },
    "Atlanta (November)": {
        "start": "2025-11-07",
        "end": "2025-11-09",
        "description": "Atlanta - November 7-9, 2025"
    },
    "Memphis (November)": {
        "start": "2025-11-25",
        "end": "2025-11-26",
        "description": "Memphis - November 25-26, 2025"
    }
}

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")


def load_transactions(csv_path: str) -> pd.DataFrame:
    """Load merged transactions CSV."""
    df = pd.read_csv(csv_path)
    df["date"] = pd.to_datetime(df["date"])
    return df


def filter_trip_transactions(df: pd.DataFrame, start_date: str, end_date: str) -> pd.DataFrame:
    """Filter transactions for a specific date range.
    
    Also excludes Walmart transactions over $30 as they are likely 
    pre-ordered items that settled during the trip.
    """
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date) + timedelta(days=1)  # Include end date
    
    mask = (df["date"] >= start) & (df["date"] < end)
    trip_df = df[mask].copy()
    
    # Exclude Walmart transactions over $30 (likely pre-ordered items)
    walmart_over_30_mask = (trip_df["label"] == "Walmart") & (trip_df["amount"] > 30)
    excluded_count = walmart_over_30_mask.sum()
    if excluded_count > 0:
        excluded_total = trip_df.loc[walmart_over_30_mask, "amount"].sum()
        print(f"  Excluding {excluded_count} Walmart transactions over $30 (${excluded_total:.2f} total)")
    
    trip_df = trip_df[~walmart_over_30_mask]
    
    return trip_df


def create_trip_summary_figure(trip_df: pd.DataFrame, trip_name: str, trip_desc: str, output_dir: Path):
    """Create a comprehensive trip summary figure with multiple charts."""
    if trip_df.empty:
        print(f"  No transactions found for {trip_name}")
        return None
    
    # Create figure with subplots
    fig = plt.figure(figsize=(16, 12))
    fig.suptitle(f"Expense Report: {trip_desc}", fontsize=16, fontweight='bold', y=0.98)
    
    # Calculate totals
    total_spent = trip_df["amount"].sum()
    num_transactions = len(trip_df)
    
    # Add summary text
    summary_text = f"Total Spent: ${total_spent:.2f} | Transactions: {num_transactions}"
    fig.text(0.5, 0.93, summary_text, ha='center', fontsize=12, style='italic')
    
    # 1. Pie Chart - Expenses by Category/Label
    ax1 = fig.add_subplot(2, 2, 1)
    label_totals = trip_df.groupby("label")["amount"].sum().sort_values(ascending=False)
    
    # Create pie chart
    colors = plt.cm.Set3(range(len(label_totals)))
    wedges, texts, autotexts = ax1.pie(
        label_totals.values,
        labels=None,
        autopct=lambda pct: f'${pct/100*total_spent:.2f}\n({pct:.1f}%)' if pct > 5 else '',
        colors=colors,
        startangle=90
    )
    ax1.set_title("Expenses by Category", fontsize=12, fontweight='bold')
    
    # Add legend
    ax1.legend(
        wedges,
        [f"{label}: ${amount:.2f}" for label, amount in label_totals.items()],
        loc="center left",
        bbox_to_anchor=(1, 0.5),
        fontsize=9
    )
    
    # 2. Bar Chart - Expenses by Card
    ax2 = fig.add_subplot(2, 2, 2)
    card_totals = trip_df.groupby("card")["amount"].sum().sort_values(ascending=True)
    
    bars = ax2.barh(card_totals.index, card_totals.values, color=sns.color_palette("viridis", len(card_totals)))
    ax2.set_xlabel("Amount ($)")
    ax2.set_title("Expenses by Card", fontsize=12, fontweight='bold')
    
    # Add value labels
    for bar, val in zip(bars, card_totals.values):
        ax2.text(val + 0.5, bar.get_y() + bar.get_height()/2, f'${val:.2f}', va='center', fontsize=10)
    
    # 3. Daily Expenses Timeline
    ax3 = fig.add_subplot(2, 1, 2)
    daily_totals = trip_df.groupby(trip_df["date"].dt.date)["amount"].sum()
    
    if len(daily_totals) > 1:
        ax3.bar(daily_totals.index, daily_totals.values, color='steelblue', alpha=0.7, edgecolor='navy')
        ax3.plot(daily_totals.index, daily_totals.values, 'ro-', markersize=8)
    else:
        ax3.bar(daily_totals.index, daily_totals.values, color='steelblue', alpha=0.7, edgecolor='navy', width=0.3)
    
    ax3.set_xlabel("Date")
    ax3.set_ylabel("Amount ($)")
    ax3.set_title("Daily Expenses", fontsize=12, fontweight='bold')
    
    # Format x-axis dates
    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    plt.xticks(rotation=45)
    
    # Add value labels on bars
    for date, val in daily_totals.items():
        ax3.text(date, val + 1, f'${val:.2f}', ha='center', fontsize=9)
    
    plt.tight_layout(rect=[0, 0, 1, 0.92])
    
    # Save figure
    safe_name = trip_name.replace(" ", "_").replace("(", "").replace(")", "")
    output_path = output_dir / f"{safe_name}_expenses.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"  Saved: {output_path}")
    return output_path


def create_transaction_details_table(trip_df: pd.DataFrame, trip_name: str, output_dir: Path):
    """Create a detailed transaction table image."""
    if trip_df.empty:
        return None
    
    # Sort by date and amount
    trip_df = trip_df.sort_values(["date", "amount"], ascending=[True, False])
    
    # Create figure
    fig, ax = plt.subplots(figsize=(14, max(4, len(trip_df) * 0.4)))
    ax.axis('off')
    
    # Prepare table data
    table_data = []
    for _, row in trip_df.iterrows():
        table_data.append([
            row["date"].strftime("%Y-%m-%d"),
            row["description"][:40] + "..." if len(str(row["description"])) > 40 else row["description"],
            f"${row['amount']:.2f}",
            row["label"],
            row["card"]
        ])
    
    # Create table
    table = ax.table(
        cellText=table_data,
        colLabels=["Date", "Description", "Amount", "Category", "Card"],
        cellLoc='left',
        loc='center',
        colWidths=[0.12, 0.4, 0.12, 0.18, 0.18]
    )
    
    # Style table
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.5)
    
    # Style header
    for i in range(5):
        table[(0, i)].set_facecolor('#4472C4')
        table[(0, i)].set_text_props(color='white', fontweight='bold')
    
    # Alternate row colors
    for i in range(1, len(table_data) + 1):
        color = '#E7E6E6' if i % 2 == 0 else 'white'
        for j in range(5):
            table[(i, j)].set_facecolor(color)
    
    safe_name = trip_name.replace(" ", "_").replace("(", "").replace(")", "")
    
    plt.title(f"Transaction Details: {trip_name}", fontsize=14, fontweight='bold', pad=20)
    
    output_path = output_dir / f"{safe_name}_details.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"  Saved: {output_path}")
    return output_path


def create_all_trips_comparison(df: pd.DataFrame, output_dir: Path):
    """Create a comparison chart of all trips."""
    trip_totals = []
    
    for trip_name, trip_info in TRIPS.items():
        trip_df = filter_trip_transactions(df, trip_info["start"], trip_info["end"])
        if not trip_df.empty:
            trip_totals.append({
                "trip": trip_name,
                "total": trip_df["amount"].sum(),
                "transactions": len(trip_df),
                "start": trip_info["start"]
            })
    
    if not trip_totals:
        print("No trip data to compare")
        return None
    
    trip_summary = pd.DataFrame(trip_totals)
    trip_summary = trip_summary.sort_values("start")
    
    # Create figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("Trip Expenses Comparison - 2025", fontsize=16, fontweight='bold')
    
    # Bar chart of total expenses
    colors = plt.cm.tab10(range(len(trip_summary)))
    bars = ax1.bar(trip_summary["trip"], trip_summary["total"], color=colors)
    ax1.set_ylabel("Total Expenses ($)")
    ax1.set_title("Total Expenses by Trip")
    plt.sca(ax1)
    plt.xticks(rotation=45, ha='right')
    
    # Add value labels
    for bar, val in zip(bars, trip_summary["total"]):
        ax1.text(bar.get_x() + bar.get_width()/2, val + 2, f'${val:.2f}', 
                ha='center', va='bottom', fontsize=9)
    
    # Pie chart of expenses distribution
    ax2.pie(trip_summary["total"], labels=trip_summary["trip"], autopct='%1.1f%%',
            colors=colors, startangle=90)
    ax2.set_title("Expense Distribution")
    
    plt.tight_layout()
    
    output_path = output_dir / "All_Trips_Comparison.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"Saved: {output_path}")
    return output_path


def main():
    """Main function to generate all trip diagrams."""
    base_dir = Path(__file__).parent.parent
    csv_dir = base_dir / "csv"
    output_dir = base_dir / "trip_diagrams"
    output_dir.mkdir(exist_ok=True)
    
    # Load merged transactions
    merged_csv = csv_dir / "All_Transactions_Merged.csv"
    
    if not merged_csv.exists():
        print(f"Error: {merged_csv} not found. Run merge_transactions.py first.")
        return
    
    print("=" * 60)
    print("Generating Trip Expense Diagrams")
    print("=" * 60)
    
    df = load_transactions(str(merged_csv))
    print(f"Loaded {len(df)} total transactions\n")
    
    # Generate diagrams for each trip
    for trip_name, trip_info in TRIPS.items():
        print(f"\nProcessing: {trip_name}")
        print(f"  Date Range: {trip_info['start']} to {trip_info['end']}")
        
        trip_df = filter_trip_transactions(df, trip_info["start"], trip_info["end"])
        print(f"  Found {len(trip_df)} transactions, Total: ${trip_df['amount'].sum():.2f}")
        
        if not trip_df.empty:
            # Create summary figure
            create_trip_summary_figure(trip_df, trip_name, trip_info["description"], output_dir)
            
            # Create transaction details table
            create_transaction_details_table(trip_df, trip_name, output_dir)
    
    # Create comparison chart
    print(f"\nGenerating comparison chart...")
    create_all_trips_comparison(df, output_dir)
    
    print(f"\n{'=' * 60}")
    print(f"All diagrams saved to: {output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
