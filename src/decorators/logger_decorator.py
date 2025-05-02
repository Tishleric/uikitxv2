# src/decorators/logger_decorator.py

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

class FunctionLogger:
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
            current_log_uuid = log_uuid_var.get()
            uuid_short = current_log_uuid[:8] if current_log_uuid else "NO_UUID"
            data_dict = current_log_data.get()

            start_time_perf = time.perf_counter()
            start_time_utc = datetime.datetime.now(datetime.timezone.utc)
            start_time_ny = start_time_utc.astimezone(NY_TZ)
            # --- Updated timestamp format for DB log ---
            timestamp_db_str = start_time_ny.strftime('%m/%d/%y %H:%M:%S')
            # Keep console format separate if needed, or use the same
            timestamp_console_str = start_time_ny.strftime('%m/%d/%y %H:%M:%S') # Using same format for console DEBUG logs for consistency

            if data_dict is not None:
                data_dict['function_name'] = self.func_name
                # Store the more precise timestamp internally if needed, but use formatted one for DB log
                data_dict['start_timestamp_iso'] = start_time_utc.isoformat()

            start_log_msg = f"Starting: {self.func_name} ({uuid_short})..."
            self.logger.debug(start_log_msg)

            args_repr = f"{args!r}" if self.log_args else "[ARGS HIDDEN]"
            kwargs_repr = f"{kwargs!r}" if self.log_args else "[KWARGS HIDDEN]"
            call_details_msg = f"Executing: {self.func_name}(args={args_repr}, kwargs={kwargs_repr}) ({uuid_short})"
            self.logger.debug(call_details_msg)

            try:
                result = func(*args, **kwargs)
                end_time_perf = time.perf_counter()
                duration_s = end_time_perf - start_time_perf

                if data_dict is not None:
                    data_dict['duration_s'] = round(duration_s, 3)

                done_log_msg = f"Done: {self.func_name} ({uuid_short})."
                if self.log_return:
                    res_repr = repr(result)
                    if len(res_repr) > 200:
                        res_repr = res_repr[:200] + '...'
                    done_log_msg += f" Returned: {res_repr}"
                done_log_msg += f" Duration: {duration_s:.3f}s"
                self.logger.debug(done_log_msg)

                if current_log_uuid:
                    db_log_data = {
                        "log_uuid": current_log_uuid,
                        "name": self.func_name,
                        "timestamp": timestamp_db_str, # Use the updated format
                        "duration_s": round(duration_s, 3)
                    }
                    db_log_msg = f"{self.DB_LOG_PREFIX}{json.dumps(db_log_data)}"
                    self.logger.info(db_log_msg)
                else:
                    self.logger.warning(f"No log_uuid found in context for {self.func_name}, skipping DB log.")

                return result

            except Exception as e:
                end_time_perf = time.perf_counter()
                duration_s = end_time_perf - start_time_perf

                if data_dict is not None:
                    data_dict['error'] = str(e)
                    data_dict['duration_s'] = round(duration_s, 3)

                error_log_msg = f"Exception in {self.func_name} ({uuid_short}): {e!r}"
                error_log_msg += f" (Occurred after {duration_s:.3f}s)"
                self.logger.error(error_log_msg, exc_info=True)

                raise
        return wrapper
