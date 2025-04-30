import logging
import functools
import time
import json
import psutil # Import psutil
# Removed uuid import - no longer needed here
# Removed contextvars import - no longer needed here
import os

# Import log_uuid_var from logger_decorator in the same package level
from .logger_decorator import log_uuid_var

# Get current process handle once
try:
    CURRENT_PROCESS = psutil.Process(os.getpid())
except psutil.NoSuchProcess:
    CURRENT_PROCESS = None # Handle case where process might not exist (unlikely here)

class TraceMemory:
    """
    A class-based decorator for logging function memory usage (RSS delta).
    Reads the log_uuid from context set by an outer decorator (e.g., FunctionLogger).

    - Logs start and end memory usage (RSS) to console at DEBUG level.
    - Logs the memory usage delta (RSS in MB) via a specific INFO message,
      including the log_uuid, but only if a log_uuid is found in the context.
    """
    DB_LOG_PREFIX = "MEMORY_TRACE_LOG:"
    BYTES_TO_MB = 1 / (1024 * 1024) # Conversion factor

    def __init__(self):
        self.logger = None
        self.func_name = None

    def __call__(self, func):
        self.logger = logging.getLogger(func.__module__)
        self.func_name = func.__name__

        @functools.wraps(func) # Preserve metadata
        def wrapper(*args, **kwargs):
            """The wrapper function that replaces the original function."""
            if CURRENT_PROCESS is None: # Skip if process handle couldn't be obtained
                 self.logger.warning("Could not get process handle, skipping memory trace.")
                 return func(*args, **kwargs)

            # Get log_uuid from context (should be set by FunctionLogger)
            current_log_uuid = log_uuid_var.get()
            uuid_short = current_log_uuid[:8] if current_log_uuid else "NO_UUID"

            mem_start_rss_mb = None # Initialize start memory
            try:
                # --- Get Starting Memory Usage ---
                try:
                    mem_info_start = CURRENT_PROCESS.memory_info()
                    mem_start_rss_mb = mem_info_start.rss * self.BYTES_TO_MB
                    self.logger.debug(f"Start Memory RSS {self.func_name} ({uuid_short}): {mem_start_rss_mb:.2f} MB")
                except Exception as mem_e:
                    self.logger.warning(f"Could not get start memory usage for {self.func_name} ({uuid_short}): {mem_e}")

                # --- Execute the wrapped function ---
                result = func(*args, **kwargs) # Call the wrapped function

            finally:
                # --- Get Ending Memory Usage & Log Delta (if UUID exists) ---
                if current_log_uuid: # Check if UUID was set by FunctionLogger
                    try:
                        mem_info_end = CURRENT_PROCESS.memory_info()
                        mem_end_rss_mb = mem_info_end.rss * self.BYTES_TO_MB
                        self.logger.debug(f"End Memory RSS {self.func_name} ({uuid_short}): {mem_end_rss_mb:.2f} MB")

                        if mem_start_rss_mb is not None:
                            mem_delta_mb = mem_end_rss_mb - mem_start_rss_mb
                            db_log_data = {
                                "log_uuid": current_log_uuid, # Include the UUID
                                "memory_delta_mb": round(mem_delta_mb, 3) # Round to 3 decimal places
                            }
                            db_log_msg = f"{self.DB_LOG_PREFIX}{json.dumps(db_log_data)}"
                            self.logger.info(db_log_msg) # Log to DB

                    except Exception as mem_e:
                        self.logger.warning(f"Could not get end memory usage or delta for {self.func_name} ({uuid_short}): {mem_e}")
                else:
                    # Log a warning if no UUID was found
                    self.logger.warning(f"No log_uuid found in context for {self.func_name}, skipping Memory DB log.")

                # --- Reset logic removed ---

            return result

        return wrapper