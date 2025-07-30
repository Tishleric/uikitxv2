import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
import pytz

# Configure logging
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DB_PATH = Path(__file__).parent / "trades.db"
CHICAGO_TZ = pytz.timezone('America/Chicago')

def validate_updates():
    """
    Connects to trades.db and queries the 'positions' and 'pricing' tables
    to validate that the consumer services are working correctly.
    """
    if not DB_PATH.exists():
        logging.error(f"Database not found at {DB_PATH}. Cannot run validation.")
        return

    logging.info(f"Connecting to database at {DB_PATH}")
    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            print("\n--- Positions Table (Consumer 2: PositionsAggregator) Validation ---")
            try:
                positions_df = pd.read_sql_query(
                    "SELECT symbol, last_greek_update, delta_y FROM positions WHERE last_greek_update IS NOT NULL ORDER BY last_greek_update DESC LIMIT 5",
                    conn
                )
                if not positions_df.empty:
                    print("Top 5 most recently updated positions (Greeks):")
                    positions_df['last_greek_update'] = pd.to_datetime(positions_df['last_greek_update']).dt.tz_localize('UTC').dt.tz_convert(CHICAGO_TZ)
                    print(positions_df.to_string(index=False))
                else:
                    print("No data with recent Greek updates found in the positions table.")
            except Exception as e:
                print(f"Could not query 'positions' table. It might not exist yet or an error occurred: {e}")

            print("\n--- Pricing Table (Consumer 1: PriceUpdaterService) Validation ---")
            try:
                pricing_df = pd.read_sql_query(
                    "SELECT symbol, price_type, price, timestamp FROM pricing WHERE price_type = 'now' ORDER BY timestamp DESC LIMIT 5",
                    conn
                )
                
                if not pricing_df.empty:
                    print("Top 5 most recently updated prices:")
                    pricing_df['timestamp'] = pd.to_datetime(pricing_df['timestamp']).dt.tz_localize('UTC').dt.tz_convert(CHICAGO_TZ)
                    print(pricing_df.to_string(index=False))
                else:
                    print("No data found in the pricing table.")
            except Exception as e:
                print(f"Could not query 'pricing' table. It might not exist yet or an error occurred: {e}")

    except sqlite3.Error as e:
        logging.error(f"An error occurred with the database: {e}", exc_info=True)

if __name__ == "__main__":
    validate_updates() 