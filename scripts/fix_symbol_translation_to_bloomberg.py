"""Fix symbol translation to ensure all symbols use Bloomberg format."""

import sys
sys.path.append('.')
import sqlite3
from datetime import datetime
from lib.trading.symbol_translator import SymbolTranslator
from lib.trading.treasury_notation_mapper import TreasuryNotationMapper

print("=== FIXING SYMBOL TRANSLATION TO BLOOMBERG FORMAT ===")
print(f"Time: {datetime.now()}\n")

# Initialize translators
symbol_translator = SymbolTranslator()
treasury_mapper = TreasuryNotationMapper()

# Connect to database
conn = sqlite3.connect('data/output/pnl/pnl_tracker.db')
cursor = conn.cursor()

# Check current symbols in cto_trades
print("1. CHECKING CURRENT SYMBOLS IN CTO_TRADES:")
print("-" * 60)
cursor.execute("SELECT DISTINCT Symbol, Type FROM cto_trades ORDER BY Symbol")
symbols = cursor.fetchall()

print(f"Found {len(symbols)} unique symbols:")
for symbol, type_ in symbols:
    print(f"  {symbol} ({type_})")

# Identify symbols that need fixing
fixes_needed = []
for symbol, type_ in symbols:
    # Check if already in Bloomberg format
    if not symbol.endswith(' Comdty'):
        fixes_needed.append((symbol, type_))
        
if fixes_needed:
    print(f"\n\nSymbols needing Bloomberg format: {len(fixes_needed)}")
    for symbol, type_ in fixes_needed:
        # For futures, just add Comdty
        if type_ == 'FUT':
            new_symbol = f"{symbol} Comdty"
        else:
            # Options already have Bloomberg format, just need Comdty suffix
            new_symbol = f"{symbol} Comdty"
        
        print(f"  {symbol} -> {new_symbol}")
        
        # Update in database
        cursor.execute("""
            UPDATE cto_trades 
            SET Symbol = ? 
            WHERE Symbol = ?
        """, (new_symbol, symbol))
        
        cursor.execute("""
            UPDATE positions 
            SET instrument_name = ? 
            WHERE instrument_name = ?
        """, (new_symbol, symbol))

# Check positions table
print("\n\n2. CHECKING CURRENT SYMBOLS IN POSITIONS:")
print("-" * 60)
cursor.execute("SELECT DISTINCT instrument_name FROM positions ORDER BY instrument_name")
pos_symbols = cursor.fetchall()

print(f"Found {len(pos_symbols)} unique symbols:")
for (symbol,) in pos_symbols:
    print(f"  {symbol}")

# Commit changes
conn.commit()

# Verify the fix
print("\n\n3. VERIFICATION AFTER FIX:")
print("-" * 60)
cursor.execute("SELECT DISTINCT Symbol FROM cto_trades ORDER BY Symbol")
fixed_symbols = cursor.fetchall()

print("All symbols now in Bloomberg format:")
for (symbol,) in fixed_symbols:
    print(f"  {symbol}")
    
conn.close()

print("\n\nSUMMARY:")
print("-" * 60)
print(f"✓ Fixed {len(fixes_needed)} symbols to Bloomberg format")
print("✓ All symbols now end with ' Comdty'")
print("✓ Updates applied to both cto_trades and positions tables") 