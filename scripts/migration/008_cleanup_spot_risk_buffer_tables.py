import sqlite3
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define database path
DB_PATH = Path(__file__).parent.parent.parent / "data" / "output" / "spot_risk" / "spot_risk.db"

def apply_cleanup():
    """
    Applies schema cleanup to remove the double-buffer tables, which are now
    redundant after the move to a Redis-based pipeline. This reverts the changes
    made in migration 006.
    """
    if not DB_PATH.exists():
        logging.warning(f"Database not found at {DB_PATH}. No cleanup needed.")
        return

    logging.info(f"Connecting to database at {DB_PATH} to perform cleanup.")
    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            cursor = conn.cursor()

            # --- Step 1: Drop the buffer tables and the pointer table ---
            logging.info("Dropping 'greeks_live_A', 'greeks_live_B', and 'active_view_pointer' tables...")
            cursor.execute("DROP TABLE IF EXISTS greeks_live_A;")
            cursor.execute("DROP TABLE IF EXISTS greeks_live_B;")
            cursor.execute("DROP TABLE IF EXISTS active_view_pointer;")

            # --- Step 2: Re-create the original 'spot_risk_calculated' table ---
            # This ensures the schema is clean for any processes that might still reference it,
            # though it will no longer be populated by the new pipeline.
            logging.info("Re-creating original 'spot_risk_calculated' table for schema consistency.")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS spot_risk_calculated (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    raw_id INTEGER NOT NULL,
                    session_id INTEGER NOT NULL,
                    calculation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    model_version TEXT NOT NULL,
                    implied_vol REAL,
                    delta_F REAL, delta_y REAL, vega_y REAL, vega_price REAL,
                    theta_F REAL, rho_y REAL, gamma_F REAL, gamma_y REAL,
                    vanna_F_y REAL, vanna_F_price REAL, charm_F REAL,
                    volga_y REAL, volga_price REAL, veta_y REAL,
                    speed_F REAL, color_F REAL, ultima REAL, zomma REAL,
                    calculation_status TEXT NOT NULL,
                    error_message TEXT,
                    calculation_time_ms REAL
                );
            """)

            conn.commit()
            logging.info("Schema cleanup applied successfully.")

    except sqlite3.Error as e:
        logging.error(f"An error occurred during schema cleanup: {e}", exc_info=True)

if __name__ == "__main__":
    apply_cleanup() 