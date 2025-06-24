#!/usr/bin/env python3

# src/lumberjack/logging_config.py

import logging
import sys
import os
from pathlib import Path
# Use relative import for sqlite_handler assuming it's in the same directory
from .handlers import SQLiteHandler
# Import monitor decorator from parent monitoring module
from ..decorators import monitor

# Store handlers globally within this module to facilitate cleanup if needed,
# although returning them from setup_logging is often cleaner.
_db_handler = None
_console_handler = None

# Get a logger specifically for this module's operations
config_logger = logging.getLogger(__name__)
# --- Ensure config_logger has a level set early ---
config_logger.setLevel(logging.DEBUG) # Set level here to capture all setup messages

@monitor()
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
               Returns (None, None) if setup fails completely.
    """
    global _db_handler, _console_handler

    # Use a basic temporary configuration for logging errors during setup itself
    temp_formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
    # --- Ensure temp_handler exists and is added only once ---
    # Check if our specific temp_handler is already present
    temp_handler_exists = any(
        isinstance(h, logging.StreamHandler) and h.stream == sys.stderr
        for h in config_logger.handlers
    )

    temp_handler = None
    if not temp_handler_exists:
        temp_handler = logging.StreamHandler(sys.stderr) # Log setup errors to stderr
        temp_handler.setFormatter(temp_formatter)
        # --- Set level on temp_handler too ---
        temp_handler.setLevel(logging.DEBUG) # Capture DEBUG messages from config_logger too
        config_logger.addHandler(temp_handler)
        # config_logger already has level set outside the function

    console_h = None
    db_h = None

    try:
        # 1. Get the root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level_main)

        # Clear existing handlers from the root logger to avoid duplicates
        # Important: Do this *before* potentially failing steps
        if root_logger.hasHandlers():
             # Make a copy before clearing, as clearing might affect iteration
             for handler in root_logger.handlers[:]:
                  # Optionally close handlers before removing if they have a close method
                  if hasattr(handler, 'close'):
                       try:
                           handler.close()
                       except Exception:
                            pass # Ignore errors during cleanup closing
                  root_logger.removeHandler(handler)

        # 2. Ensure the directory for the db exists
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir, exist_ok=True) # Use exist_ok=True
                config_logger.debug(f"Created log directory: {db_dir}")
            except OSError as e:
                # --- Use logging instead of print ---
                config_logger.error(f"Error creating log directory {db_dir}: {e}", exc_info=False)
                # Continue, SQLiteHandler might still work or handle its own error

        # 3. Create Console Handler
        console_h = logging.StreamHandler(sys.stdout)
        console_h.setLevel(log_level_console)

        # 4. Create Formatter for Console
        console_formatter = logging.Formatter(console_format, datefmt=date_format)
        console_h.setFormatter(console_formatter)

        # 5. Create SQLite Handler
        db_h = SQLiteHandler(db_filename=db_path)
        db_h.setLevel(log_level_db)

        # 6. Add Handlers to the Root Logger
        root_logger.addHandler(console_h)
        root_logger.addHandler(db_h)

        # Store references globally *after* successful creation
        _console_handler = console_h
        _db_handler = db_h

        config_logger.info("Logging setup complete.") # Log confirmation via module logger

    except Exception as e:
        config_logger.critical(f"Critical error during logging setup: {e}", exc_info=True)
        # Fallback to basic console logging if setup fails critically
        # Ensure root logger handlers are cleared before basicConfig
        logging.getLogger().handlers.clear()
        logging.basicConfig(level=logging.WARNING, format='%(levelname)s:%(name)s:%(message)s')
        logging.error("Logging setup failed, using basicConfig fallback.")
        # Return None for handlers if setup failed
        return None, None
    finally:
        # Remove the temporary handler used for setup logging *if we added it*
        if temp_handler and temp_handler in config_logger.handlers:
             config_logger.removeHandler(temp_handler)

    return console_h, db_h # Return successfully created handlers

@monitor()
def shutdown_logging():
    """Safely closes logging handlers, especially the database handler."""
    global _db_handler, _console_handler # Include console handler for completeness if needed
    # --- Check if config_logger has handlers before logging shutdown message ---
    if config_logger.hasHandlers():
        config_logger.info("Shutting down logging...") # Use module logger
    else:
        # If no handlers, print as a fallback
        print("Shutting down logging (config_logger has no handlers)...")


    # Close DB Handler
    if _db_handler:
        try:
            _db_handler.close()
            if config_logger.hasHandlers():
                 config_logger.debug("Database handler closed.")
            else:
                 print("Database handler closed.")
            _db_handler = None # Clear reference
        except Exception as e:
            if config_logger.hasHandlers():
                 config_logger.error(f"Error closing database handler: {e}", exc_info=True)
            else:
                 print(f"ERROR: Error closing database handler: {e}")

    # Close Console Handler (optional, usually not necessary for StreamHandler)
    if _console_handler:
         try:
             # StreamHandlers don't typically need closing unless the stream does
             if hasattr(_console_handler, 'close'):
                  _console_handler.close()
                  if config_logger.hasHandlers():
                       config_logger.debug("Console handler closed.")
                  else:
                       print("Console handler closed.")
             _console_handler = None # Clear reference
         except Exception as e:
             if config_logger.hasHandlers():
                  config_logger.error(f"Error closing console handler: {e}", exc_info=True)
             else:
                  print(f"ERROR: Error closing console handler: {e}")

    # Optional: Call logging.shutdown() if you want to shut down everything forcefully
    # logging.shutdown()

# Example of how to use (keep commented out):
# if __name__ == '__main__':
#     ch, dbh = setup_logging(db_path='../logs/example_run.db') # Example: specify path relative to caller
#     logging.getLogger().info("This is a test info.")
#     logging.getLogger('__main__').debug("This is a test debug from main.")
#     shutdown_logging()
