"""
Generate overall expense analysis diagrams.
Creates visualizations for spending patterns, categories, and trends.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import numpy as np
from pathlib import Path
from datetime import datetime


# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")


def load_transactions(csv_path: str) -> pd.DataFrame:
    """Load merged transactions CSV."""
    df = pd.read_csv(csv_path)
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M")
    df["week"] = df["date"].dt.isocalendar().week
    df["day_of_week"] = df["date"].dt.day_name()
    return df


def create_monthly_spending_chart(df: pd.DataFrame, output_dir: Path):
    """Create monthly spending trends chart."""
    monthly = df.groupby(df["date"].dt.to_period("M"))["amount"].sum()
    
    fig, ax = plt.subplots(figsize=(14, 6))
    
    x_labels = [str(m) for m in monthly.index]
    bars = ax.bar(x_labels, monthly.values, color='steelblue', alpha=0.7, edgecolor='navy')
    ax.plot(x_labels, monthly.values, 'ro-', markersize=8)
    
    ax.set_xlabel("Month")
    ax.set_ylabel("Total Spending ($)")
    ax.set_title("Monthly Spending Trends - 2025", fontsize=14, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    
    # Add value labels
    for bar, val in zip(bars, monthly.values):
        ax.text(bar.get_x() + bar.get_width()/2, val + 10, f'${val:.0f}', 
                ha='center', va='bottom', fontsize=9)
    
    # Add average line
    avg = monthly.mean()
    ax.axhline(y=avg, color='red', linestyle='--', label=f'Average: ${avg:.2f}')
    ax.legend()
    
    plt.tight_layout()
    output_path = output_dir / "Monthly_Spending_Trends.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Saved: {output_path}")


def create_category_breakdown(df: pd.DataFrame, output_dir: Path):
    """Create spending by category pie chart."""
    category_totals = df.groupby("label")["amount"].sum().sort_values(ascending=False)
    
    # Get top 10 categories, group rest as "Other"
    top_10 = category_totals.head(10)
    other = category_totals[10:].sum()
    if other > 0:
        top_10["Other Categories"] = other
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    fig.suptitle("Spending by Category", fontsize=16, fontweight='bold')
    
    # Pie chart
    colors = plt.cm.Set3(np.linspace(0, 1, len(top_10)))
    wedges, texts, autotexts = ax1.pie(
        top_10.values,
        labels=None,
        autopct=lambda pct: f'{pct:.1f}%' if pct > 3 else '',
        colors=colors,
        startangle=90
    )
    ax1.set_title("Distribution")
    ax1.legend(
        wedges,
        [f"{label}: ${amount:.2f}" for label, amount in top_10.items()],
        loc="center left",
        bbox_to_anchor=(1, 0.5),
        fontsize=9
    )
    
    # Horizontal bar chart
    top_10_sorted = top_10.sort_values(ascending=True)
    bars = ax2.barh(top_10_sorted.index, top_10_sorted.values, color=colors[::-1])
    ax2.set_xlabel("Amount ($)")
    ax2.set_title("Top Categories by Spending")
    
    for bar, val in zip(bars, top_10_sorted.values):
        ax2.text(val + 5, bar.get_y() + bar.get_height()/2, f'${val:.2f}', 
                va='center', fontsize=9)
    
    plt.tight_layout()
    output_path = output_dir / "Category_Breakdown.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Saved: {output_path}")


def create_card_spending_chart(df: pd.DataFrame, output_dir: Path):
    """Create spending by card chart."""
    card_totals = df.groupby("card")["amount"].sum().sort_values(ascending=False)
    card_counts = df.groupby("card").size()
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("Spending by Credit Card", fontsize=16, fontweight='bold')
    
    # Total spending by card
    colors = plt.cm.tab10(range(len(card_totals)))
    bars1 = ax1.bar(card_totals.index, card_totals.values, color=colors)
    ax1.set_ylabel("Total Spending ($)")
    ax1.set_title("Total Amount")
    plt.sca(ax1)
    plt.xticks(rotation=45, ha='right')
    
    for bar, val in zip(bars1, card_totals.values):
        ax1.text(bar.get_x() + bar.get_width()/2, val + 10, f'${val:.0f}', 
                ha='center', va='bottom', fontsize=10)
    
    # Transaction count by card
    bars2 = ax2.bar(card_counts.index, card_counts.values, color=colors)
    ax2.set_ylabel("Number of Transactions")
    ax2.set_title("Transaction Count")
    plt.sca(ax2)
    plt.xticks(rotation=45, ha='right')
    
    for bar, val in zip(bars2, card_counts.values):
        ax2.text(bar.get_x() + bar.get_width()/2, val + 2, str(val), 
                ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    output_path = output_dir / "Card_Spending.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Saved: {output_path}")


def create_restaurant_breakdown(df: pd.DataFrame, output_dir: Path):
    """Create restaurant/food spending breakdown."""
    # Filter for food-related labels
    food_labels = [
        "DoorDash", "Grubhub", "Uber Eats", "Wendy's", "McDonald's", 
        "Taco Bell", "Burger King", "Chick-fil-A", "Pizza", "Domino's",
        "Starbucks", "High Ground Coffee", "Dunkin", "Cook Out", 
        "Waffle House", "Chili's", "Buffalo Wild Wings", "Panda Express",
        "Raising Cane's", "Thai Restaurant", "TopGolf", "Boardtown Pies",
        "Dave's Dark Horse", "Dining", "Restaurants"
    ]
    
    food_df = df[df["label"].isin(food_labels)]
    food_totals = food_df.groupby("label")["amount"].sum().sort_values(ascending=False)
    
    if food_totals.empty:
        print("No restaurant data to plot")
        return
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    fig.suptitle(f"Restaurant & Food Spending Analysis\nTotal: ${food_totals.sum():.2f}", 
                 fontsize=16, fontweight='bold')
    
    # Horizontal bar chart
    colors = plt.cm.Spectral(np.linspace(0, 1, len(food_totals)))
    bars = ax1.barh(food_totals.index, food_totals.values, color=colors)
    ax1.set_xlabel("Amount ($)")
    ax1.set_title("Spending by Restaurant/Service")
    
    for bar, val in zip(bars, food_totals.values):
        ax1.text(val + 1, bar.get_y() + bar.get_height()/2, f'${val:.2f}', 
                va='center', fontsize=9)
    
    # Pie chart for delivery vs dine-in
    delivery_labels = ["DoorDash", "Grubhub", "Uber Eats"]
    delivery_total = food_df[food_df["label"].isin(delivery_labels)]["amount"].sum()
    other_total = food_totals.sum() - delivery_total
    
    ax2.pie([delivery_total, other_total], 
            labels=[f"Delivery Apps\n${delivery_total:.2f}", f"Other Food\n${other_total:.2f}"],
            autopct='%1.1f%%',
            colors=['#ff6b6b', '#4ecdc4'],
            startangle=90,
            explode=(0.05, 0))
    ax2.set_title("Delivery vs Other Food")
    
    plt.tight_layout()
    output_path = output_dir / "Restaurant_Breakdown.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Saved: {output_path}")


def create_gas_station_analysis(df: pd.DataFrame, output_dir: Path):
    """Create gas station spending analysis."""
    gas_df = df[df["label"].isin(["Gas Station Indiscretion", "Gasoline"])]
    
    if gas_df.empty:
        print("No gas station data to plot")
        return
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f"Gas Station Spending Analysis\nTotal: ${gas_df['amount'].sum():.2f}", 
                 fontsize=16, fontweight='bold')
    
    # Monthly gas spending
    ax1 = axes[0, 0]
    monthly_gas = gas_df.groupby(gas_df["date"].dt.to_period("M"))["amount"].sum()
    ax1.bar([str(m) for m in monthly_gas.index], monthly_gas.values, color='orange', alpha=0.7)
    ax1.set_xlabel("Month")
    ax1.set_ylabel("Amount ($)")
    ax1.set_title("Monthly Gas Station Spending")
    plt.sca(ax1)
    plt.xticks(rotation=45, ha='right')
    
    # Indiscretion vs Actual Gas
    ax2 = axes[0, 1]
    label_totals = gas_df.groupby("label")["amount"].sum()
    colors = ['#e74c3c', '#2ecc71']
    ax2.pie(label_totals.values, labels=label_totals.index, autopct='%1.1f%%',
            colors=colors, startangle=90)
    ax2.set_title("Snacks/Drinks vs Fuel")
    
    # Transaction amount distribution
    ax3 = axes[1, 0]
    ax3.hist(gas_df["amount"], bins=20, color='steelblue', edgecolor='black', alpha=0.7)
    ax3.axvline(x=30, color='red', linestyle='--', label='$30 threshold')
    ax3.set_xlabel("Transaction Amount ($)")
    ax3.set_ylabel("Frequency")
    ax3.set_title("Transaction Amount Distribution")
    ax3.legend()
    
    # Transaction count
    ax4 = axes[1, 1]
    label_counts = gas_df.groupby("label").size()
    bars = ax4.bar(label_counts.index, label_counts.values, color=colors)
    ax4.set_ylabel("Number of Transactions")
    ax4.set_title("Transaction Count")
    for bar, val in zip(bars, label_counts.values):
        ax4.text(bar.get_x() + bar.get_width()/2, val + 1, str(val), 
                ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    output_path = output_dir / "Gas_Station_Analysis.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Saved: {output_path}")


def create_walmart_analysis(df: pd.DataFrame, output_dir: Path):
    """Create Walmart spending analysis."""
    walmart_df = df[df["label"] == "Walmart"]
    
    if walmart_df.empty:
        print("No Walmart data to plot")
        return
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f"Walmart Spending Analysis\nTotal: ${walmart_df['amount'].sum():.2f} ({len(walmart_df)} transactions)", 
                 fontsize=16, fontweight='bold')
    
    # Monthly Walmart spending
    ax1 = axes[0, 0]
    monthly = walmart_df.groupby(walmart_df["date"].dt.to_period("M"))["amount"].sum()
    bars = ax1.bar([str(m) for m in monthly.index], monthly.values, color='#0071ce', alpha=0.8)
    ax1.set_xlabel("Month")
    ax1.set_ylabel("Amount ($)")
    ax1.set_title("Monthly Walmart Spending")
    plt.sca(ax1)
    plt.xticks(rotation=45, ha='right')
    for bar, val in zip(bars, monthly.values):
        ax1.text(bar.get_x() + bar.get_width()/2, val + 2, f'${val:.0f}', 
                ha='center', va='bottom', fontsize=8)
    
    # Transaction size distribution
    ax2 = axes[0, 1]
    ax2.hist(walmart_df["amount"], bins=15, color='#0071ce', edgecolor='black', alpha=0.7)
    ax2.axvline(x=walmart_df["amount"].mean(), color='red', linestyle='--', 
                label=f'Average: ${walmart_df["amount"].mean():.2f}')
    ax2.set_xlabel("Transaction Amount ($)")
    ax2.set_ylabel("Frequency")
    ax2.set_title("Transaction Size Distribution")
    ax2.legend()
    
    # By card
    ax3 = axes[1, 0]
    card_totals = walmart_df.groupby("card")["amount"].sum().sort_values(ascending=True)
    bars = ax3.barh(card_totals.index, card_totals.values, color='#0071ce', alpha=0.8)
    ax3.set_xlabel("Amount ($)")
    ax3.set_title("Walmart Spending by Card")
    for bar, val in zip(bars, card_totals.values):
        ax3.text(val + 2, bar.get_y() + bar.get_height()/2, f'${val:.2f}', 
                va='center', fontsize=9)
    
    # Weekly pattern
    ax4 = axes[1, 1]
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekly = walmart_df.groupby("day_of_week")["amount"].sum().reindex(day_order)
    ax4.bar(weekly.index, weekly.values, color='#0071ce', alpha=0.8)
    ax4.set_xlabel("Day of Week")
    ax4.set_ylabel("Amount ($)")
    ax4.set_title("Walmart Spending by Day of Week")
    plt.sca(ax4)
    plt.xticks(rotation=45, ha='right')
    
    plt.tight_layout()
    output_path = output_dir / "Walmart_Analysis.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Saved: {output_path}")


def create_daily_pattern_chart(df: pd.DataFrame, output_dir: Path):
    """Create daily/weekly spending patterns."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("Spending Patterns", fontsize=16, fontweight='bold')
    
    # By day of week
    ax1 = axes[0]
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    daily = df.groupby("day_of_week")["amount"].sum().reindex(day_order)
    colors = ['#3498db'] * 5 + ['#e74c3c'] * 2  # Weekdays blue, weekends red
    bars = ax1.bar(daily.index, daily.values, color=colors, alpha=0.8)
    ax1.set_xlabel("Day of Week")
    ax1.set_ylabel("Total Spending ($)")
    ax1.set_title("Spending by Day of Week")
    plt.sca(ax1)
    plt.xticks(rotation=45, ha='right')
    
    for bar, val in zip(bars, daily.values):
        ax1.text(bar.get_x() + bar.get_width()/2, val + 10, f'${val:.0f}', 
                ha='center', va='bottom', fontsize=9)
    
    # Average transaction by day
    ax2 = axes[1]
    avg_daily = df.groupby("day_of_week")["amount"].mean().reindex(day_order)
    bars = ax2.bar(avg_daily.index, avg_daily.values, color=colors, alpha=0.8)
    ax2.set_xlabel("Day of Week")
    ax2.set_ylabel("Average Transaction ($)")
    ax2.set_title("Average Transaction by Day")
    plt.sca(ax2)
    plt.xticks(rotation=45, ha='right')
    
    for bar, val in zip(bars, avg_daily.values):
        ax2.text(bar.get_x() + bar.get_width()/2, val + 0.5, f'${val:.2f}', 
                ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    output_path = output_dir / "Daily_Patterns.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Saved: {output_path}")


