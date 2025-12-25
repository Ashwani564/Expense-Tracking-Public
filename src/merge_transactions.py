"""
Merge all CSV files (CapitalOne, Discover, Chase) into one unified CSV.
Apply labeling rules for vending machine expenses, SimpleBills, and Shell gas station.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime


def normalize_date(date_str: str) -> str:
    """Convert various date formats to YYYY-MM-DD."""
    date_str = str(date_str).strip()
    
    # Try different formats
    formats = [
        "%Y-%m-%d",      # 2025-01-15
        "%m/%d/%Y",      # 01/15/2025
        "%m/%d/%y",      # 01/15/25
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    return date_str


def load_capital_one(file_path: str) -> pd.DataFrame:
    """Load and normalize CapitalOne CSV."""
    # Try different encodings to handle special characters
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    df = None
    for encoding in encodings:
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
    
    if df is None:
        raise ValueError(f"Could not read {file_path} with any encoding")
    
    # Filter out credits/payments (only keep debits)
    df = df[df["Debit"].notna()].copy()
    
    # Normalize columns
    normalized = pd.DataFrame({
        "date": df["Transaction Date"].apply(normalize_date),
        "description": df["Description"],
        "amount": df["Debit"],
        "category": df["Category"],
        "card": "CapitalOne",
        "source": Path(file_path).name
    })
    
    return normalized


def load_discover(file_path: str) -> pd.DataFrame:
    """Load and normalize Discover CSV."""
    # Try different encodings to handle special characters
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    df = None
    for encoding in encodings:
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
    
    if df is None:
        raise ValueError(f"Could not read {file_path} with any encoding")
    
    # Filter out payments and credits (negative amounts or specific categories)
    df = df[df["Amount"] > 0].copy()
    df = df[~df["Category"].isin(["Payments and Credits", "Awards and Rebate Credits"])].copy()
    
    # Normalize columns
    normalized = pd.DataFrame({
        "date": df["Trans. Date"].apply(normalize_date),
        "description": df["Description"],
        "amount": df["Amount"],
        "category": df["Category"],
        "card": "Discover",
        "source": Path(file_path).name
    })
    
    return normalized


def load_chase(file_path: str) -> pd.DataFrame:
    """Load and normalize Chase CSV (extracted from PDFs)."""
    # Try different encodings to handle special characters
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    df = None
    for encoding in encodings:
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
    
    if df is None:
        raise ValueError(f"Could not read {file_path} with any encoding")
    
    # Already normalized during extraction
    normalized = pd.DataFrame({
        "date": df["date"],
        "description": df["description"],
        "amount": df["amount"],
        "category": df["category"],
        "card": df["card"],
        "source": df["source"]
    })
    
    return normalized


def apply_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Apply custom labels based on merchant patterns."""
    df = df.copy()
    
    # Create a new 'label' column
    df["label"] = df["category"]  # Default to original category
    
    # Vending machine patterns (must be processed first, before restaurants)
    vending_patterns = [
        "AMK MSU POD UNION",
        "AMK MSU POD",
        "AMK POD",
        "AMK MSU EINSTEINS",
        "AMK MSU GRIFFIS",
        "AMK MSU PANDA",  # Campus vending, not Panda Express restaurant
        "CTLP*REFRESHMENTS INC",
        "CTLP*REFRESH",
        "COCA COLA CLARK STARKVIL",
        "COCA COLA CLARK STARKV",
        "COCA COLA SOUTH METRO",
        "CTLP*GREENSBORO VENDIN",
        "365 MARKET K",  # Vending/convenience at MSU
    ]
    
    for pattern in vending_patterns:
        mask = df["description"].str.upper().str.contains(pattern.upper(), na=False)
        df.loc[mask, "label"] = "Vending Machine"
    
    # SimpleBills = Electricity
    simplebills_mask = df["description"].str.upper().str.contains("SIMPLEBILLS|SIMPLE BILLS", na=False, regex=True)
    df.loc[simplebills_mask, "label"] = "Electricity"
    
    # Gas Station Indiscretion - multiple gas station brands (for small purchases like snacks/drinks)
    gas_station_patterns = [
        "SHELL",
        "LOVE'S",
        "LOVE S",
        "BUC-EE",
        "BUCEE",
        "EXXON",
        "CHEVRON",
        "MARATHON",
        "MURPHY",
        "QT ",  # QuikTrip
        "QUIKTRIP",
        "PILOT",
        "CIRCLE K",
        "SPRINT MART",
        "76 - DEES",
        "76 DEES",
        "TEXACO",
        "BP#",
        "ON THE WAY",
    ]
    
    for pattern in gas_station_patterns:
        mask = df["description"].str.upper().str.contains(pattern.upper(), na=False)
        # Only label as "Gas Station Indiscretion" if amount is under $30
        # Transactions $30+ are actual fuel fill-ups, label as "Gasoline"
        df.loc[mask & (df["amount"] < 30), "label"] = "Gas Station Indiscretion"
        df.loc[mask & (df["amount"] >= 30), "label"] = "Gasoline"
    
    # Walmart - label all Walmart transactions
    walmart_patterns = [
        "WALMART",
        "WAL-MART",
        "WM SUPERCENTER",
        "WALMART.COM",
    ]
    
    for pattern in walmart_patterns:
        mask = df["description"].str.upper().str.contains(pattern.upper(), na=False)
        df.loc[mask, "label"] = "Walmart"
    
    # ========== Books & Reading ==========
    books_patterns = [
        (["KINDLE"], "Books (Kindle)"),
        (["MCNALLY JACKSON"], "Books"),
    ]
    for patterns, label in books_patterns:
        for pattern in patterns:
            mask = df["description"].str.upper().str.contains(pattern.upper(), na=False)
            df.loc[mask, "label"] = label
    
    # ========== Streaming & Subscriptions ==========
    streaming_labels = [
        (["NETFLIX"], "Netflix"),
        (["DISNEY PLUS", "DISNEY+"], "Disney+"),
        (["YOUTUBE"], "YouTube Premium"),
        (["GOOGLE *ONE", "GOOGLE ONE"], "Google One"),
        (["HINGE"], "Hinge"),
        (["APPLE.COM"], "Apple"),
    ]
    for patterns, label in streaming_labels:
        for pattern in patterns:
            mask = df["description"].str.upper().str.contains(pattern.upper(), na=False)
            df.loc[mask, "label"] = label
    
    # ========== Professional Services ==========
    pro_services_labels = [
        (["LINKEDIN"], "LinkedIn Premium"),
        (["STP*V*RESUME", "RESUMEEXAMPLE", "RESUME-EXAMPLE"], "Resume Services"),
        (["ATLYS"], "Visa Services (Atlys)"),
        (["MSDPS"], "DMV/DPS"),
    ]
    for patterns, label in pro_services_labels:
        for pattern in patterns:
            mask = df["description"].str.upper().str.contains(pattern.upper(), na=False)
            df.loc[mask, "label"] = label
    
    # ========== API & Cloud Costs ==========
    api_labels = [
        (["GOOGLE *CLOUD", "GOOGLE CLOUD"], "API Costs (Google Cloud)"),
        (["GOOGLE COLAB", "COLAB"], "API Costs (Google Colab)"),
        (["AWS", "AMAZON WEB SERVICES"], "API Costs (AWS)"),
        (["ELEVENLABS", "ELEVEN LABS"], "API Costs (ElevenLabs)"),
    ]
    for patterns, label in api_labels:
        for pattern in patterns:
            mask = df["description"].str.upper().str.contains(pattern.upper(), na=False)
            df.loc[mask, "label"] = label
    
    # ========== Transportation ==========
    transport_labels = [
        (["UBER *TRIP"], "Uber Taxi"),
        (["PAYPAL *LYFT", "LYFT"], "Lyft"),
        (["MTA*NYCT", "OMNY"], "NYC Transit"),
        (["BIRD APP"], "Bird Scooter"),
        (["HNYFERRYIIL", "FERRY"], "Ferry"),
    ]
    for patterns, label in transport_labels:
        for pattern in patterns:
            mask = df["description"].str.upper().str.contains(pattern.upper(), na=False)
            df.loc[mask, "label"] = label
    
    # ========== Clothing & Retail ==========
    clothing_labels = [
        (["MARSHALLS"], "Clothes (Marshalls)"),
        (["CENTURY 21"], "Clothes (Century 21)"),
        (["H&M "], "Clothes (H&M)"),
        (["NIKE", "KLARNA*NIKE", "KLARNA* NIKE"], "Clothes (Nike)"),
        (["FIVE BELOW"], "Five Below"),
    ]
    for patterns, label in clothing_labels:
        for pattern in patterns:
            mask = df["description"].str.upper().str.contains(pattern.upper(), na=False)
            df.loc[mask, "label"] = label
    
    # ========== Groceries & Supermarkets ==========
    grocery_labels = [
        (["KROGER"], "Grocery (Kroger)"),
        (["ALDI"], "Grocery (Aldi)"),
        (["PATEL BROTHERS"], "Grocery (Patel Brothers)"),
        (["B & W DELI"], "Deli/Grocery (NYC)"),
    ]
    for patterns, label in grocery_labels:
        for pattern in patterns:
            mask = df["description"].str.upper().str.contains(pattern.upper(), na=False)
            df.loc[mask, "label"] = label
    
    # ========== Other Shopping ==========
    shopping_labels = [
        (["DOLLAR-GENERAL", "DOLLAR GENERAL"], "Dollar General"),
        (["TARGET"], "Target"),
        (["MICRO CENTER"], "Electronics (Micro Center)"),
        (["NYC GIFTS"], "NYC Gift Shop"),
        (["WH SMITH"], "WHSmith (Airport)"),
        (["BOOTS"], "Boots (UK Pharmacy)"),
        (["MAFES SALES"], "MSU MAFES Store"),
        (["NASSAU STREET"], "Nassau Street Store"),
    ]
    for patterns, label in shopping_labels:
        for pattern in patterns:
            mask = df["description"].str.upper().str.contains(pattern.upper(), na=False)
            df.loc[mask, "label"] = label
    
    # ========== Services ==========
    services_labels = [
        (["US MOBILE", "USMOBILE"], "Phone Service"),
        (["TOGGLE INSURANCE"], "Renters Insurance"),
        (["MOLINA HEALTH", "AMBETTER", "WELLCARE"], "Health Insurance"),
        (["UPS STORE"], "Shipping (UPS)"),
        (["SPORT CLIPS"], "Haircut"),
        (["COPY COW"], "Printing"),
        (["PEARSON"], "Textbooks (Pearson)"),
        (["MSU STUDENT HEALTH"], "MSU Health Center"),
        (["MSU CAMPUS"], "MSU Campus"),
        (["HCC MEDICAL", "HCCMEDICAL"], "Medical Payment"),
        (["MIDTOWN WASH"], "Car Wash"),
        (["GREENE ST DECK"], "Parking"),
        (["SOLIDGATE"], "Online Service"),
        (["BICYCLE REP"], "Bicycle Repair"),
    ]
    for patterns, label in services_labels:
        for pattern in patterns:
            mask = df["description"].str.upper().str.contains(pattern.upper(), na=False)
            df.loc[mask, "label"] = label
    
    # ========== Travel ==========
    travel_labels = [
        (["VIRGIN ATLANTIC"], "Flight (Virgin Atlantic)"),
        (["CHASE TRAVEL", "TRIPCHRG"], "Chase Travel"),
        (["SUPER 8"], "Hotel (Super 8)"),
    ]
    for patterns, label in travel_labels:
        for pattern in patterns:
            mask = df["description"].str.upper().str.contains(pattern.upper(), na=False)
            df.loc[mask, "label"] = label
    
    # ========== Entertainment ==========
    entertainment_labels = [
        (["UEC THEATRE"], "Movie Theater"),
        (["TOPGOLF"], "TopGolf"),
    ]
    for patterns, label in entertainment_labels:
        for pattern in patterns:
            mask = df["description"].str.upper().str.contains(pattern.upper(), na=False)
            df.loc[mask, "label"] = label
    
    # ========== Microsoft ==========
    microsoft_mask = df["description"].str.upper().str.contains("MICROSOFT", na=False)
    df.loc[microsoft_mask, "label"] = "Microsoft"
    
    # ========== Amazon - categorize by type ==========
    # Amazon Prime subscriptions (must be before generic Amazon)
    amazon_prime_mask = df["description"].str.upper().str.contains("AMAZON PRIME", na=False)
    df.loc[amazon_prime_mask, "label"] = "Amazon Prime"
    
    # Amazon Marketplace/Shopping (not Prime, not Kindle, not AWS)
    amazon_shopping_mask = (
        df["description"].str.upper().str.contains("AMAZON", na=False) & 
        ~df["description"].str.upper().str.contains("PRIME", na=False) &
        ~df["description"].str.upper().str.contains("KINDLE", na=False) &
        ~df["description"].str.upper().str.contains("WEB SERVICES", na=False)
    )
    df.loc[amazon_shopping_mask, "label"] = "Amazon Shopping"
    
    # ========== Google One-Off ==========
    # Generic Google payments (after specific Google services)
    google_generic_mask = (
        df["description"].str.upper().str.contains("PAYPAL *GOOGLE", na=False) &
        (df["label"] == df["category"])  # Only if not already labeled
    )
    df.loc[google_generic_mask, "label"] = "Google Services"
    
    # ========== Alipay ==========
    alipay_mask = df["description"].str.upper().str.contains("ALIPAY", na=False)
    df.loc[alipay_mask, "label"] = "Alipay Transfer"
    
    # ========== NYC Halal Restaurants ==========
    halal_patterns = ["HALAL", "BARHOSHA", "HOODA", "YASSO", "CAIRO"]
    for pattern in halal_patterns:
        mask = df["description"].str.upper().str.contains(pattern.upper(), na=False)
        df.loc[mask, "label"] = "NYC Halal Food"
    
    # ========== Restaurant-specific labels (order matters) ==========
    restaurant_labels = [
        # Fast food chains
        (["WENDYS", "WENDY'S", "WENDY S"], "Wendy's"),
        (["MCDONALD"], "McDonald's"),
        (["TACO BELL"], "Taco Bell"),
        (["BURGER KING"], "Burger King"),
        (["CHICK-FIL-A", "CHICKFILA", "CHICK FIL"], "Chick-fil-A"),
        (["RAISING CANE"], "Raising Cane's"),
        (["COOK OUT", "COOKOUT"], "Cook Out"),
        (["WAFFLE HOUSE"], "Waffle House"),
        
        # Casual dining
        (["CHILIS", "CHILI'S", "CHILI S"], "Chili's"),
        (["BUFFALO", "BUFFALOWI"], "Buffalo Wild Wings"),
        (["ANDAMAN THAI"], "Thai Restaurant"),
        (["TOPGOLF"], "TopGolf"),
        (["PITA PIT"], "Pita Pit"),
        
        # Pizza
        (["DOMINO", "DOMINOS"], "Domino's"),
        (["PIZZA", "LITTLE ITALY"], "Pizza"),
        
        # Coffee shops
        (["STARBUCKS"], "Starbucks"),
        (["HIGH GROUND COFFEE"], "High Ground Coffee"),
        (["DUNKIN"], "Dunkin"),
        
        # Delivery services
        (["DD *DOORDASH", "DOORDASH"], "DoorDash"),
        (["GRUBHUB"], "Grubhub"),
        (["UBER *EATS", "UBER EATS", "UBEREATS", "UBER   *EATS"], "Uber Eats"),
        
        # Other specific places
        (["PANDA EXPRESS", "TECH DINING-PANDA"], "Panda Express"),
        (["BOARDTOWN"], "Boardtown Pies"),
        (["DAVES DARK HORSE"], "Dave's Dark Horse"),
        (["TAXI SHOP CAF"], "Taxi Shop Café"),
        (["RETAG FOOD"], "Food Vendor"),
    ]
    
    for patterns, label in restaurant_labels:
        for pattern in patterns:
            mask = df["description"].str.upper().str.contains(pattern.upper(), na=False)
            # Don't override vending machine labels
            mask = mask & (df["label"] != "Vending Machine")
            df.loc[mask, "label"] = label
    
    # ========== FINAL PASS: Ensure Vending Machine labels are applied ==========
    # Re-apply vending machine labels at the end to ensure they're not overwritten
    # Use regex=False to treat patterns literally (asterisks are part of merchant names)
    vending_final_patterns = [
        "AMK MSU",
        "AMK POD",
        "CTLP",  # All CTLP transactions are vending machines
        "COCA COLA CLARK",
        "COCA COLA SOUTH",
        "365 MARKET K",
    ]
    for pattern in vending_final_patterns:
        mask = df["description"].str.upper().str.contains(pattern.upper(), na=False, regex=False)
        df.loc[mask, "label"] = "Vending Machine"
    
    return df


