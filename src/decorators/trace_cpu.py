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
            # Get log_uuid from context initially *only* for the start debug log
            initial_log_uuid = log_uuid_var.get()
            initial_uuid_short = initial_log_uuid[:8] if initial_log_uuid else "NO_UUID"

            cpu_start = None # Initialize cpu_start
            result = None # Initialize result
            try:
                # --- Get Starting CPU Usage --- (Uses initial_uuid_short)
                try:
                    cpu_start = psutil.cpu_percent(interval=0.01)
                    self.logger.debug(f"Start CPU {self.func_name} ({initial_uuid_short}): {cpu_start:.1f}%")
                except Exception as cpu_e:
                    self.logger.warning(f"Could not get start CPU usage for {self.func_name} ({initial_uuid_short}): {cpu_e}")

                # --- Execute the wrapped function (including inner decorators) ---
                # The context variable might be set/reset by inner decorators during this call
                result = func(*args, **kwargs)

            finally:
                # --- Get log_uuid FRESHLY from context before logging ---
                # This reads the value potentially set by TraceCloser/FunctionLogger,
                # before TraceCloser's finally block resets it.
                final_log_uuid = log_uuid_var.get()
                final_uuid_short = final_log_uuid[:8] if final_log_uuid else "NO_UUID"

                # --- Get Ending CPU Usage & Log Delta (if final UUID exists) ---
                if final_log_uuid: # Check the freshly retrieved UUID
                    try:
                        cpu_end = psutil.cpu_percent(interval=None)
                        # Use final_uuid_short for the end debug log for consistency
                        self.logger.debug(f"End CPU {self.func_name} ({final_uuid_short}): {cpu_end:.1f}%")

                        if cpu_start is not None:
                            cpu_delta = cpu_end - cpu_start
                            db_log_data = {
                                "log_uuid": final_log_uuid, # Use the final UUID for DB log
                                "cpu_delta": round(cpu_delta, 2)
                            }
                            db_log_msg = f"{self.DB_LOG_PREFIX}{json.dumps(db_log_data)}"
                            self.logger.info(db_log_msg) # Log to DB

                    except Exception as cpu_e:
                        self.logger.warning(f"Could not get end CPU usage or delta for {self.func_name} ({final_uuid_short}): {cpu_e}")
                else:
                    # This warning means TraceCloser likely wasn't used or failed
                    self.logger.warning(f"No final log_uuid found in context for {self.func_name}, skipping CPU DB log.")

            return result

        return wrapper