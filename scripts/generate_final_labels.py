import json

def generate_final_labels():
    """
    Generates a curated list of the Top 10 most critical labels 
    for Loan, NDA, and Sales agreements.
    """
    
    # The 'labels' list is a list of Dictionaries (Key-Value pairs).
    # Each dictionary defines one label's name and its colors for the UI.
    labels = [
        # --- 1. THE BASICS (Who, When, Where) ---
        
        # Who is involved? (Borrower, Lender, Buyer, Seller, Discloser)
        # We merge them all into 'PARTY_NAME' so the model learns faster.
        {"text": "PARTY_NAME", "background_color": "#00008B", "text_color": "#ffffff"},
        
        # When does it start? (Effective Date, Agreement Date)
        {"text": "EFFECTIVE_DATE", "background_color": "#B22222", "text_color": "#ffffff"},
        
        # When does it end? (Maturity Date, Termination Date)
        {"text": "EXPIRATION_DATE", "background_color": "#DC143C", "text_color": "#ffffff"},
        
        # Where is the court? (New Delhi, London, New York)
        {"text": "JURISDICTION", "background_color": "#800080", "text_color": "#ffffff"},


        # --- 2. THE MONEY (Financials) ---
        
        # How much money? (Principal Amount, Purchase Price)
        # We merge 'Loan Amount' and 'Sales Price' into one strong label.
        {"text": "TOTAL_AMOUNT", "background_color": "#006400", "text_color": "#ffffff"},
        
        # Advanced: Cost of Money (Interest Rate, Penalty Fee %)
        # Crucial for Bank Loans.
        {"text": "INTEREST_RATE", "background_color": "#32CD32", "text_color": "#000000"},


        # --- 3. THE RISK CLAUSES (Advanced Legal Details) ---
        
        # Advanced: What assets are at risk? (Inventory, Machinery, House)
        # Crucial for Bank Loans (Secured vs Unsecured).
        {"text": "COLLATERAL", "background_color": "#2E8B57", "text_color": "#ffffff"},
        
        # Advanced: How long is the secret kept? (2 years, Perpetual)
        # Crucial for NDAs.
        {"text": "CONFIDENTIALITY_PERIOD", "background_color": "#FF8C00", "text_color": "#000000"},
        
        # Advanced: How do we get out? (30 days notice, 1 month notice)
        # Crucial for all agreements.
        {"text": "TERMINATION_NOTICE_PERIOD", "background_color": "#FF6347", "text_color": "#ffffff"},
        
        # Advanced: Which Law applies? (IT Act 2000, Laws of Delaware)
        # Distinct from Jurisdiction (City).
        {"text": "GOVERNING_LAW", "background_color": "#BA55D3", "text_color": "#ffffff"}
    ]
    
    # Define the output filename
    output_filename = "final_labels.json"
    
    # Open the file in 'Write' mode ('w')
    with open(output_filename, "w") as f:
        # json.dump converts our Python list into a text format Doccano understands
        # indent=4 makes it pretty and easy to read for humans
        json.dump(labels, f, indent=4)
        
    print(f"✅ Success! Generated '{output_filename}' with {len(labels)} labels.")
    print(f"📍 File location: {output_filename}")

# This block ensures the function runs only when you execute this script directly
if __name__ == "__main__":
    generate_final_labels()