def create_top_merchants_chart(df: pd.DataFrame, output_dir: Path):
    """Create top merchants/labels chart."""
    label_totals = df.groupby("label")["amount"].sum().sort_values(ascending=False).head(15)
    label_counts = df.groupby("label").size().loc[label_totals.index]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    fig.suptitle("Top 15 Spending Categories", fontsize=16, fontweight='bold')
    
    # By total amount
    colors = plt.cm.viridis(np.linspace(0, 0.8, len(label_totals)))
    bars1 = ax1.barh(label_totals.index[::-1], label_totals.values[::-1], color=colors[::-1])
    ax1.set_xlabel("Total Amount ($)")
    ax1.set_title("By Total Spending")
    
    for bar, val in zip(bars1, label_totals.values[::-1]):
        ax1.text(val + 5, bar.get_y() + bar.get_height()/2, f'${val:.2f}', 
                va='center', fontsize=9)
    
    # By transaction count
    bars2 = ax2.barh(label_counts.index[::-1], label_counts.values[::-1], color=colors[::-1])
    ax2.set_xlabel("Number of Transactions")
    ax2.set_title("By Transaction Count")
    
    for bar, val in zip(bars2, label_counts.values[::-1]):
        ax2.text(val + 0.5, bar.get_y() + bar.get_height()/2, str(val), 
                va='center', fontsize=9)
    
    plt.tight_layout()
    output_path = output_dir / "Top_Categories.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Saved: {output_path}")


