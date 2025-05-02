import logging
import functools
import time
import json
import psutil

# --- Import context vars from the new central file ---
from .context_vars import log_uuid_var, current_log_data
# ---

class TraceCpu:
    DB_LOG_PREFIX = "CPU_TRACE_LOG:"

    def __init__(self):
        self.logger = None
        self.func_name = None

    def __call__(self, func):
        self.logger = logging.getLogger(func.__module__)
        self.func_name = func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            initial_log_uuid = log_uuid_var.get()
            initial_uuid_short = initial_log_uuid[:8] if initial_log_uuid else "NO_UUID"
            data_dict = current_log_data.get()

            cpu_start = None
            result = None
            cpu_delta = None

            try:
                try:
                    cpu_start = psutil.cpu_percent(interval=0.01)
                    self.logger.debug(f"Start CPU {self.func_name} ({initial_uuid_short}): {cpu_start:.1f}%")
                except Exception as cpu_e:
                    self.logger.warning(f"Could not get start CPU usage for {self.func_name} ({initial_uuid_short}): {cpu_e}")

                result = func(*args, **kwargs)

            finally:
                final_log_uuid = log_uuid_var.get()
                final_uuid_short = final_log_uuid[:8] if final_log_uuid else "NO_UUID"

                if final_log_uuid:
                    try:
                        cpu_end = psutil.cpu_percent(interval=None)
                        self.logger.debug(f"End CPU {self.func_name} ({final_uuid_short}): {cpu_end:.1f}%")

                        if cpu_start is not None:
                            cpu_delta = cpu_end - cpu_start
                            db_log_data = {
                                "log_uuid": final_log_uuid,
                                "cpu_delta": round(cpu_delta, 2)
                            }
                            db_log_msg = f"{self.DB_LOG_PREFIX}{json.dumps(db_log_data)}"
                            self.logger.info(db_log_msg)

                            if data_dict is not None:
                                data_dict['cpu_delta'] = round(cpu_delta, 2)

                    except Exception as cpu_e:
                        self.logger.warning(f"Could not get end CPU usage or delta for {self.func_name} ({final_uuid_short}): {cpu_e}")
                else:
                    self.logger.warning(f"No final log_uuid found in context for {self.func_name}, skipping CPU DB log.")

            return result
        return wrapper
