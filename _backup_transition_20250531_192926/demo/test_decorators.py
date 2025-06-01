# demo/test_decorators.py

import logging
import os
import sys
import atexit
import time
import random
import math

# --- Adjust Python path to find 'src' ---
# Get the directory containing the current script (demo/)
current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory (uikitxv2/)
project_root = os.path.dirname(current_dir)
# Add src directory to sys.path
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)
# --- End Path Adjustment ---

# --- Import lumberjack and decorators ---
try:
    # Import logging setup and shutdown functions
    from lumberjack.logging_config import setup_logging, shutdown_logging
    # Import the decorators
    from decorators.trace_closer import TraceCloser
    from decorators.trace_time import TraceTime
    from decorators.trace_cpu import TraceCpu
    from decorators.trace_memory import TraceMemory
    # Import context vars (optional, but shows they are available)
    from decorators.context_vars import log_uuid_var, current_log_data
except ImportError as e:
    # Use print here as logging might not be set up yet
    print(f"[Import Error] Failed to import necessary components: {e}", file=sys.stderr)
    print(f"[Import Error] Current sys.path: {sys.path}", file=sys.stderr)
    sys.exit(1) # Exit if essential imports fail
# --- End Imports ---

# --- Logging Configuration for Test Script ---
# Define the directory for log files relative to the project root
LOG_DB_DIR = os.path.join(project_root, 'logs')
# Define a *different* database file path for this test script
LOG_DB_PATH = os.path.join(LOG_DB_DIR, 'decorator_test_logs.db')
# Ensure the log directory exists
os.makedirs(LOG_DB_DIR, exist_ok=True)

# Setup logging: Console output at DEBUG level, Database logging at INFO level
# The root logger level is set to DEBUG to allow all messages through initially
console_handler, db_handler = setup_logging(
    db_path=LOG_DB_PATH,
    log_level_console=logging.DEBUG, # Show detailed logs in console
    log_level_db=logging.INFO,       # Only store INFO level (TraceCloser summaries) in DB
    log_level_main=logging.DEBUG     # Root logger allows DEBUG and above
)

# Register the shutdown_logging function to be called automatically on script exit
# This ensures database connections are closed properly.
atexit.register(shutdown_logging)
# --- End Logging Configuration ---

# --- Dummy Functions with Decorator Combinations ---

# Function 1: TraceCloser only
@TraceCloser()
def dummy_func_closer_only(duration=0.05):
    """Simple function with only TraceCloser."""
    logging.info("-> Inside dummy_func_closer_only")
    time.sleep(duration)
    return "Closer Only Done"

# Function 2: TraceCloser + TraceTime
@TraceCloser()
@TraceTime(log_args=True, log_return=True)
def dummy_func_logger(a, b, duration=0.06):
    """Function with TraceCloser and TraceTime."""
    logging.info("-> Inside dummy_func_logger")
    time.sleep(duration)
    return a + b

# Function 3: TraceCloser + TraceCpu
@TraceCloser()
@TraceCpu()
def dummy_func_cpu(iterations=10000, duration=0.07):
    """Function with TraceCloser and TraceCpu."""
    logging.info("-> Inside dummy_func_cpu")
    # Simulate some CPU work
    result = sum(math.sqrt(i) for i in range(iterations))
    time.sleep(duration)
    return f"CPU Done: {result:.2f}"

# Function 4: TraceCloser + TraceMemory
@TraceCloser()
@TraceMemory()
def dummy_func_memory(list_size=100000, duration=0.08):
    """Function with TraceCloser and TraceMemory."""
    logging.info("-> Inside dummy_func_memory")
    # Simulate memory allocation
    my_list = list(range(list_size))
    time.sleep(duration)
    return f"Memory Done: List length {len(my_list)}"

# Function 5: TraceCloser + TraceCpu + TraceTime
@TraceCloser()
@TraceCpu()
@TraceTime(log_args=False, log_return=False) # Hide args/return for brevity
def dummy_func_cpu_logger(iterations=15000, duration=0.09):
    """Function with TraceCloser, TraceCpu, and TraceTime."""
    logging.info("-> Inside dummy_func_cpu_logger")
    result = sum(math.sqrt(i) for i in range(iterations))
    time.sleep(duration)
    return "CPU + Logger Done"

