import logging
import functools
import time
import json
import datetime
from zoneinfo import ZoneInfo
import uuid  # Added import
import contextvars  # Added import

# Define the context variable here
log_uuid_var = contextvars.ContextVar('log_uuid', default=None)

NY_TZ = ZoneInfo("America/New_York")

class FunctionLogger:
    """
    A class-based decorator for logging function execution details.
    Generates/sets log_uuid in context if not already present.

    - Logs detailed start/executing/done messages to console at DEBUG level.
    - Logs a summary message (function name, timestamp, duration, log_uuid)
      at INFO level, formatted for the SQLiteHandler.
    """
    DB_LOG_PREFIX = "FUNC_EXEC_LOG:"

    def __init__(self, log_args=True, log_return=True):
        self.log_args = log_args
        self.log_return = log_return
        self.logger = None
        self.func_name = None

    def __call__(self, func):
        self.logger = logging.getLogger(func.__module__)
        self.func_name = func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # --- UUID Handling (FunctionLogger is responsible) ---
            existing_uuid = log_uuid_var.get()
            token = None
            uuid_generated_here = False # Keep track if this instance set the var
            if existing_uuid is None:
                # No UUID yet, generate one and set it for this context
                current_log_uuid = str(uuid.uuid4())
                token = log_uuid_var.set(current_log_uuid)
                uuid_generated_here = True
                # Optional: Log that a new UUID was generated
                # self.logger.debug(f"Generated new log_uuid: {current_log_uuid[:8]} for {self.func_name}")
            else:
                # UUID already set by an outer decorator (or nested call)
                current_log_uuid = existing_uuid
            uuid_short = current_log_uuid[:8] if current_log_uuid else "NO_UUID"
            # --- End UUID Handling ---

            start_time_perf = time.perf_counter()
            start_time_utc = datetime.datetime.now(datetime.timezone.utc)
            start_time_ny = start_time_utc.astimezone(NY_TZ)
            timestamp_str = start_time_ny.strftime('%m/%d/%y %H:%M')

            # --- Log Starting Message (DEBUG - Console) ---
            start_log_msg = f"Starting: {self.func_name} ({uuid_short})..."
            self.logger.debug(start_log_msg)

            # --- Log "What it's doing" (DEBUG - Console) ---
            args_repr = f"{args!r}" if self.log_args else "[ARGS HIDDEN]"
            kwargs_repr = f"{kwargs!r}" if self.log_args else "[KWARGS HIDDEN]"
            call_details_msg = f"Executing: {self.func_name}(args={args_repr}, kwargs={kwargs_repr}) ({uuid_short})"
            self.logger.debug(call_details_msg)

            # Outer try for finally block ensuring context reset
            try:
                try: # Inner try for function execution and exception logging
                    result = func(*args, **kwargs)
                    end_time_perf = time.perf_counter()
                    duration_s = end_time_perf - start_time_perf

                    # --- Log Done Message (DEBUG - Console) ---
                    done_log_msg = f"Done: {self.func_name} ({uuid_short})."
                    if self.log_return:
                        done_log_msg += f" Returned: {result!r}"
                    done_log_msg += f" Duration: {duration_s:.3f}s"
                    self.logger.debug(done_log_msg)

                    # --- Log Summary Message (INFO - For SQLite Handler) ---
                    if current_log_uuid: # Only log to DB if we have a UUID
                        db_log_data = {
                            "log_uuid": current_log_uuid, # Include the UUID
                            "name": self.func_name,
                            "timestamp": timestamp_str,
                            "duration_s": round(duration_s, 3)
                        }
                        db_log_msg = f"{self.DB_LOG_PREFIX}{json.dumps(db_log_data)}"
                        self.logger.info(db_log_msg)
                    else:
                        # This case should be rare now as we generate UUID here if needed
                        self.logger.warning(f"No log_uuid available for {self.func_name}, skipping DB log.")

                    return result

                except Exception as e:
                    end_time_perf = time.perf_counter()
                    duration_s = end_time_perf - start_time_perf
                    error_log_msg = f"Exception in {self.func_name} ({uuid_short}): {e!r}"
                    error_log_msg += f" (Occurred after {duration_s:.3f}s)"
                    # Log error with traceback info
                    self.logger.error(error_log_msg, exc_info=True)
                    # Note: We don't log FUNC_EXEC_LOG to DB on exception here.
                    raise # Re-raise the exception

            finally:
                # --- Reset Context Variable only if set in this wrapper ---
                if uuid_generated_here and token:
                    log_uuid_var.reset(token)
                    # Optional: Log the reset
                    # self.logger.debug(f"Reset log_uuid context for {self.func_name} ({uuid_short})")

        return wrapper