# 💳 Personal Expense Tracker

A comprehensive expense tracking system that extracts transactions from credit card PDF statements, merges data from multiple banks, applies intelligent categorization, and generates visual spending analytics with AI-powered financial advice.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Gemini](https://img.shields.io/badge/Google-Gemini%202.0-orange.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## ✨ Features

- **📄 PDF Extraction**: Extract transactions from Chase credit card statements using Google Gemini AI
- **🏦 Multi-Bank Support**: Merge transactions from Chase, Capital One, and Discover
- **🏷️ Smart Labeling**: 90+ automatic merchant categories (restaurants, subscriptions, gas stations, etc.)
- **📊 Visual Analytics**: Generate comprehensive spending charts and dashboards
- **✈️ Trip Reports**: Create expense breakdowns for specific date ranges
- **🤖 AI Financial Advisor**: Get personalized budget advice from Gemini AI

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

### Installation

```bash
# Clone the repository
git clone https://github.com/Ashwani564/Expense-Tracking-Public.git
cd Expense-Tracking-Public

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your GEMINI_API key
```

### Project Structure

```
├── src/
│   ├── extract_chase_transactions.py  # PDF extraction with Gemini
│   ├── merge_transactions.py          # Multi-bank merging & labeling
│   ├── generate_trip_diagrams.py      # Trip-specific visualizations
│   ├── generate_overall_diagrams.py   # Overall spending analytics
│   ├── gemini_advisor.py              # AI financial advisor
│   └── run_phase1.py                  # Run all scripts
├── PDF/                               # Place Chase PDFs here
├── csv/                               # Place bank CSVs here
├── overall_diagrams/                  # Generated overall charts
├── trip_diagrams/                     # Generated trip charts
├── requirements.txt
├── .env.example
└── AGENTS.md                          # Technical documentation
```

## 📖 Usage Guide

### Step 1: Prepare Your Data

**Chase Statements (PDF)**
```
PDF/
├── 7557/           # Last 4 digits of card
│   ├── statement1.pdf
│   └── statement2.pdf
└── 2040/
    └── statement.pdf
```

**Capital One & Discover (CSV)**
- Download transaction CSVs from your bank's website
- Place them in the `csv/` folder with names starting with `CapitalOne` or `Discover`

### Step 2: Extract Chase Transactions

```bash
python src/extract_chase_transactions.py
```

This uses Gemini AI to parse your Chase PDF statements and outputs `csv/Chase_Extracted_Transactions.csv`.

### Step 3: Merge All Transactions

```bash
python src/merge_transactions.py
```

This combines all bank data and applies smart labeling rules. Output: `csv/All_Transactions_Merged.csv`

### Step 4: Generate Visualizations

**Overall Spending Analytics:**
```bash
python src/generate_overall_diagrams.py
```

**Trip-Specific Reports:**
```bash
python src/generate_trip_diagrams.py
```

### Step 5: Get AI Financial Advice

```bash
python src/gemini_advisor.py --income 900 --rent 450
```

### Run Everything at Once

```bash
python src/run_phase1.py
```

## 🏷️ Labeling System

The system automatically categorizes transactions into 90+ labels:

| Category | Examples |
|----------|----------|
| **Food Delivery** | DoorDash, Grubhub, Uber Eats |
| **Fast Food** | Wendy's, McDonald's, Taco Bell, Chick-fil-A |
| **Groceries** | Kroger, Aldi, Walmart, Patel Brothers |
| **Gas Stations** | Shell, Chevron, Buc-ee's (with snack detection!) |
| **Subscriptions** | Netflix, Disney+, YouTube Premium, Amazon Prime |
| **API/Cloud** | Google Cloud, AWS, ElevenLabs |
| **Transportation** | Uber Taxi, Lyft, NYC Transit |
| **Clothing** | Marshalls, Nike, H&M, Century 21 |

### Special Logic

- **Gas Station Indiscretion**: Purchases <$30 at gas stations (snacks/drinks)
- **Gasoline**: Purchases ≥$30 at gas stations (actual fuel)
- **Vending Machine**: Catches all campus vending (AMK, CTLP, Coca-Cola)
- **Trip Filtering**: Excludes Walmart orders >$30 from trip reports (pre-orders)

## 📊 Generated Charts

| Chart | Description |
|-------|-------------|
| `Summary_Dashboard.png` | Key metrics overview |
| `Monthly_Spending_Trends.png` | Month-over-month analysis |
| `Category_Breakdown.png` | Top spending categories |
| `Restaurant_Breakdown.png` | Food spending deep-dive |
| `Gas_Station_Analysis.png` | Fuel vs snacks |
| `Vending_Machine_Analysis.png` | Campus vending habits |
| `Walmart_Analysis.png` | Walmart spending patterns |

## 🤖 AI Financial Advisor

The Gemini-powered advisor analyzes your spending charts and provides:

- Reality check on overspending
- Survival budget plan
- Expenses to eliminate/reduce
- Weekly spending allowance
- 30-day savings challenge

```bash
python src/gemini_advisor.py --income YOUR_INCOME --rent YOUR_RENT
```

## 🔧 Customization

### Adding New Labels

Edit `src/merge_transactions.py`:

```python
new_labels = [
    (["MERCHANT_PATTERN"], "Label Name"),
]
for patterns, label in new_labels:
    for pattern in patterns:
        mask = df["description"].str.upper().str.contains(pattern.upper(), na=False)
        df.loc[mask, "label"] = label
```

### Adding New Trips

Edit `src/generate_trip_diagrams.py`:

```python
TRIPS = [
    {
        "name": "Trip_Name",
        "description": "Display Name",
        "start_date": "2025-01-01",
        "end_date": "2025-01-05"
    },
]
```

### Adding New Banks

See `AGENTS.md` for detailed instructions on adding support for additional banks.

## 📋 Requirements

```
pandas>=2.0.0
matplotlib>=3.7.0
seaborn>=0.12.0
google-genai>=1.0.0
python-dotenv>=1.0.0
```

## 🔒 Privacy

- Your `.env` file (containing API keys) is gitignored
- Personal financial data folders (`PDF/`, `csv/`, `*_diagrams/`) are gitignored
- Never commit sensitive financial data to public repositories

## 📄 License

MIT License - feel free to use and modify for your personal finance tracking needs.

## 🙏 Acknowledgments

- [Google Gemini](https://deepmind.google/technologies/gemini/) for AI-powered PDF extraction and financial advice
- [Matplotlib](https://matplotlib.org/) & [Seaborn](https://seaborn.pydata.org/) for visualizations

---

**Note**: This tool is for personal use. Always verify extracted data against your actual statements.