# Function 6: TraceCloser + TraceMemory + TraceTime
@TraceCloser()
@TraceMemory()
@TraceTime(log_args=False, log_return=True)
def dummy_func_memory_logger(list_size=120000, duration=0.1):
    """Function with TraceCloser, TraceMemory, and TraceTime."""
    logging.info("-> Inside dummy_func_memory_logger")
    my_list = list(range(list_size))
    time.sleep(duration)
    return f"Memory + Logger Done: List length {len(my_list)}"

# Function 7: TraceCloser + TraceCpu + TraceMemory
@TraceCloser()
@TraceCpu()
@TraceMemory()
def dummy_func_cpu_memory(iterations=5000, list_size=50000, duration=0.11):
    """Function with TraceCloser, TraceCpu, and TraceMemory."""
    logging.info("-> Inside dummy_func_cpu_memory")
    result = sum(math.sqrt(i) for i in range(iterations))
    my_list = list(range(list_size))
    time.sleep(duration)
    return f"CPU + Memory Done: Sum={result:.2f}, List={len(my_list)}"

# Function 8: Full Stack - TraceCloser + TraceCpu + TraceMemory + TraceTime
@TraceCloser()
@TraceCpu()
@TraceMemory()
@TraceTime(log_args=True, log_return=True)
def dummy_func_full_stack(x, text="test", iterations=8000, list_size=80000, duration=0.12):
    """Function with all decorators applied."""
    logging.info("-> Inside dummy_func_full_stack")
    result = sum(math.sqrt(i) for i in range(iterations))
    my_list = list(range(list_size))
    time.sleep(duration)
    return f"Full Stack Done: x={x}, text='{text}', Sum={result:.2f}, List={len(my_list)}"

# Function 9: Error Case
@TraceCloser()
@TraceCpu()
@TraceMemory()
@TraceTime(log_args=True, log_return=True)
def dummy_func_error(divisor=0):
    """Function designed to raise an error."""
    logging.info("-> Inside dummy_func_error")
    time.sleep(0.05)
    result = 10 / divisor # This will raise ZeroDivisionError
    return result


# --- Main Execution Logic ---
if __name__ == "__main__":
    main_logger = logging.getLogger(__name__)
    main_logger.info("--- Starting Decorator Combination Test ---")

    print("\n[1] Testing @TraceCloser only...")
    dummy_func_closer_only()

    print("\n[2] Testing @TraceCloser + @TraceTime...")
    dummy_func_logger(5, 10)

    print("\n[3] Testing @TraceCloser + @TraceCpu...")
    dummy_func_cpu()

    print("\n[4] Testing @TraceCloser + @TraceMemory...")
    dummy_func_memory()

    print("\n[5] Testing @TraceCloser + @TraceCpu + @TraceTime...")
    dummy_func_cpu_logger()

    print("\n[6] Testing @TraceCloser + @TraceMemory + @TraceTime...")
    dummy_func_memory_logger()

    print("\n[7] Testing @TraceCloser + @TraceCpu + @TraceMemory...")
    dummy_func_cpu_memory()

    print("\n[8] Testing Full Stack (@TraceCloser + @TraceCpu + @TraceMemory + @TraceTime)...")
    dummy_func_full_stack(99, text="hello")

    print("\n[9] Testing Error Case (Full Stack)...")
    try:
        dummy_func_error(divisor=0)
    except ZeroDivisionError:
        main_logger.info("Successfully caught expected ZeroDivisionError from dummy_func_error.")
    except Exception as e:
        main_logger.error(f"Caught unexpected error from dummy_func_error: {e}", exc_info=True)


    main_logger.info("--- Decorator Combination Test Finished ---")

    # Explicitly call shutdown here for clarity, although atexit handles it too
    logging.shutdown()
    # Attempt to unregister atexit handler if it exists (best effort)
    if shutdown_logging in getattr(atexit, '_exithandlers', []):
         try: atexit.unregister(shutdown_logging)
         except Exception as e: main_logger.warning(f"Could not unregister atexit handler: {e}")