def merge_all_csvs(csv_dir: str) -> pd.DataFrame:
    """Merge all CSV files into one DataFrame."""
    csv_path = Path(csv_dir)
    all_dfs = []
    
    # Load CapitalOne
    capital_one_files = list(csv_path.glob("CapitalOne*.csv"))
    for f in capital_one_files:
        print(f"Loading CapitalOne: {f.name}")
        df = load_capital_one(str(f))
        all_dfs.append(df)
        print(f"  Loaded {len(df)} transactions")
    
    # Load Discover
    discover_files = list(csv_path.glob("Discover*.csv"))
    for f in discover_files:
        print(f"Loading Discover: {f.name}")
        df = load_discover(str(f))
        all_dfs.append(df)
        print(f"  Loaded {len(df)} transactions")
    
    # Load Chase (extracted)
    chase_files = list(csv_path.glob("Chase_Extracted*.csv"))
    for f in chase_files:
        print(f"Loading Chase: {f.name}")
        df = load_chase(str(f))
        all_dfs.append(df)
        print(f"  Loaded {len(df)} transactions")
    
    if not all_dfs:
        print("No CSV files found!")
        return pd.DataFrame()
    
    # Combine all DataFrames
    merged = pd.concat(all_dfs, ignore_index=True)
    
    # Apply labels
    merged = apply_labels(merged)
    
    # Sort by date
    merged["date"] = pd.to_datetime(merged["date"])
    merged = merged.sort_values("date")
    merged["date"] = merged["date"].dt.strftime("%Y-%m-%d")
    
    return merged


def main():
    """Main function to merge all CSVs."""
    base_dir = Path(__file__).parent.parent
    csv_dir = base_dir / "csv"
    
    print("=" * 60)
    print("Merging All Credit Card Transactions")
    print("=" * 60)
    
    # Merge all CSVs
    merged_df = merge_all_csvs(str(csv_dir))
    
    if merged_df.empty:
        print("No transactions to merge")
        return
    
    # Save merged CSV
    output_path = csv_dir / "All_Transactions_Merged.csv"
    merged_df.to_csv(output_path, index=False)
    
    print(f"\n{'=' * 60}")
    print(f"Total transactions: {len(merged_df)}")
    print(f"Date range: {merged_df['date'].min()} to {merged_df['date'].max()}")
    print(f"Saved to: {output_path}")
    
    # Print label summary
    print(f"\nLabel Summary:")
    print(merged_df["label"].value_counts().to_string())
    
    # Print card summary
    print(f"\nCard Summary:")
    print(merged_df["card"].value_counts().to_string())


if __name__ == "__main__":
    main()
