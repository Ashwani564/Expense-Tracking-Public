# Technical Architecture Documentation

## Overview

This document provides comprehensive technical documentation for the Personal Expense Tracking System—a modular data pipeline for processing multi-bank credit card statements and generating actionable financial insights.

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Component Specifications](#component-specifications)
3. [Data Flow Pipeline](#data-flow-pipeline)
4. [Labeling Engine](#labeling-engine)
5. [API Reference](#api-reference)
6. [Extension Guide](#extension-guide)
7. [Performance & Error Handling](#performance--error-handling)

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         EXPENSE TRACKING SYSTEM                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
│  │  Chase PDFs  │    │CapitalOne CSV│    │ Discover CSV │              │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘              │
│         │                   │                   │                       │
│         ▼                   │                   │                       │
│  ┌──────────────┐           │                   │                       │
│  │   Gemini AI  │           │                   │                       │
│  │  Extraction  │           │                   │                       │
│  └──────┬───────┘           │                   │                       │
│         │                   │                   │                       │
│         └───────────────────┼───────────────────┘                       │
│                             ▼                                           │
│                  ┌─────────────────────┐                                │
│                  │  Merge & Transform  │                                │
│                  │   (90+ Labels)      │                                │
│                  └──────────┬──────────┘                                │
│                             │                                           │
│         ┌───────────────────┼───────────────────┐                       │
│         ▼                   ▼                   ▼                       │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                 │
│  │Trip Diagrams│    │  Overall    │    │   Gemini    │                 │
│  │             │    │  Analytics  │    │   Advisor   │                 │
│  └─────────────┘    └─────────────┘    └─────────────┘                 │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Component Specifications

### 1. Data Extraction Layer

**Module**: `src/extract_chase_transactions.py`

| Attribute | Value |
|-----------|-------|
| Purpose | Extract structured data from Chase PDF statements |
| AI Model | Google Gemini 2.0 Flash |
| Context Window | 65,000 tokens |
| Output Format | CSV with normalized schema |

**Processing Pipeline**:
1. Upload PDF to Gemini File API
2. Submit extraction prompt with JSON schema definition
3. Parse and validate JSON response
4. Handle multi-page statements with transaction continuity
5. Export normalized CSV

**Output Schema**:
```csv
date,description,amount,category,card,source
2025-01-15,AMAZON.COM,29.99,Shopping,Chase-7557,statement.pdf
```

---

### 2. Data Transformation Layer

**Module**: `src/merge_transactions.py`

**Supported Data Sources**:

| Bank | Input Format | Loader Function | Key Fields |
|------|--------------|-----------------|------------|
| Chase | Extracted CSV | `load_chase()` | date, description, amount |
| Capital One | Bank CSV | `load_capital_one()` | Transaction Date, Description, Debit |
| Discover | Bank CSV | `load_discover()` | Trans. Date, Description, Amount |

**Normalization Rules**:
- Date formats: `YYYY-MM-DD`, `MM/DD/YYYY`, `MM/DD/YY` → `YYYY-MM-DD`
- Amounts: String to float, handle currency symbols
- Encoding: Auto-detect (UTF-8, Latin-1, CP1252, ISO-8859-1)

---

### 3. Visualization Layer

#### Trip Analysis (`src/generate_trip_diagrams.py`)

**Capabilities**:
- Date-range filtering for travel periods
- Automatic exclusion of pre-ordered items (Walmart >$30)
- Per-trip expense breakdown
- Multi-trip comparison charts

**Configuration Schema**:
```python
TRIPS = [
    {
        "name": "NYC_Trip",           # Filename prefix
        "description": "NYC Trip",    # Chart title
        "start_date": "2025-06-15",
        "end_date": "2025-06-20"
    }
]
```

#### Overall Analytics (`src/generate_overall_diagrams.py`)

**Generated Visualizations**:

| Output File | Chart Type | Description |
|-------------|------------|-------------|
| `Summary_Dashboard.png` | Multi-panel | Key metrics overview |
| `Monthly_Spending_Trends.png` | Bar + Line | Month-over-month with average |
| `Category_Breakdown.png` | Pie + Bar | Top 10 categories |
| `Other_Categories_Breakdown.png` | Multi-panel | Detailed breakdown beyond top 10 |
| `Card_Spending.png` | Dual Bar | Amount and count by card |
| `Top_Categories.png` | Horizontal Bar | Ranked spending categories |
| `Daily_Patterns.png` | Bar | Spending by day of week |
| `Restaurant_Breakdown.png` | Bar + Pie | Food spending analysis |
| `Gas_Station_Analysis.png` | Multi-panel | Fuel vs. convenience purchases |
| `Walmart_Analysis.png` | Multi-panel | Walmart spending patterns |
| `Vending_Machine_Analysis.png` | Multi-panel | Campus vending habits |

---

### 4. AI Advisory Layer

**Module**: `src/gemini_advisor.py`

| Attribute | Value |
|-----------|-------|
| Model | Gemini 2.0 Flash |
| Input | Transaction summary + chart images |
| Output | Personalized financial advice (Markdown) |

**Analysis Components**:
1. **Reality Check**: Current vs. available budget comparison
2. **Survival Budget**: Allocation plan for essential expenses
3. **Elimination Targets**: Specific expenses to cut
4. **Optimization Tips**: Areas for cost reduction
5. **30-Day Challenge**: Actionable savings plan

---

## Data Flow Pipeline

```
INPUT                    PROCESS                      OUTPUT
─────────────────────────────────────────────────────────────────
Chase PDFs          →    Gemini Extraction      →    Chase CSV
CapitalOne CSV      →    Load & Normalize       →    ┐
Discover CSV        →    Load & Normalize       →    ├→ Merged CSV
Chase CSV           →    Load & Normalize       →    ┘
                                                         │
Merged CSV          →    Apply Labels (90+)     →    Labeled CSV
                                                         │
                    ┌────────────────────────────────────┤
                    ↓                ↓                   ↓
             Trip Diagrams    Overall Charts      AI Advisor
                    ↓                ↓                   ↓
             trip_diagrams/   overall_diagrams/   financial_advice.md
```

---

## Labeling Engine

### Processing Order (Priority High → Low)

```
1. Vending Machine     (AMK, CTLP, Coca-Cola patterns)
2. Utilities           (SimpleBills → Electricity)
3. Gas Stations        (<$30 → Indiscretion, ≥$30 → Gasoline)
4. Walmart             (All Walmart variants)
5. Streaming/Subs      (Netflix, Disney+, etc.)
6. Professional        (LinkedIn, Resume services)
7. API/Cloud           (Google Cloud, AWS, ElevenLabs)
8. Transportation      (Uber, Lyft, Transit)
9. Clothing            (Marshalls, Nike, H&M)
10. Groceries          (Kroger, Aldi, etc.)
11. Shopping           (Target, Dollar General, etc.)
12. Services           (Phone, Insurance, etc.)
13. Travel             (Flights, Hotels)
14. Entertainment      (Movies, TopGolf)
15. Amazon             (Prime vs Shopping distinction)
16. Restaurants        (Chain-specific labels)
17. Final Pass         (Edge case cleanup)
```

### Label Categories (90+ Total)

| Category Group | Labels |
|----------------|--------|
| **Food Delivery** | DoorDash, Grubhub, Uber Eats |
| **Fast Food** | Wendy's, McDonald's, Taco Bell, Burger King, Chick-fil-A, Raising Cane's |
| **Casual Dining** | Chili's, Buffalo Wild Wings, Waffle House, Panda Express |
| **Coffee** | Starbucks, Dunkin, High Ground Coffee |
| **Groceries** | Grocery (Kroger), Grocery (Aldi), Grocery (Patel Brothers) |
| **Vending** | Vending Machine |
| **Gas Stations** | Gas Station Indiscretion, Gasoline |
| **Streaming** | Netflix, Disney+, YouTube Premium, Hinge |
| **E-Commerce** | Amazon Shopping, Amazon Prime |
| **API/Cloud** | API Costs (Google Cloud), API Costs (AWS), API Costs (ElevenLabs), API Costs (Google Colab) |
| **Transportation** | Uber Taxi, Lyft, NYC Transit, Bird Scooter, Ferry |
| **Clothing** | Clothes (Marshalls), Clothes (Nike), Clothes (H&M), Clothes (Century 21) |
| **Books** | Books (Kindle), Books |
| **Professional** | LinkedIn Premium, Resume Services |
| **Insurance** | Renters Insurance, Health Insurance |
| **Utilities** | Electricity, Phone Service |
| **Travel** | Flight (Virgin Atlantic), Hotel (Super 8), Chase Travel |
| **Shopping** | Walmart, Target, Dollar General, Five Below |

---

## API Reference

### extract_chase_transactions.py

```python
def extract_transactions_from_pdf(pdf_path: str) -> List[Dict]
    """
    Extract transactions from a Chase PDF statement.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        List of transaction dictionaries with keys:
        - date: Transaction date (YYYY-MM-DD)
        - description: Merchant description
        - amount: Transaction amount (float)
        - category: Original category from statement
    """
```

### merge_transactions.py

```python
def apply_labels(df: pd.DataFrame) -> pd.DataFrame
    """
    Apply labeling rules to transactions.
    
    Args:
        df: DataFrame with columns [date, description, amount, category, card, source]
        
    Returns:
        DataFrame with additional 'label' column
    """

def merge_all_csvs(csv_dir: str) -> pd.DataFrame
    """
    Load and merge all CSV files from supported banks.
    
    Args:
        csv_dir: Directory containing CSV files
        
    Returns:
        Merged and labeled DataFrame
    """
```

### gemini_advisor.py

```python
def get_financial_advice(income: float = 900, rent: float = 450) -> str
    """
    Generate personalized financial advice.
    
    Args:
        income: Monthly income
        rent: Monthly rent (fixed expense)
        
    Returns:
        Markdown-formatted financial advice
    """
```

---

## Extension Guide

### Adding a New Bank

1. **Create Loader Function**:
```python
def load_new_bank(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path)
    return pd.DataFrame({
        "date": df["Date Column"].apply(normalize_date),
        "description": df["Description Column"],
        "amount": df["Amount Column"],
        "category": df.get("Category Column", "Uncategorized"),
        "card": "NewBank",
        "source": Path(file_path).name
    })
```

2. **Register in `merge_all_csvs()`**:
```python
new_bank_files = list(csv_path.glob("NewBank*.csv"))
for f in new_bank_files:
    df = load_new_bank(str(f))
    all_dfs.append(df)
```

### Adding New Labels

```python
# In apply_labels() function
new_labels = [
    (["PATTERN1", "PATTERN2"], "New Label"),
]
for patterns, label in new_labels:
    for pattern in patterns:
        mask = df["description"].str.upper().str.contains(
            pattern.upper(), na=False
        )
        df.loc[mask, "label"] = label
```

### Adding New Visualizations

```python
def create_new_chart(df: pd.DataFrame, output_dir: Path):
    """Create a new visualization."""
    fig, ax = plt.subplots(figsize=(12, 8))
    # ... visualization logic ...
    plt.savefig(output_dir / "New_Chart.png", dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: New_Chart.png")

# Register in main()
create_new_chart(df, output_dir)
```

---

## Performance & Error Handling

### Performance Characteristics

| Operation | Typical Duration | Notes |
|-----------|------------------|-------|
| PDF Extraction | 5-15s per PDF | Gemini API rate limited |
| CSV Loading | <1s per file | Depends on file size |
| Label Application | 1-2s | 734 transactions |
| Chart Generation | 2-3s per chart | 11 charts total |
| AI Advisor | 10-20s | Image analysis + generation |

### Error Handling

| Error Type | Handling Strategy |
|------------|-------------------|
| PDF Parse Failure | Retry with exponential backoff (3 attempts) |
| CSV Encoding | Auto-detect: UTF-8 → Latin-1 → CP1252 → ISO-8859-1 |
| Missing API Key | Clear error message with setup instructions |
| Empty Data | Graceful skip with warning log |
| Invalid Dates | Passthrough with original value |

### Resource Limits

- Gemini API: 65,000 token context window
- Recommended: Process PDFs sequentially to avoid rate limits
- Large datasets (>100k rows): Consider chunked processing

---

## Future Development Roadmap

### Phase 2 Features

- [ ] Web interface for PDF upload
- [ ] Real-time expense tracking
- [ ] Budget alerts and notifications
- [ ] Multi-user support with authentication
- [ ] Bank API integration (Plaid)
- [ ] Mobile companion app
- [ ] Export to accounting software (QuickBooks, YNAB)

---

*Last Updated: December 2025*
