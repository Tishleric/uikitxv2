# demo/run_queries_demo.py

import logging # Keep logging import for setup
import os
import sys
import atexit

# --- Adjust Python path to find 'src' ---
# Ensures the script can find lumberjack etc.
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    # Path adjustment logging removed
    sys.path.insert(0, src_path)
# --- End Path Adjustment ---

# --- Import Logging Setup ---
try:
    from lumberjack.logging_config import setup_logging, shutdown_logging
except ImportError as e:
    # Use print here as logging setup itself failed
    print(f"[Import Error in run_queries_demo] Failed to import logging setup: {e}", file=sys.stderr)
    sys.exit(1)
# --- End Imports ---

# --- Import Query Functions ---
# Import after path adjustment and logging setup potentially
try:
    import query_runner # Import the module containing decorated functions
except ImportError as e:
     # Use print here as logging might not be fully set up
     print(f"[Import Error] Could not import query_runner: {e}", file=sys.stderr)
     sys.exit(1)
except Exception as e:
     # Catch other potential errors during query_runner import (like YAML load failure or DB setup)
     # Use print here as logging might not be fully set up
     print(f"[Error] Failed during import of query_runner: {e}", file=sys.stderr)
     sys.exit(1)
# --- End Query Function Import ---


# --- Logging Configuration for Demo ---
LOG_DB_DIR = os.path.join(project_root, 'logs')
# Use a specific database for this demo run
LOG_DB_PATH = os.path.join(LOG_DB_DIR, 'query_timing_logs.db')
os.makedirs(LOG_DB_DIR, exist_ok=True)

# Setup logging: Console DEBUG, Database INFO
# This setup is still needed for the decorators to log correctly
console_handler, db_handler = setup_logging(
    db_path=LOG_DB_PATH,
    log_level_console=logging.DEBUG,
    log_level_db=logging.INFO,
    log_level_main=logging.DEBUG
)
atexit.register(shutdown_logging)
# --- End Logging Configuration ---


# --- Main Execution Logic ---
if __name__ == "__main__":
    # --- main_logger removed ---
    # main_logger = logging.getLogger(__name__)
    # main_logger.info("--- Starting Query Timing Demo ---") # Removed

    # --- Call Decorated Query Functions ---
    # The decorators will log the start/end/details of these calls

    # Step indication logging removed
    user1 = query_runner.get_user_by_id(1)
    # Result logging removed (decorator handles it at DEBUG if enabled)

    # Step indication logging removed
    user99 = query_runner.get_user_by_id(99)
    # Result logging removed

    # Step indication logging removed
    rows_affected = query_runner.update_order_status("Processing", 1)
    # Result logging removed

    # Step indication logging removed
    active_sessions = query_runner.get_active_sessions()
    # Result logging removed

    # Step indication logging removed
    try:
        query_runner.get_non_existent_data(123)
    except Exception as e:
        # Error is logged by TraceCloser. No need for manual logging here.
        # We know the call was made, and the logs will show the failure.
        pass # Simply catch the expected exception to allow script to continue

    # --- End Function Calls ---

    # Script end logging removed
    # main_logger.info("--- Query Timing Demo Finished ---")

    # Explicitly call shutdown here for clarity
    # Note: atexit will also call it, but calling it here ensures
    # logs are flushed before the script potentially exits immediately.
    logging.shutdown()
    # Attempt to unregister atexit handler if it exists (best effort)
    # Warning logging removed from here
    if shutdown_logging in getattr(atexit, '_exithandlers', []):
         try: atexit.unregister(shutdown_logging)
         except Exception: pass # Ignore errors during unregister

