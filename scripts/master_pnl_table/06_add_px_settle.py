#!/usr/bin/env python3
"""
Add px_settle column to FULLPNL table.
Populates with prior_close data from market_prices database.
"""
import sqlite3
from pathlib import Path
from datetime import datetime

def add_px_settle_column():
    """Add px_settle column to FULLPNL table and populate from market_prices."""
    
    # Database paths - go up two levels to project root
    project_root = Path(__file__).parent.parent.parent
    pnl_db_path = project_root / "data/output/pnl/pnl_tracker.db"
    market_prices_db_path = project_root / "data/output/market_prices/market_prices.db"
    
    if not pnl_db_path.exists():
        print(f"Error: P&L database not found at {pnl_db_path}")
        return
        
    if not market_prices_db_path.exists():
        print(f"Error: Market prices database not found at {market_prices_db_path}")
        return
    
    conn = sqlite3.connect(pnl_db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(FULLPNL)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'px_settle' not in columns:
            print("Adding px_settle column to FULLPNL table...")
            cursor.execute("ALTER TABLE FULLPNL ADD COLUMN px_settle REAL")
            conn.commit()
            print("✓ px_settle column added")
        else:
            print("px_settle column already exists")
        
        # Attach market prices database
        cursor.execute(f"ATTACH DATABASE '{market_prices_db_path}' AS market_prices")
        
        # First, determine what trade dates we have
        cursor.execute("""
            SELECT DISTINCT trade_date 
            FROM market_prices.futures_prices 
            ORDER BY trade_date DESC 
            LIMIT 2
        """)
        dates = cursor.fetchall()
        
        if len(dates) < 2:
            print("Error: Need at least 2 trade dates in market_prices database")
            return
            
        # Date logic: 
        # - px_last comes from current_price on date T
        # - px_settle comes from prior_close on date T+1 (which represents the close from date T)
        # This is because prior_close on any given date represents the previous day's close
        current_trade_date = dates[1][0]  # Second most recent date (T)
        next_trade_date = dates[0][0]     # Most recent date (T+1)
        
        print(f"Using trade dates:")
        print(f"  Current trade date (T): {current_trade_date}")
        print(f"  Next trade date (T+1): {next_trade_date}")
        print(f"  px_settle will use prior_close from {next_trade_date} (which represents close of {current_trade_date})")
        
        # Get all symbols from FULLPNL
        cursor.execute("SELECT symbol FROM FULLPNL")
        symbols = cursor.fetchall()
        print(f"\nProcessing {len(symbols)} symbols...")
        
        updated_count = 0
        missing_count = 0
        
        for (symbol,) in symbols:
            px_settle = None
            print(f"\nProcessing: {symbol}")
            
            # Check if it's a future (ends with "Comdty" but no strike price)
            # Options have format: "SYMBOL STRIKE Comdty" where STRIKE contains a decimal
            # Futures have format: "SYMBOL Comdty" with no strike
            parts = symbol.split()
            is_option = len(parts) == 3 and '.' in parts[1]  # Has strike price in middle
            
            if not is_option:
                print("  Detected as FUTURE")
                # It's a future - strip " Comdty" and look in futures_prices
                base_symbol = symbol.replace(" Comdty", "")
                
                cursor.execute("""
                    SELECT prior_close 
                    FROM market_prices.futures_prices 
                    WHERE symbol = ?
                    AND trade_date = ?
                    ORDER BY last_updated DESC
                    LIMIT 1
                """, (base_symbol, next_trade_date))
                
                result = cursor.fetchone()
                if result and result[0] is not None:
                    px_settle = result[0]
                    print(f"Future {symbol} -> {base_symbol}: px_settle = {px_settle}")
            else:
                print("  Detected as OPTION")
                # It's an option - match exact symbol in options_prices
                cursor.execute("""
                    SELECT prior_close 
                    FROM market_prices.options_prices 
                    WHERE symbol = ? 
                    AND trade_date = ?
                    ORDER BY last_updated DESC
                    LIMIT 1
                """, (symbol, next_trade_date))
                
                result = cursor.fetchone()
                if result:
                    if result[0] is not None:
                        px_settle = result[0]
                        print(f"Option {symbol}: px_settle = {px_settle}")
                    else:
                        print(f"Option {symbol}: prior_close is NULL in database")
                else:
                    print(f"Option {symbol}: No record found for trade_date {next_trade_date}")
            
            # Update FULLPNL with px_settle
            if px_settle is not None:
                cursor.execute("""
                    UPDATE FULLPNL 
                    SET px_settle = ?
                    WHERE symbol = ?
                """, (px_settle, symbol))
                updated_count += 1
            else:
                print(f"⚠ No prior_close found for {symbol}")
                missing_count += 1
        
        conn.commit()
        
        # Show summary
        print(f"\n{'='*60}")
        print(f"SUMMARY - px_settle Column Population:")
        print(f"{'='*60}")
        print(f"Total symbols: {len(symbols)}")
        print(f"Successfully updated: {updated_count} ({updated_count/len(symbols)*100:.1f}%)")
        print(f"Missing data: {missing_count} ({missing_count/len(symbols)*100:.1f}%)")
        
        # Show final table state
        print(f"\n{'='*60}")
        print("FULLPNL Table with px_settle:")
        print(f"{'='*60}")
        
        cursor.execute("""
            SELECT symbol, bid, ask, price, px_last, px_settle
            FROM FULLPNL
            ORDER BY symbol
        """)
        
        results = cursor.fetchall()
        
        # Print header
        print(f"{'Symbol':<30} {'Bid':>10} {'Ask':>10} {'Price':>10} {'px_last':>10} {'px_settle':>10}")
        print("-" * 90)
        
        # Print data
        for row in results:
            symbol, bid, ask, price, px_last, px_settle = row
            bid_str = f"{bid:.6f}" if bid is not None else "NULL"
            ask_str = f"{ask:.6f}" if ask is not None else "NULL"
            price_str = f"{price:.6f}" if price is not None else "NULL"
            px_last_str = f"{px_last:.6f}" if px_last is not None else "NULL"
            px_settle_str = f"{px_settle:.6f}" if px_settle is not None else "NULL"
            
            print(f"{symbol:<30} {bid_str:>10} {ask_str:>10} {price_str:>10} {px_last_str:>10} {px_settle_str:>10}")
        
        # Show comparison between px_last and px_settle where both exist
        print(f"\n{'='*60}")
        print("Price Comparison (px_last vs px_settle):")
        print(f"{'='*60}")
        
        cursor.execute("""
            SELECT symbol, px_last, px_settle, (px_last - px_settle) as diff
            FROM FULLPNL
            WHERE px_last IS NOT NULL AND px_settle IS NOT NULL
            ORDER BY symbol
        """)
        
        comparisons = cursor.fetchall()
        if comparisons:
            print(f"{'Symbol':<30} {'px_last':>10} {'px_settle':>10} {'Diff':>10}")
            print("-" * 60)
            
            for symbol, px_last, px_settle, diff in comparisons:
                print(f"{symbol:<30} {px_last:>10.6f} {px_settle:>10.6f} {diff:>10.6f}")
        else:
            print("No symbols have both px_last and px_settle for comparison")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        cursor.execute("DETACH DATABASE market_prices")
        conn.close()

if __name__ == "__main__":
    print("Adding px_settle column to FULLPNL table...")
    print(f"Timestamp: {datetime.now()}")
    add_px_settle_column() 