import sqlite3
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define database path
DB_PATH = Path(__file__).parent.parent / "trades.db"

def drop_deprecated_price_tables():
    """
    Connects to trades.db and drops the old, unused 'futures_prices' and
    'options_prices' tables, which have been replaced by the 'pricing' table.
    """
    if not DB_PATH.exists():
        logging.error(f"Database not found at {DB_PATH}. Cannot run cleanup.")
        return

    logging.info(f"Connecting to database at {DB_PATH} to drop deprecated tables.")
    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            cursor = conn.cursor()

            logging.info("Dropping 'futures_prices' table...")
            cursor.execute("DROP TABLE IF EXISTS futures_prices;")

            logging.info("Dropping 'options_prices' table...")
            cursor.execute("DROP TABLE IF EXISTS options_prices;")

            conn.commit()
            logging.info("Deprecated price tables dropped successfully.")

    except sqlite3.Error as e:
        logging.error(f"An error occurred during table cleanup: {e}", exc_info=True)

if __name__ == "__main__":
    drop_deprecated_price_tables() 