def create_vending_machine_analysis(df: pd.DataFrame, output_dir: Path):
    """Create vending machine spending analysis."""
    vending_df = df[df["label"] == "Vending Machine"]
    
    if vending_df.empty:
        print("No vending machine data to plot")
        return
    
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle(f"Vending Machine Analysis\nTotal: ${vending_df['amount'].sum():.2f} ({len(vending_df)} transactions)", 
                 fontsize=16, fontweight='bold')
    
    # Monthly trend
    ax1 = axes[0]
    monthly = vending_df.groupby(vending_df["date"].dt.to_period("M"))["amount"].sum()
    ax1.bar([str(m) for m in monthly.index], monthly.values, color='#9b59b6', alpha=0.8)
    ax1.set_xlabel("Month")
    ax1.set_ylabel("Amount ($)")
    ax1.set_title("Monthly Spending")
    plt.sca(ax1)
    plt.xticks(rotation=45, ha='right')
    
    # Transaction distribution
    ax2 = axes[1]
    ax2.hist(vending_df["amount"], bins=10, color='#9b59b6', edgecolor='black', alpha=0.7)
    ax2.set_xlabel("Amount ($)")
    ax2.set_ylabel("Frequency")
    ax2.set_title("Transaction Amounts")
    
    # By day of week
    ax3 = axes[2]
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    daily = vending_df.groupby("day_of_week").size().reindex(day_order, fill_value=0)
    ax3.bar(daily.index, daily.values, color='#9b59b6', alpha=0.8)
    ax3.set_xlabel("Day of Week")
    ax3.set_ylabel("Transaction Count")
    ax3.set_title("Usage by Day")
    plt.sca(ax3)
    plt.xticks(rotation=45, ha='right')
    
    plt.tight_layout()
    output_path = output_dir / "Vending_Machine_Analysis.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Saved: {output_path}")


