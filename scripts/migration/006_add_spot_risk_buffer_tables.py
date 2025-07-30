
import sqlite3
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define database path
DB_PATH = Path(__file__).parent.parent.parent / "data" / "output" / "spot_risk" / "spot_risk.db"

def apply_migration():
    """
    Applies the schema migration to introduce double-buffer tables for spot risk Greeks.
    - Renames 'spot_risk_calculated' to 'greeks_live_A'.
    - Creates 'greeks_live_B' as a copy.
    - Creates 'active_view_pointer' to manage the active table.
    - Removes the old 'latest_calculations' view.
    """
    if not DB_PATH.exists():
        logging.error(f"Database not found at {DB_PATH}. Please run the watcher to create it first.")
        return

    logging.info(f"Connecting to database at {DB_PATH}")
    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            cursor = conn.cursor()

            # --- Step 1: Drop the old view if it exists ---
            logging.info("Dropping old 'latest_calculations' view...")
            cursor.execute("DROP VIEW IF EXISTS latest_calculations;")

            # --- Step 2: Rename the existing table to 'greeks_live_A' ---
            logging.info("Renaming 'spot_risk_calculated' to 'greeks_live_A'...")
            try:
                # Check if the table exists before renaming
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spot_risk_calculated';")
                if cursor.fetchone():
                    cursor.execute("ALTER TABLE spot_risk_calculated RENAME TO greeks_live_A;")
                else:
                    # If 'spot_risk_calculated' doesn't exist, create 'greeks_live_A' from scratch
                    logging.info("'spot_risk_calculated' not found, creating 'greeks_live_A' directly.")
                    cursor.execute("""
                        CREATE TABLE greeks_live_A (
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
            except sqlite3.OperationalError as e:
                logging.warning(f"Could not rename table (perhaps it was already renamed?): {e}")


            # --- Step 3: Create 'greeks_live_B' with the same schema ---
            logging.info("Creating 'greeks_live_B' table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS greeks_live_B (
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

            # --- Step 4: Create and populate the view pointer table ---
            logging.info("Creating and initializing 'active_view_pointer' table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS active_view_pointer (
                    id INTEGER PRIMARY KEY,
                    active_view TEXT NOT NULL
                );
            """)
            cursor.execute("INSERT OR IGNORE INTO active_view_pointer (id, active_view) VALUES (1, 'A');")

            conn.commit()
            logging.info("Migration applied successfully.")

    except sqlite3.Error as e:
        logging.error(f"An error occurred during migration: {e}", exc_info=True)

if __name__ == "__main__":
    apply_migration()