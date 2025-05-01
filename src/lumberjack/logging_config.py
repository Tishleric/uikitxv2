import logging
import sys
import os
# Use relative import for sqlite_handler assuming it's in the same directory
from .sqlite_handler import SQLiteHandler

# Store handlers globally within this module to facilitate cleanup if needed,
# although returning them from setup_logging is often cleaner.
_db_handler = None
_console_handler = None

def setup_logging(
    log_level_main=logging.DEBUG,
    log_level_console=logging.DEBUG,
    log_level_db=logging.INFO,
    db_path='logs/function_exec.db', # Default path
    console_format='%(asctime)s - %(levelname)-8s - %(name)s - %(funcName)s - %(message)s',
    date_format='%Y-%m-%d %H:%M:%S'
):
    """
    Configures logging with a console handler and an SQLite handler.

    Args:
        log_level_main: The minimum level for the root logger.
        log_level_console: The minimum level for console output.
        log_level_db: The minimum level for database logging.
        db_path: Path to the SQLite database file. Directory will be created if needed.
        console_format: Format string for console messages.
        date_format: Date format string for console messages.

    Returns:
        tuple: A tuple containing the configured console_handler and db_handler,
               which might be needed for explicit closing later.
               Returns (None, None) if setup fails.
    """
    global _db_handler, _console_handler

    try:
        # 1. Get the root logger
        logger = logging.getLogger()
        logger.setLevel(log_level_main)

        # Clear existing handlers to avoid duplicates if called multiple times
        if logger.hasHandlers():
            logger.handlers.clear()

        # 2. Create Console Handler
        _console_handler = logging.StreamHandler(sys.stdout)
        _console_handler.setLevel(log_level_console)

        # 3. Create Formatter for Console
        console_formatter = logging.Formatter(console_format, datefmt=date_format)
        _console_handler.setFormatter(console_formatter)

        # 4. Create SQLite Handler
        # Ensure the directory for the db exists
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir, exist_ok=True) # Use exist_ok=True
                print(f"Created log directory: {db_dir}")
            except OSError as e:
                print(f"Error creating log directory {db_dir}: {e}")
                # For now, we proceed, SQLiteHandler handles connection errors

        _db_handler = SQLiteHandler(db_filename=db_path)
        _db_handler.setLevel(log_level_db)

        # 5. Add Handlers to the Logger
        logger.addHandler(_console_handler)
        logger.addHandler(_db_handler)

        logger.info("Logging setup complete.") # Log confirmation
        return _console_handler, _db_handler # Return handlers

    except Exception as e:
        print(f"Error during logging setup: {e}")
        # Fallback to basic console logging if setup fails
        logging.basicConfig(level=logging.WARNING, format='%(levelname)s:%(message)s')
        logging.error("Logging setup failed, using basicConfig fallback.")
        return None, None

def shutdown_logging():
    """Safely closes logging handlers, especially the database handler."""
    global _db_handler
    print("Shutting down logging...")
    if _db_handler:
        try:
            _db_handler.close()
            print("Database handler closed.")
        except Exception as e:
            print(f"Error closing database handler: {e}")
    # Optional: Call logging.shutdown() if you want to shut down everything
    # logging.shutdown()

# Example of how to use (keep commented out):
# if __name__ == '__main__':
#     ch, dbh = setup_logging(db_path='../logs/example_run.db') # Example: specify path relative to caller
#     logging.getLogger().info("This is a test info.")
#     logging.getLogger('__main__').debug("This is a test debug from main.")
#     shutdown_logging() 