def create_other_categories_breakdown(df: pd.DataFrame, output_dir: Path):
    """Create detailed breakdown of 'Other Categories' (everything beyond top 10)."""
    category_totals = df.groupby("label")["amount"].sum().sort_values(ascending=False)
    category_counts = df.groupby("label").size()
    
    # Get categories beyond top 10
    top_10_labels = category_totals.head(10).index.tolist()
    other_df = df[~df["label"].isin(top_10_labels)]
    other_totals = other_df.groupby("label")["amount"].sum().sort_values(ascending=False)
    other_counts = other_df.groupby("label").size()
    
    if other_totals.empty:
        print("No 'Other Categories' to plot")
        return
    
    total_other = other_totals.sum()
    
    fig = plt.figure(figsize=(18, 14))
    fig.suptitle(f"Detailed Breakdown: Other Categories\nTotal: ${total_other:,.2f} across {len(other_totals)} categories", 
                 fontsize=16, fontweight='bold')
    
    # Split into two groups for better visibility
    mid_point = len(other_totals) // 2
    first_half = other_totals.iloc[:mid_point]
    second_half = other_totals.iloc[mid_point:]
    
    # First half - horizontal bar chart
    ax1 = fig.add_subplot(2, 2, 1)
    colors1 = plt.cm.viridis(np.linspace(0.2, 0.8, len(first_half)))
    first_half_sorted = first_half.sort_values(ascending=True)
    bars1 = ax1.barh(first_half_sorted.index, first_half_sorted.values, color=colors1)
    ax1.set_xlabel("Amount ($)")
    ax1.set_title(f"Categories (Part 1 of 2)")
    for bar, val in zip(bars1, first_half_sorted.values):
        ax1.text(val + 1, bar.get_y() + bar.get_height()/2, f'${val:.2f}', 
                va='center', fontsize=8)
    
    # Second half - horizontal bar chart
    ax2 = fig.add_subplot(2, 2, 2)
    colors2 = plt.cm.plasma(np.linspace(0.2, 0.8, len(second_half)))
    second_half_sorted = second_half.sort_values(ascending=True)
    bars2 = ax2.barh(second_half_sorted.index, second_half_sorted.values, color=colors2)
    ax2.set_xlabel("Amount ($)")
    ax2.set_title(f"Categories (Part 2 of 2)")
    for bar, val in zip(bars2, second_half_sorted.values):
        ax2.text(val + 1, bar.get_y() + bar.get_height()/2, f'${val:.2f}', 
                va='center', fontsize=8)
    
    # Grouped by category type - pie chart
    ax3 = fig.add_subplot(2, 2, 3)
    
    # Group into broader categories
    category_groups = {
        "Food & Dining": ["Wendy's", "McDonald's", "Taco Bell", "Burger King", "Chick-fil-A", 
                         "Pizza", "Domino's", "Starbucks", "High Ground Coffee", "Dunkin",
                         "Cook Out", "Waffle House", "Chili's", "Buffalo Wild Wings", 
                         "Panda Express", "Raising Cane's", "Thai Restaurant", "TopGolf",
                         "Boardtown Pies", "Dave's Dark Horse", "Dining", "Restaurants",
                         "DoorDash", "Grubhub", "Uber Eats", "NYC Halal Food", "Pita Pit",
                         "Food Vendor", "Taxi Shop Café", "Deli/Grocery (NYC)"],
        "Groceries": ["Grocery (Kroger)", "Grocery (Aldi)", "Grocery (Patel Brothers)"],
        "Subscriptions": ["Netflix", "Disney+", "YouTube Premium", "Google One", "Hinge",
                         "Apple", "Amazon Prime", "Microsoft", "LinkedIn Premium"],
        "Shopping": ["Target", "Dollar General", "Five Below", "NYC Gift Shop", 
                    "Nassau Street Store", "MSU MAFES Store", "WHSmith (Airport)",
                    "Boots (UK Pharmacy)", "Electronics (Micro Center)", "Amazon Shopping"],
        "Clothes": ["Clothes (Marshalls)", "Clothes (Century 21)", "Clothes (H&M)", "Clothes (Nike)"],
        "Services": ["Phone Service", "Renters Insurance", "Health Insurance", "Shipping (UPS)",
                    "Haircut", "Printing", "Medical Payment", "Car Wash", "Parking",
                    "MSU Health Center", "MSU Campus", "DMV/DPS", "Visa Services (Atlys)",
                    "Online Service", "Bicycle Repair", "Resume Services", "Textbooks (Pearson)"],
        "Transportation": ["Uber Taxi", "Lyft", "NYC Transit", "Bird Scooter", "Ferry"],
        "Travel": ["Flight (Virgin Atlantic)", "Hotel (Super 8)", "Chase Travel"],
        "Entertainment": ["Movie Theater", "TopGolf", "Entertainment"],
        "API & Tech": ["API Costs (Google Cloud)", "API Costs (Google Colab)", 
                      "API Costs (AWS)", "API Costs (ElevenLabs)", "Google Services"],
        "Books": ["Books (Kindle)", "Books"],
    }
    
    group_totals = {}
    for group_name, labels in category_groups.items():
        group_sum = other_totals[other_totals.index.isin(labels)].sum()
        if group_sum > 0:
            group_totals[group_name] = group_sum
    
    # Add any ungrouped categories
    grouped_labels = [label for labels in category_groups.values() for label in labels]
    ungrouped = other_totals[~other_totals.index.isin(grouped_labels)].sum()
    if ungrouped > 0:
        group_totals["Other"] = ungrouped
    
    group_series = pd.Series(group_totals).sort_values(ascending=False)
    colors3 = plt.cm.Set3(np.linspace(0, 1, len(group_series)))
    wedges, texts, autotexts = ax3.pie(
        group_series.values,
        labels=None,
        autopct=lambda pct: f'{pct:.1f}%' if pct > 3 else '',
        colors=colors3,
        startangle=90
    )
    ax3.set_title("Grouped by Type")
    ax3.legend(
        wedges,
        [f"{label}: ${amount:.2f}" for label, amount in group_series.items()],
        loc="center left",
        bbox_to_anchor=(1, 0.5),
        fontsize=8
    )
    
    # Transaction count vs amount scatter
    ax4 = fig.add_subplot(2, 2, 4)
    other_data = pd.DataFrame({
        'amount': other_totals,
        'count': other_counts[other_totals.index]
    })
    scatter = ax4.scatter(other_data['count'], other_data['amount'], 
                         c=range(len(other_data)), cmap='viridis', 
                         s=100, alpha=0.7, edgecolors='black')
    ax4.set_xlabel("Number of Transactions")
    ax4.set_ylabel("Total Amount ($)")
    ax4.set_title("Transaction Count vs Total Spending")
    
    # Label top spenders
    top_5_other = other_totals.head(5)
    for label in top_5_other.index:
        x = other_data.loc[label, 'count']
        y = other_data.loc[label, 'amount']
        ax4.annotate(label, (x, y), textcoords="offset points", xytext=(5, 5), fontsize=7)
    
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    output_path = output_dir / "Other_Categories_Breakdown.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Saved: {output_path}")


