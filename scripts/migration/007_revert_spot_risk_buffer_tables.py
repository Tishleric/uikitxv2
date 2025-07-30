
import sqlite3
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define database path
DB_PATH = Path(__file__).parent.parent.parent / "data" / "output" / "spot_risk" / "spot_risk.db"

def revert_migration():
    """
    Reverts the schema migration, restoring the original 'spot_risk_calculated' table.
    - Drops 'greeks_live_B' and 'active_view_pointer'.
    - Renames 'greeks_live_A' back to 'spot_risk_calculated'.
    - Re-creates the 'latest_calculations' view.
    """
    if not DB_PATH.exists():
        logging.error(f"Database not found at {DB_PATH}. Nothing to revert.")
        return

    logging.info(f"Connecting to database at {DB_PATH} to revert migration.")
    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            cursor = conn.cursor()

            # --- Step 1: Drop buffer tables and pointer ---
            logging.info("Dropping 'greeks_live_B' and 'active_view_pointer' tables...")
            cursor.execute("DROP TABLE IF EXISTS greeks_live_B;")
            cursor.execute("DROP TABLE IF EXISTS active_view_pointer;")

            # --- Step 2: Rename 'greeks_live_A' back to 'spot_risk_calculated' ---
            logging.info("Renaming 'greeks_live_A' back to 'spot_risk_calculated'...")
            try:
                # Check if 'greeks_live_A' exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='greeks_live_A';")
                if cursor.fetchone():
                    cursor.execute("ALTER TABLE greeks_live_A RENAME TO spot_risk_calculated;")
                else:
                    logging.warning("'greeks_live_A' not found, skipping rename.")
            except sqlite3.OperationalError as e:
                logging.warning(f"Could not rename 'greeks_live_A' (perhaps it was already renamed?): {e}")


            # --- Step 3: Re-create the 'latest_calculations' view ---
            logging.info("Re-creating 'latest_calculations' view...")
            cursor.execute("""
                CREATE VIEW IF NOT EXISTS latest_calculations AS
                SELECT 
                    r.instrument_key,
                    r.bloomberg_symbol,
                    r.instrument_type,
                    r.expiry_date,
                    r.strike,
                    r.midpoint_price,
                    c.*
                FROM spot_risk_raw r
                INNER JOIN spot_risk_calculated c ON r.id = c.raw_id
                WHERE c.id IN (
                    SELECT MAX(c2.id)
                    FROM spot_risk_calculated c2
                    GROUP BY c2.raw_id
                );
            """)

            conn.commit()
            logging.info("Migration reverted successfully.")

    except sqlite3.Error as e:
        logging.error(f"An error occurred during migration reversal: {e}", exc_info=True)

if __name__ == "__main__":
    revert_migration()