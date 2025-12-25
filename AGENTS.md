We are working on an credit card expense tracker
How this works:
PHASE 1
1.) I put all the pdfs, of different banks, in one folder.

2.) Using gemini-3.0-flash-preview model, all the transactions are converted into one csv file where they are sorted by date
a) CSV files for discover and capital one are available.
b) Convert different pdfs of chase 7557 and 2040 card into one csv
c) merge all csv files together
d) Labeling rules:
   - Vending Machine: AMK MSU POD UNION, CTLP*REFRESHMENTS INC, COCA COLA CLARK STARKVIL, CTLP*GREENSBORO VENDIN
   - Electricity: SIMPLEBILLS, SIMPLE BILLS
   - Gas Station Indiscretion: SHELL, LOVE'S, BUC-EE'S, EXXON, CHEVRON, MARATHON, MURPHY, QT (QuikTrip), PILOT, CIRCLE K, SPRINT MART, 76 - DEES OIL
   - Walmart: All WALMART related transactions (WALMART.COM, WAL-MART, WM SUPERCENTER, etc.)
   - Only label as "Gasoline" for gas transactions above $30 (actual fuel fill-ups)
   
   - Shopping/Services labels:
     * Books: KINDLE, MCNALLY JACKSON BOOKS
     * Amazon Shopping: AMAZON (not Prime, not Kindle)
     * Amazon Prime: AMAZON PRIME
     * Netflix: NETFLIX
     * LinkedIn: LINKEDIN
     * Resume Services: STP*V*resume-example, RESUMEEXAMPLE
     * API Costs: GOOGLE *CLOUD, GOOGLE COLAB, AWS, AMAZON WEB SERVICES, ELEVENLABS, ELEVEN LABS
     * Uber Taxi: UBER *TRIP (not Uber Eats)
     * Clothes: MARSHALLS, CENTURY 21, H&M, NIKE, KLARNA*NIKE, FIVE BELOW
     * Disney+: DISNEY PLUS
     * YouTube: YOUTUBE
     * Google One: GOOGLE ONE
     * Hinge: HINGE
     * Apple: APPLE.COM
     * Microsoft: MICROSOFT
   
   - Restaurant-specific labels:
     * Wendy's: WENDYS, WENDY'S
     * McDonald's: MCDONALD, MCDONALDS
     * Taco Bell: TACO BELL
     * Burger King: BURGER KING
     * Chick-fil-A: CHICK-FIL-A, CHICKFILA
     * Chili's: CHILIS, CHILI'S
     * DoorDash: DOORDASH, DD *DOORDASH
     * Grubhub: GRUBHUB
     * Uber Eats: UBER *EATS, UBER EATS
     * Starbucks: STARBUCKS
     * Dunkin: DUNKIN
     * Panda Express: PANDA EXPRESS
     * Waffle House: WAFFLE HOUSE
     * Cook Out: COOK OUT, COOKOUT
     * Buffalo Wild Wings: BUFFALO, BUFFALOWI
     * Domino's: DOMINO, DOMINOS
     * Pizza places: PIZZA, LITTLE ITALY PIZZA
     * Raising Cane's: RAISING CANE
     * High Ground Coffee: HIGH GROUND COFFEE
     * Other Dining: Any other restaurant/dining transaction
   
e) Trip expense filtering rules:
   - Exclude Walmart transactions over $30 from trip calculations (likely pre-ordered items that settled during trip)

3.) Generate diagrams in two folders:

a) trip_diagrams/ - Specific trip expense reports:
   - NYC Trip: July 1 to July 7, 2025
   - Atlanta: August 16, 2025 (same day return)
   - Dallas: October 3, 2025 to October 5, 2025
   - North Carolina: October 16 to October 19
   - Memphis: October 20, 2025 (same day return)
   - Atlanta: November 7 to November 9, 2025
   - Memphis: November 25 2025 to November 26, 2025

b) overall_diagrams/ - Overall expense analysis:
   - Monthly spending trends
   - Spending by category (pie chart)
   - Spending by card
   - Top merchants/labels
   - Daily/weekly spending patterns
   - Restaurant spending breakdown
   - Gas station spending analysis
   - Walmart spending trends

PHASE 2:
Make a frontend where peope can put their pdf, details about their trip and get end to end analysis like above