def create_summary_dashboard(df: pd.DataFrame, output_dir: Path):
    """Create a summary dashboard with key metrics."""
    fig = plt.figure(figsize=(16, 12))
    fig.suptitle("2025 Expense Summary Dashboard", fontsize=20, fontweight='bold', y=0.98)
    
    # Key metrics text
    total_spent = df["amount"].sum()
    avg_transaction = df["amount"].mean()
    total_transactions = len(df)
    date_range = f"{df['date'].min().strftime('%b %d')} - {df['date'].max().strftime('%b %d, %Y')}"
    
    # Add metrics box
    metrics_text = f"""
    Total Spent: ${total_spent:,.2f}
    Total Transactions: {total_transactions}
    Average Transaction: ${avg_transaction:.2f}
    Period: {date_range}
    """
    fig.text(0.5, 0.92, metrics_text, ha='center', fontsize=12, 
             bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
    
    # Top 5 categories pie
    ax1 = fig.add_subplot(2, 3, 1)
    top_5 = df.groupby("label")["amount"].sum().sort_values(ascending=False).head(5)
    colors = plt.cm.Set2(range(len(top_5)))
    ax1.pie(top_5.values, labels=top_5.index, autopct='%1.1f%%', colors=colors)
    ax1.set_title("Top 5 Categories")
    
    # Monthly trend
    ax2 = fig.add_subplot(2, 3, 2)
    monthly = df.groupby(df["date"].dt.to_period("M"))["amount"].sum()
    ax2.plot([str(m) for m in monthly.index], monthly.values, 'b-o', linewidth=2, markersize=8)
    ax2.fill_between(range(len(monthly)), monthly.values, alpha=0.3)
    ax2.set_title("Monthly Trend")
    ax2.set_ylabel("Amount ($)")
    plt.sca(ax2)
    plt.xticks(rotation=45, ha='right')
    
    # Card distribution
    ax3 = fig.add_subplot(2, 3, 3)
    card_totals = df.groupby("card")["amount"].sum()
    ax3.pie(card_totals.values, labels=card_totals.index, autopct='%1.1f%%')
    ax3.set_title("Spending by Card")
    
    # Top 10 categories bar
    ax4 = fig.add_subplot(2, 1, 2)
    top_10 = df.groupby("label")["amount"].sum().sort_values(ascending=True).tail(10)
    colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(top_10)))
    bars = ax4.barh(top_10.index, top_10.values, color=colors)
    ax4.set_xlabel("Amount ($)")
    ax4.set_title("Top 10 Spending Categories")
    for bar, val in zip(bars, top_10.values):
        ax4.text(val + 10, bar.get_y() + bar.get_height()/2, f'${val:.0f}', 
                va='center', fontsize=9)
    
    plt.tight_layout(rect=[0, 0, 1, 0.88])
    output_path = output_dir / "Summary_Dashboard.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Saved: {output_path}")


