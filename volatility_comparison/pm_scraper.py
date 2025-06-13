"""
Scrape Pricing Monkey for market greeks data
"""

import time
import webbrowser
import pyperclip
from pywinauto.keyboard import send_keys
import pandas as pd
from bond_option_pricer import parse_treasury_price

PM_URL = "https://pricingmonkey.com/b/d815cb0e-74bf-4fc6-8975-550319ca8dad"

def scrape_pm():
    """Automate browser to copy PM data"""
    # Clear clipboard
    pyperclip.copy("")
    
    # Open URL
    print(f"Opening browser to: {PM_URL}")
    print("NOTE: You must be signed in to Pricing Monkey for this to work!")
    webbrowser.open(PM_URL, new=2)
    
    # Wait longer for page load and sign-in
    print("Waiting 30 seconds for page to load and bid/ask to populate...")
    time.sleep(30)
    
    # Navigate to data
    print("Navigating to data...")
    send_keys('{TAB 7}')
    time.sleep(0.5)
    send_keys('{DOWN}')
    time.sleep(0.5)
    
    # Select range (5x8) - hold shift while moving
    print("Selecting data range...")
    send_keys('+{DOWN 5}')  # Shift+Down 5 times
    time.sleep(0.5)
    send_keys('+{RIGHT 8}')  # Shift+Right 8 times
    time.sleep(0.5)
    
    # Copy
    print("Copying to clipboard...")
    send_keys('^c')
    time.sleep(3)  # Wait longer for clipboard
    
    # Close browser
    send_keys('^w')
    
    return pyperclip.paste()

def clean_price_format(price_str):
    """Clean price format - remove leading zeros and dashes, but don't convert to decimal"""
    if not price_str:
        return ""
    
    # Remove leading zeros and dashes (0-02 -> 2, 0-17 -> 17)
    cleaned = price_str.strip()
    if cleaned.startswith('0-'):
        cleaned = cleaned[2:]  # Remove "0-" prefix
    elif cleaned.startswith('-'):
        cleaned = cleaned[1:]   # Remove "-" prefix
    
    return cleaned

def parse_clipboard(data):
    """Parse clipboard TSV data into DataFrame"""
    lines = data.strip().split('\n')
    if len(lines) < 1:
        return pd.DataFrame()
    
    # Parse TSV - start from line 0 to avoid dropping first data row
    rows = []
    for i, line in enumerate(lines):
        cols = line.split('\t')
        if len(cols) >= 9:
            # Check if this looks like a header row
            if i == 0 and ('description' in cols[0].lower() or 'trade' in cols[0].lower()):
                continue  # Skip header row
            
            # Parse strike as-is (already in decimal format, no processing needed)
            try:
                strike = float(cols[3]) if cols[3] else 0
            except:
                strike = 0
            
            # Parse underlying as treasury format and convert to decimal
            underlying_decimal = parse_treasury_price(cols[4]) if cols[4] else 0
            
            # Clean price, bid, ask formats but DON'T convert to decimal
            price_clean = clean_price_format(cols[6])
            bid_clean = clean_price_format(cols[7])
            ask_clean = clean_price_format(cols[8])
            
            # Parse vol as float (should be percentage)
            try:
                vol = float(cols[5].replace('%', '')) if cols[5] else 0
            except:
                vol = 0
            
            rows.append({
                'description': cols[0],
                'days': cols[1],
                'expiry': cols[2],
                'strike': strike,
                'underlying': cols[4],  # Keep original format
                'underlying_decimal': underlying_decimal,  # Add decimal version
                'vol': vol,
                'price': price_clean,
                'bid': bid_clean,
                'ask': ask_clean
            })
    
    return pd.DataFrame(rows)

if __name__ == "__main__":
    print("Scraping Pricing Monkey...")
    try:
        clipboard_data = scrape_pm()
        
        print("=" * 80)
        print("RAW CLIPBOARD DATA:")
        print("=" * 80)
        print(clipboard_data)
        print("=" * 80)
        print(f"Clipboard data length: {len(clipboard_data)} characters")
        print(f"Number of lines: {len(clipboard_data.split('\n')) if clipboard_data else 0}")
        print()
        
        if clipboard_data:
            df = parse_clipboard(clipboard_data)
            if not df.empty:
                df.to_csv('pm_data.csv', index=False)
                print(f"Successfully saved {len(df)} records to pm_data.csv")
                print()
                print("=" * 80)
                print("FULL PARSED DATAFRAME:")
                print("=" * 80)
                print(df.to_string(index=False, max_rows=None, max_cols=None))
                print("=" * 80)
                print()
                print("Column info:")
                for col in df.columns:
                    print(f"  {col}: {df[col].dtype}")
            else:
                print("ERROR: Failed to parse clipboard data into DataFrame")
                print(f"First 500 chars of clipboard: {clipboard_data[:500]}...")
        else:
            print("ERROR: No data in clipboard")
    except Exception as e:
        print(f"ERROR during PM scraping: {e}")
        import traceback
        traceback.print_exc() 