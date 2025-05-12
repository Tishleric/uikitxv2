# src/decorators/trace_time.py

import logging
import functools
import time
import json
import datetime
from zoneinfo import ZoneInfo
import uuid
import contextvars # Keep for general contextvar usage if needed elsewhere

# --- Import context vars from the new central file ---
from .context_vars import log_uuid_var, current_log_data
# ---

NY_TZ = ZoneInfo("America/New_York")

class TraceTime:
    # DB_LOG_PREFIX = "FUNC_EXEC_LOG:" # REMOVED - No longer emitting DB log directly

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
            current_log_uuid = log_uuid_var.get()
            uuid_short = current_log_uuid[:8] if current_log_uuid else "NO_UUID"
            data_dict = current_log_data.get()

            start_time_perf = time.perf_counter()
            start_time_utc = datetime.datetime.now(datetime.timezone.utc)
            start_time_ny = start_time_utc.astimezone(NY_TZ)
            timestamp_console_str = start_time_ny.strftime('%m/%d/%y %H:%M:%S')

            # --- Update Context ---
            if data_dict is not None:
                data_dict['function_name'] = self.func_name
                # Store the more precise timestamp internally if needed by TraceCloser
                data_dict['start_timestamp_iso'] = start_time_utc.isoformat()
            else:
                # Log warning if context is missing, as duration won't be stored
                self.logger.warning(f"TraceTime: Context data dictionary not found for {self.func_name} ({uuid_short}). Duration will not be added to context.")

            # --- Keep Console Logs ---
            start_log_msg = f"Starting: {self.func_name} ({uuid_short})..."
            self.logger.debug(start_log_msg)

            args_repr = f"{args!r}" if self.log_args else "[ARGS HIDDEN]"
            kwargs_repr = f"{kwargs!r}" if self.log_args else "[KWARGS HIDDEN]"
            call_details_msg = f"Executing: {self.func_name}(args={args_repr}, kwargs={kwargs_repr}) ({uuid_short})"
            self.logger.debug(call_details_msg)
            # --- End Console Logs ---

            try:
                result = func(*args, **kwargs)
                end_time_perf = time.perf_counter()
                duration_s = end_time_perf - start_time_perf

                # --- Update Context ---
                if data_dict is not None:
                    data_dict['duration_s'] = round(duration_s, 3)
                # --- End Context Update ---

                # --- Keep Console Logs ---
                done_log_msg = f"Done: {self.func_name} ({uuid_short})."
                if self.log_return:
                    res_repr = repr(result)
                    if len(res_repr) > 200:
                        res_repr = res_repr[:200] + '...'
                    done_log_msg += f" Returned: {res_repr}"
                done_log_msg += f" Duration: {duration_s:.3f}s"
                self.logger.debug(done_log_msg)
                # --- End Console Logs ---

                # --- REMOVED DB Log Emission Block ---
                # if current_log_uuid:
                #     db_log_data = { ... }
                #     db_log_msg = f"{self.DB_LOG_PREFIX}{json.dumps(db_log_data)}"
                #     self.logger.info(db_log_msg)
                # else:
                #     self.logger.warning(...)
                # --- End REMOVED Block ---

                return result

            except Exception as e:
                end_time_perf = time.perf_counter()
                duration_s = end_time_perf - start_time_perf

                # --- Update Context ---
                if data_dict is not None:
                    data_dict['error'] = str(e) # Add error info to context for TraceCloser
                    data_dict['duration_s'] = round(duration_s, 3) # Still record duration
                # --- End Context Update ---

                # --- Keep Console Logs (Error already logged by TraceCloser) ---
                # Error message is logged more informatively by TraceCloser's except block
                # We can keep a simple duration log here if desired, or remove it.
                # Let's keep it for now.
                error_duration_msg = f"Exception in {self.func_name} ({uuid_short}) occurred after {duration_s:.3f}s"
                self.logger.debug(error_duration_msg) # Log duration at DEBUG level on error
                # --- End Console Logs ---

                raise # Re-raise exception for TraceCloser to handle
        return wrapper 