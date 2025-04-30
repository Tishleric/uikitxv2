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

            # Get log_uuid from context initially *only* for the start debug log
            initial_log_uuid = log_uuid_var.get()
            initial_uuid_short = initial_log_uuid[:8] if initial_log_uuid else "NO_UUID"

            mem_start_rss_mb = None # Initialize start memory
            result = None # Initialize result
            try:
                # --- Get Starting Memory Usage --- (Uses initial_uuid_short)
                try:
                    mem_info_start = CURRENT_PROCESS.memory_info()
                    mem_start_rss_mb = mem_info_start.rss * self.BYTES_TO_MB
                    self.logger.debug(f"Start Memory RSS {self.func_name} ({initial_uuid_short}): {mem_start_rss_mb:.2f} MB")
                except Exception as mem_e:
                    self.logger.warning(f"Could not get start memory usage for {self.func_name} ({initial_uuid_short}): {mem_e}")

                # --- Execute the wrapped function (including inner decorators) ---
                # The context variable might be set/reset by inner decorators during this call
                result = func(*args, **kwargs)

            finally:
                # --- Get log_uuid FRESHLY from context before logging ---
                # This reads the value potentially set by TraceCloser/FunctionLogger,
                # before TraceCloser's finally block resets it.
                final_log_uuid = log_uuid_var.get()
                final_uuid_short = final_log_uuid[:8] if final_log_uuid else "NO_UUID"

                # --- Get Ending Memory Usage & Log Delta (if final UUID exists) ---
                if final_log_uuid: # Check the freshly retrieved UUID
                    try:
                        mem_info_end = CURRENT_PROCESS.memory_info()
                        mem_end_rss_mb = mem_info_end.rss * self.BYTES_TO_MB
                        # Use final_uuid_short for the end debug log for consistency
                        self.logger.debug(f"End Memory RSS {self.func_name} ({final_uuid_short}): {mem_end_rss_mb:.2f} MB")

                        if mem_start_rss_mb is not None:
                            mem_delta_mb = mem_end_rss_mb - mem_start_rss_mb
                            db_log_data = {
                                "log_uuid": final_log_uuid, # Use the final UUID for DB log
                                "memory_delta_mb": round(mem_delta_mb, 3) # Round to 3 decimal places
                            }
                            db_log_msg = f"{self.DB_LOG_PREFIX}{json.dumps(db_log_data)}"
                            self.logger.info(db_log_msg) # Log to DB

                    except Exception as mem_e:
                        self.logger.warning(f"Could not get end memory usage or delta for {self.func_name} ({final_uuid_short}): {mem_e}")
                else:
                     # This warning means TraceCloser likely wasn't used or failed
                    self.logger.warning(f"No final log_uuid found in context for {self.func_name}, skipping Memory DB log.")

            return result

        return wrapper