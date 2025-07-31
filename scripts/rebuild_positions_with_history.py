"""
Rebuilds positions and daily_positions tables from historical trade data.

This script orchestrates a two-part process:
1. Runs the comprehensive daily P&L simulation using specified close prices.
2. Runs the positions aggregator to populate the final master positions table.
"""

import sqlite3
from datetime import datetime
import sys
import os
import pandas as pd

# Add project root to path to allow for absolute imports
# This is a more robust way to handle pathing
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from lib.trading.pnl_fifo_lifo.test_simulation import run_comprehensive_daily_breakdown
from lib.trading.pnl_fifo_lifo.positions_aggregator import PositionsAggregator
from lib.trading.pnl_fifo_lifo.config import DB_NAME

def get_db_connection():
    """Establishes a connection to the database."""
    return sqlite3.connect(DB_NAME)

def main():
    """Main execution function."""
    print("--- Starting Historical Positions Rebuild ---")

    # Define the symbol and historical close prices
    # This assumes a single primary symbol from the trade files.
    symbol = ''
    close_prices = {
        datetime(2025, 7, 21).date(): {symbol: 111.1875},
        datetime(2025, 7, 22).date(): {symbol: 111.40625},
        datetime(2025, 7, 23).date(): {symbol: 111.015625},
        datetime(2025, 7, 24).date(): {symbol: 110.828125},
        datetime(2025, 7, 25).date(): {symbol: 110.984375},
        datetime(2025, 7, 28).date(): {symbol: 110.765625},
        datetime(2025, 7, 29).date(): {symbol: 111.359375},
    }

    # --- Part 1: Historical Simulation ---
    print("\n[Part 1/2] Running comprehensive daily breakdown simulation...")
    try:
        run_comprehensive_daily_breakdown(close_prices=close_prices)
        print("[Part 1/2] Historical simulation completed successfully.")
    except Exception as e:
        print(f"ERROR in historical simulation: {e}")
        return

    # --- Part 2: Final Position Aggregation ---
    print("\n[Part 2/2] Running final positions aggregation...")
    try:
        aggregator = PositionsAggregator(trades_db_path=DB_NAME)
        aggregator._load_positions_from_db()
        aggregator._write_positions_to_db()
        print("[Part 2/2] Final aggregation completed successfully.")
    except Exception as e:
        print(f"ERROR in final aggregation: {e}")
        return

    # --- Verification ---
    print("\n--- Verification ---")
    try:
        conn = get_db_connection()
        print("\nFinal 'daily_positions':")
        daily_df = pd.read_sql_query("SELECT * FROM daily_positions", conn)
        print(daily_df.to_string())

        print("\nFinal 'positions' table:")
        pos_df = pd.read_sql_query("SELECT symbol, open_position, closed_position, fifo_realized_pnl, fifo_unrealized_pnl FROM positions", conn)
        print(pos_df.to_string())
        
        conn.close()
    except Exception as e:
        print(f"ERROR during verification: {e}")

    print("\n--- Historical Positions Rebuild Complete ---")

if __name__ == '__main__':
    main()
