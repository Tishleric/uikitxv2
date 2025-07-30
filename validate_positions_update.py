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
            print("\n--- Positions Table (Consumer 2) Validation ---")
            try:
                positions_df = pd.read_sql_query(
                    "SELECT symbol, last_greek_update, delta_y FROM positions ORDER BY last_greek_update DESC LIMIT 5",
                    conn
                )
                if not positions_df.empty:
                    print("Top 5 most recently updated positions (Greeks):")
                    positions_df['last_greek_update'] = pd.to_datetime(positions_df['last_greek_update']).dt.tz_localize('UTC').dt.tz_convert(CHICAGO_TZ)
                    print(positions_df.to_string(index=False))
                else:
                    print("No data found in the positions table.")
            except Exception as e:
                print(f"Could not query 'positions' table. It might not exist yet or an error occurred: {e}")

            print("\n--- Pricing Table (Consumer 1) Validation ---")
            try:
                # Query both futures and options pricing tables and combine them
                futures_prices_df = pd.read_sql_query(
                    "SELECT symbol, Current_Price, last_updated FROM futures_prices ORDER BY last_updated DESC LIMIT 5",
                    conn
                )
                options_prices_df = pd.read_sql_query(
                    "SELECT symbol, Current_Price, last_updated FROM options_prices ORDER BY last_updated DESC LIMIT 5",
                    conn
                )
                
                # Combine and find the top 5 most recent overall
                all_prices_df = pd.concat([futures_prices_df, options_prices_df])
                all_prices_df['last_updated'] = pd.to_datetime(all_prices_df['last_updated'])
                all_prices_df.sort_values(by='last_updated', ascending=False, inplace=True)
                top_5_prices = all_prices_df.head(5)

                if not top_5_prices.empty:
                    print("Top 5 most recently updated prices:")
                    top_5_prices['last_updated'] = top_5_prices['last_updated'].dt.tz_localize('UTC').dt.tz_convert(CHICAGO_TZ)
                    print(top_5_prices.to_string(index=False))
                else:
                    print("No data found in the pricing tables.")
            except Exception as e:
                print(f"Could not query pricing tables. They might not exist yet or an error occurred: {e}")

    except sqlite3.Error as e:
        logging.error(f"An error occurred with the database: {e}", exc_info=True)

if __name__ == "__main__":
    validate_updates() 