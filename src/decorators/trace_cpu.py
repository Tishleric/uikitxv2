import logging
import functools
import time
import json
import psutil # Import psutil
# Removed uuid import - no longer needed here
# Removed contextvars import - no longer needed here

# Import log_uuid_var from logger_decorator in the same package level
from .logger_decorator import log_uuid_var

class TraceCpu:
    """
    A class-based decorator for logging function CPU usage.
    Reads the log_uuid from context set by an outer decorator (e.g., FunctionLogger).

    - Logs start and end CPU usage to console at DEBUG level.
    - Logs the CPU usage delta via a specific INFO message, including the log_uuid,
      but only if a log_uuid is found in the context.
    """
    DB_LOG_PREFIX = "CPU_TRACE_LOG:"

    def __init__(self):
        self.logger = None
        self.func_name = None

    def __call__(self, func):
        self.logger = logging.getLogger(func.__module__)
        self.func_name = func.__name__

        @functools.wraps(func) # Preserve metadata
        def wrapper(*args, **kwargs):
            """The wrapper function that replaces the original function."""
            # Get log_uuid from context (should be set by FunctionLogger)
            current_log_uuid = log_uuid_var.get()
            uuid_short = current_log_uuid[:8] if current_log_uuid else "NO_UUID"

            cpu_start = None # Initialize cpu_start
            try:
                # --- Get Starting CPU Usage ---
                try:
                    cpu_start = psutil.cpu_percent(interval=0.01)
                    self.logger.debug(f"Start CPU {self.func_name} ({uuid_short}): {cpu_start:.1f}%")
                except Exception as cpu_e:
                    self.logger.warning(f"Could not get start CPU usage for {self.func_name} ({uuid_short}): {cpu_e}")

                # --- Execute the wrapped function ---
                result = func(*args, **kwargs) # Call the wrapped function

            finally:
                # --- Get Ending CPU Usage & Log Delta (if UUID exists) ---
                if current_log_uuid: # Check if UUID was set by FunctionLogger
                    try:
                        cpu_end = psutil.cpu_percent(interval=None)
                        self.logger.debug(f"End CPU {self.func_name} ({uuid_short}): {cpu_end:.1f}%")

                        if cpu_start is not None:
                            cpu_delta = cpu_end - cpu_start
                            db_log_data = {
                                "log_uuid": current_log_uuid, # Include the UUID
                                "cpu_delta": round(cpu_delta, 2)
                            }
                            db_log_msg = f"{self.DB_LOG_PREFIX}{json.dumps(db_log_data)}"
                            self.logger.info(db_log_msg) # Log to DB

                    except Exception as cpu_e:
                        self.logger.warning(f"Could not get end CPU usage or delta for {self.func_name} ({uuid_short}): {cpu_e}")
                else:
                    # Log a warning if no UUID was found (FunctionLogger likely not used/outer)
                    self.logger.warning(f"No log_uuid found in context for {self.func_name}, skipping CPU DB log.")

                # --- Reset logic removed ---

            return result

        return wrapper