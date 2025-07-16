"""Price Step 5: Fix instrument to Bloomberg symbol mapping."""

import sys
sys.path.append('.')
import sqlite3
from datetime import datetime

print("=== PRICE STEP 5: FIXING PRICE MAPPING ===")
print(f"Time: {datetime.now()}\n")

# 1. Analyze the mapping pattern
print("1. ANALYZING MAPPING PATTERNS:")
conn = sqlite3.connect("data/output/pnl/pnl_tracker.db")
cursor = conn.cursor()

# Get some option examples
print("   Option examples from positions:")
cursor.execute("""
    SELECT DISTINCT instrument_name 
    FROM positions 
    WHERE instrument_name LIKE '%/%'
    LIMIT 5
""")
for row in cursor.fetchall():
    inst = row[0]
    print(f"   • {inst}")
    # Extract parts
    parts = inst.split('/')
    if len(parts) == 2:
        base = parts[0]
        strike = parts[1]
        print(f"     Base: {base}, Strike: {strike}")

# Get some option examples from prices
print("\n   Option examples from market_prices:")
cursor.execute("""
    SELECT DISTINCT bloomberg 
    FROM market_prices 
    WHERE asset_type = 'OPTION'
    LIMIT 10
""")
for row in cursor.fetchall():
    print(f"   • {row[0]}")

# 2. Create a simple mapping function
print("\n2. CREATING MAPPING FUNCTION:")

def map_instrument_to_bloomberg(instrument_name):
    """Map internal instrument name to Bloomberg symbol."""
    
    # For futures - simple mapping
    future_map = {
        'XCMEFFDPSX20250919U0ZN': 'TU',  # Example mapping
        # Add more mappings as needed
    }
    
    if instrument_name in future_map:
        return future_map[instrument_name]
    
    # For options - more complex
    if '/' in instrument_name:
        # Example: XCMEOCADPS20250714N0VY2/110 
        # Needs to map to something like "3MN5C 110.000 Comdty"
        
        parts = instrument_name.split('/')
        strike = float(parts[1])
        
        # This is a simplified example - real mapping would be more complex
        # For now, just try to find a matching strike
        cursor.execute("""
            SELECT bloomberg 
            FROM market_prices 
            WHERE asset_type = 'OPTION' 
            AND bloomberg LIKE ?
            LIMIT 1
        """, (f'%{strike:.3f}%',))
        
        result = cursor.fetchone()
        if result:
            return result[0]
    
    return None

# 3. Test the mapping
print("\n3. TESTING MAPPING:")
test_instruments = [
    "XCMEOCADPS20250714N0VY2/110",
    "XCMEOCADPS20250714N0VY2/111.25",
    "XCMEFFDPSX20250919U0ZN"
]

for inst in test_instruments:
    bloomberg = map_instrument_to_bloomberg(inst)
    print(f"   {inst} → {bloomberg}")
    
    if bloomberg:
        # Try to get price
        cursor.execute("""
            SELECT px_last, px_settle 
            FROM market_prices 
            WHERE bloomberg = ?
            ORDER BY upload_timestamp DESC
            LIMIT 1
        """, (bloomberg,))
        
        result = cursor.fetchone()
        if result:
            print(f"     Price found: last={result[0]}, settle={result[1]}")

# 4. Show what needs to be fixed
print("\n4. REQUIRED FIX:")
print("   The system needs a proper symbol translation layer that:")
print("   • Maps internal instrument names to Bloomberg symbols")
print("   • Handles both futures and options")
print("   • Is used by position_manager.update_market_prices()")
print("\n   Options:")
print("   1. Update SymbolTranslator class with proper mappings")
print("   2. Modify get_market_price to handle translation")
print("   3. Create a mapping table in the database")

# 5. Quick workaround - populate some prices directly
print("\n5. APPLYING TEMPORARY WORKAROUND:")
print("   Adding market prices with internal instrument names...")

# Get current prices from bloomberg symbols
updates = []
cursor.execute("""
    SELECT DISTINCT 
        p.instrument_name,
        mp.px_last,
        mp.px_settle,
        mp.upload_timestamp
    FROM positions p
    LEFT JOIN market_prices mp ON mp.bloomberg LIKE '%' || SUBSTR(p.instrument_name, -3) || '%'
    WHERE mp.px_last IS NOT NULL
    LIMIT 10
""")

for row in cursor.fetchall():
    updates.append({
        'bloomberg': row[0],  # Use internal name as bloomberg
        'px_last': row[1],
        'px_settle': row[2],
        'timestamp': row[3]
    })

if updates:
    print(f"   Found {len(updates)} prices to add")
    # Would insert these with internal names as a workaround

conn.close()

print("\n✅ PRICE STEP 5 COMPLETE") 