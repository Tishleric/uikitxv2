#!/usr/bin/env python
"""Investigate TYU5 Coverage Gap

This script investigates why TYU5 isn't processing all symbols.
"""

import sys
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.trading.pnl_integration.tyu5_adapter import TYU5Adapter


def investigate_coverage():
    """Investigate why TYU5 isn't processing all symbols."""
    
    print("=" * 80)
    print("TYU5 COVERAGE INVESTIGATION")
    print("=" * 80)
    
    # Connect to database
    db_path = "data/output/pnl/pnl_tracker.db"
    conn = sqlite3.connect(db_path)
    
    # 1. Check what trades are in cto_trades
    print("\n1. CTO_TRADES ANALYSIS")
    print("-" * 60)
    
    cto_query = """
    SELECT 
        Symbol,
        COUNT(*) as trade_count,
        SUM(CASE WHEN Action = 'BUY' THEN Quantity ELSE 0 END) as total_buys,
        SUM(CASE WHEN Action = 'SELL' THEN Quantity ELSE 0 END) as total_sells,
        SUM(Quantity) as net_quantity,
        Type,
        MIN(Date) as first_trade,
        MAX(Date) as last_trade
    FROM cto_trades
    WHERE is_sod = 0 AND is_exercise = 0
    GROUP BY Symbol, Type
    ORDER BY Symbol
    """
    
    cto_df = pd.read_sql_query(cto_query, conn)
    print("\nCTO Trades Summary:")
    print(cto_df.to_string(index=False))
    
    # 2. Check what TYU5 adapter would query
    print("\n\n2. TYU5 ADAPTER QUERY TEST")
    print("-" * 60)
    
    adapter = TYU5Adapter(db_path)
    trades_for_tyu5 = adapter.get_trades_for_calculation()
    
    print(f"\nTYU5 Adapter found {len(trades_for_tyu5)} trades")
    if not trades_for_tyu5.empty:
        print("\nSymbols in TYU5 query:")
        tyu5_symbols = trades_for_tyu5['Symbol'].unique()
        for symbol in sorted(tyu5_symbols):
            count = len(trades_for_tyu5[trades_for_tyu5['Symbol'] == symbol])
            print(f"  - {symbol}: {count} trades")
    
    # 3. Compare CTO symbols vs TYU5 symbols
    print("\n\n3. SYMBOL COMPARISON")
    print("-" * 60)
    
    cto_symbols = set(cto_df['Symbol'].unique())
    tyu5_symbols = set(trades_for_tyu5['Symbol'].unique()) if not trades_for_tyu5.empty else set()
    
    print(f"\nSymbols in CTO trades: {len(cto_symbols)}")
    print(f"Symbols in TYU5 query: {len(tyu5_symbols)}")
    
    missing_in_tyu5 = cto_symbols - tyu5_symbols
    if missing_in_tyu5:
        print(f"\nSymbols in CTO but NOT in TYU5 ({len(missing_in_tyu5)}):")
        for symbol in sorted(missing_in_tyu5):
            print(f"  - {symbol}")
    
    # 4. Check symbol transformation
    print("\n\n4. SYMBOL TRANSFORMATION ANALYSIS")
    print("-" * 60)
    
    if not trades_for_tyu5.empty:
        print("\nTYU5 Symbol Transformations:")
        # Show original CTO symbols vs transformed TYU5 symbols
        print("\nCTO Symbols -> TYU5 Format:")
        
        # For each unique CTO symbol, show what it becomes in TYU5
        for cto_symbol in sorted(cto_symbols):
            # Find if this symbol appears in TYU5 (after transformation)
            # Options get transformed significantly
            if cto_symbol.startswith('VBY'):
                # VBYN25P3 109.500 Comdty -> VY3N5 P 109.500
                print(f"  {cto_symbol} -> [transformed to VY format]")
            elif cto_symbol.startswith('TYW'):
                # TYWN25P4 109.750 Comdty -> WY4N5 P 109.750
                print(f"  {cto_symbol} -> [transformed to WY format]")
            else:
                # Futures and other symbols stay mostly the same
                print(f"  {cto_symbol} -> {cto_symbol}")
                
        print("\nNOTE: Option symbol transformation:")
        print("  Bloomberg format: VBYN25P3 109.500 Comdty")
        print("  TYU5 format:     VY3N5 P 109.500")
    
    # 5. Check what positions are being tracked
    print("\n\n5. POSITION TRACKING TYPE")
    print("-" * 60)
    
    positions_query = """
    SELECT 
        instrument_name,
        position_quantity,
        CASE 
            WHEN position_quantity > 0 THEN 'LONG'
            WHEN position_quantity < 0 THEN 'SHORT'
            ELSE 'FLAT'
        END as position_type,
        is_option,
        total_realized_pnl,
        unrealized_pnl
    FROM positions
    WHERE position_quantity != 0
    ORDER BY instrument_name
    """
    
    positions_df = pd.read_sql_query(positions_query, conn)
    print("\nPositions Summary:")
    print(positions_df.to_string(index=False))
    
    print("\n\nPOSITION TRACKING EXPLANATION:")
    print("-" * 40)
    print("We are tracking NET POSITIONS:")
    print("- Open positions: Non-zero net quantity (long or short)")
    print("- Closed positions: Zero net quantity (not shown)")
    print("- Position = Sum of all trades for that symbol")
    print("- Positive quantity = LONG position")
    print("- Negative quantity = SHORT position")
    
    # 6. Check for any filters or issues
    print("\n\n6. POTENTIAL ISSUES")
    print("-" * 60)
    
    # Check for excluded trades
    excluded_query = """
    SELECT 
        Symbol,
        COUNT(*) as excluded_count,
        SUM(CASE WHEN is_sod = 1 THEN 1 ELSE 0 END) as sod_trades,
        SUM(CASE WHEN is_exercise = 1 THEN 1 ELSE 0 END) as exercise_trades
    FROM cto_trades
    WHERE is_sod = 1 OR is_exercise = 1
    GROUP BY Symbol
    """
    
    excluded_df = pd.read_sql_query(excluded_query, conn)
    if not excluded_df.empty:
        print("\nExcluded Trades:")
        print(excluded_df.to_string(index=False))
    else:
        print("\nNo trades excluded (good!)")
    
    # 7. Check market prices availability
    print("\n\n7. MARKET PRICE AVAILABILITY")
    print("-" * 60)
    
    # Get market prices that TYU5 would see
    market_prices = adapter.get_market_prices()
    if not market_prices.empty:
        print(f"\nMarket prices available: {len(market_prices)} symbols")
        tyu5_price_symbols = set(market_prices['Symbol'].unique())
        
        # Check which trade symbols have prices
        if not trades_for_tyu5.empty:
            trade_symbols_in_tyu5 = set(trades_for_tyu5['Symbol'].unique())
            symbols_without_prices = trade_symbols_in_tyu5 - tyu5_price_symbols
            
            if symbols_without_prices:
                print(f"\nTYU5 trade symbols WITHOUT market prices ({len(symbols_without_prices)}):")
                for symbol in sorted(symbols_without_prices):
                    print(f"  - {symbol}")
    else:
        print("\nNo market prices found!")
    
    conn.close()
    
    # Summary
    print("\n\n" + "=" * 80)
    print("INVESTIGATION SUMMARY")
    print("=" * 80)
    
    print("\nKEY FINDINGS:")
    print("1. Position Tracking Type: NET POSITIONS (open positions only)")
    print("2. CTO trades has all symbols but TYU5 may be transforming them")
    print("3. Symbol transformation for options changes format significantly")
    print("4. Market price availability may affect what gets processed")
    
    if missing_in_tyu5:
        print(f"\nMISSING SYMBOLS: {len(missing_in_tyu5)} symbols in CTO not processed by TYU5")
        print("Likely causes:")
        print("- Symbol transformation issues")
        print("- Market price lookup failures")
        print("- TYU5 internal filtering")


if __name__ == "__main__":
    investigate_coverage() 