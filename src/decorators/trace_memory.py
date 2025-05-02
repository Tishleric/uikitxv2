import logging
import functools
import time
import json
import psutil
import os

# --- Import context vars from the new central file ---
from .context_vars import log_uuid_var, current_log_data
# ---

try:
    CURRENT_PROCESS = psutil.Process(os.getpid())
except psutil.NoSuchProcess:
    CURRENT_PROCESS = None

class TraceMemory:
    DB_LOG_PREFIX = "MEMORY_TRACE_LOG:"
    BYTES_TO_MB = 1 / (1024 * 1024)

    def __init__(self):
        self.logger = None
        self.func_name = None

    def __call__(self, func):
        self.logger = logging.getLogger(func.__module__)
        self.func_name = func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if CURRENT_PROCESS is None:
                 self.logger.warning("Could not get process handle, skipping memory trace.")
                 return func(*args, **kwargs)

            initial_log_uuid = log_uuid_var.get()
            initial_uuid_short = initial_log_uuid[:8] if initial_log_uuid else "NO_UUID"
            data_dict = current_log_data.get()

            mem_start_rss_mb = None
            result = None
            mem_delta_mb = None

            try:
                try:
                    mem_info_start = CURRENT_PROCESS.memory_info()
                    mem_start_rss_mb = mem_info_start.rss * self.BYTES_TO_MB
                    self.logger.debug(f"Start Memory RSS {self.func_name} ({initial_uuid_short}): {mem_start_rss_mb:.2f} MB")
                except Exception as mem_e:
                    self.logger.warning(f"Could not get start memory usage for {self.func_name} ({initial_uuid_short}): {mem_e}")

                result = func(*args, **kwargs)

            finally:
                final_log_uuid = log_uuid_var.get()
                final_uuid_short = final_log_uuid[:8] if final_log_uuid else "NO_UUID"

                if final_log_uuid:
                    try:
                        mem_info_end = CURRENT_PROCESS.memory_info()
                        mem_end_rss_mb = mem_info_end.rss * self.BYTES_TO_MB
                        self.logger.debug(f"End Memory RSS {self.func_name} ({final_uuid_short}): {mem_end_rss_mb:.2f} MB")

                        if mem_start_rss_mb is not None:
                            mem_delta_mb = mem_end_rss_mb - mem_start_rss_mb
                            db_log_data = {
                                "log_uuid": final_log_uuid,
                                "memory_delta_mb": round(mem_delta_mb, 3)
                            }
                            db_log_msg = f"{self.DB_LOG_PREFIX}{json.dumps(db_log_data)}"
                            self.logger.info(db_log_msg)

                            if data_dict is not None:
                                data_dict['memory_delta_mb'] = round(mem_delta_mb, 3)

                    except Exception as mem_e:
                        self.logger.warning(f"Could not get end memory usage or delta for {self.func_name} ({final_uuid_short}): {mem_e}")
                else:
                    self.logger.warning(f"No final log_uuid found in context for {self.func_name}, skipping Memory DB log.")

            return result
        return wrapper