def main():
    """Main function to generate all overall diagrams."""
    base_dir = Path(__file__).parent.parent
    csv_dir = base_dir / "csv"
    output_dir = base_dir / "overall_diagrams"
    output_dir.mkdir(exist_ok=True)
    
    # Load merged transactions
    merged_csv = csv_dir / "All_Transactions_Merged.csv"
    
    if not merged_csv.exists():
        print(f"Error: {merged_csv} not found. Run merge_transactions.py first.")
        return
    
    print("=" * 60)
    print("Generating Overall Expense Diagrams")
    print("=" * 60)
    
    df = load_transactions(str(merged_csv))
    print(f"Loaded {len(df)} total transactions")
    print(f"Date range: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}")
    print(f"Total spending: ${df['amount'].sum():,.2f}\n")
    
    # Generate all diagrams
    print("Generating diagrams...")
    create_summary_dashboard(df, output_dir)
    create_monthly_spending_chart(df, output_dir)
    create_category_breakdown(df, output_dir)
    create_other_categories_breakdown(df, output_dir)
    create_card_spending_chart(df, output_dir)
    create_top_merchants_chart(df, output_dir)
    create_daily_pattern_chart(df, output_dir)
    create_restaurant_breakdown(df, output_dir)
    create_gas_station_analysis(df, output_dir)
    create_walmart_analysis(df, output_dir)
    create_vending_machine_analysis(df, output_dir)
    create_other_categories_breakdown(df, output_dir)
    
    print(f"\n{'=' * 60}")
    print(f"All diagrams saved to: {output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
