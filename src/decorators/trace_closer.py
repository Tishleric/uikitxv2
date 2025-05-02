# src/decorators/trace_closer.py

import logging
import functools
import uuid
import contextvars # Keep for general contextvar usage if needed elsewhere
import datetime
import json # Make sure json is imported
from zoneinfo import ZoneInfo

# --- Import context vars from the new central file ---
from .context_vars import log_uuid_var, current_log_data
# ---

NY_TZ = ZoneInfo("America/New_York")

class TraceCloser:
    FLOW_TRACE_PREFIX = "FLOW_TRACE:"

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            existing_uuid = log_uuid_var.get()
            uuid_token = None
            data_token = None
            uuid_generated_here = False
            data_dict = None

            if existing_uuid is None:
                current_log_uuid = str(uuid.uuid4())
                data_dict = {}
                try:
                    uuid_token = log_uuid_var.set(current_log_uuid)
                    data_token = current_log_data.set(data_dict)
                    uuid_generated_here = True
                except Exception as e:
                    self.logger.error(f"TraceCloser failed to set context: {e}", exc_info=True)
                    raise
            else:
                data_dict = current_log_data.get()
                if data_dict is None:
                    self.logger.warning(f"TraceCloser found existing UUID but no data dict for {func.__name__}")
                    data_dict = {}
                    try:
                         data_token = current_log_data.set(data_dict)
                    except Exception as e:
                         self.logger.error(f"TraceCloser failed to set data context for existing UUID: {e}", exc_info=True)

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                 if data_dict is not None:
                      data_dict['error'] = str(e)
                 raise
            finally:
                final_uuid = log_uuid_var.get()
                final_data = current_log_data.get()

                if final_uuid and final_data is not None:
                    try:
                        func_name = final_data.get('function_name', func.__name__)
                        end_time_utc = datetime.datetime.now(datetime.timezone.utc)
                        end_time_ny = end_time_utc.astimezone(NY_TZ)
                        # --- Updated timestamp format for DB log ---
                        timestamp_str = end_time_ny.strftime('%m/%d/%y %H:%M:%S')

                        log_level = "INFO"
                        message = ""

                        if 'error' in final_data:
                            log_level = "ERROR"
                            message = f"Error: {final_data['error']}"
                        else:
                            duration = final_data.get('duration_s', 'N/A')
                            memory = final_data.get('memory_delta_mb', 'N/A')
                            cpu = final_data.get('cpu_delta', 'N/A')
                            # Ensure values are formatted correctly if they are numbers
                            duration_str = f"{duration:.3f}" if isinstance(duration, (int, float)) else str(duration)
                            memory_str = f"{memory:.3f}" if isinstance(memory, (int, float)) else str(memory)
                            cpu_str = f"{cpu:.2f}" if isinstance(cpu, (int, float)) else str(cpu)
                            message = f"Executed in {duration_str}s using {memory_str}mb memory delta with {cpu_str}% CPU delta."


                        flow_trace_data = {
                            "log_uuid": final_uuid,
                            "level": log_level,
                            "timestamp": timestamp_str, # Use the updated format
                            "function_name": func_name,
                            "message": message
                        }
                        flow_trace_msg = f"{self.FLOW_TRACE_PREFIX}{json.dumps(flow_trace_data)}"

                        if log_level == "ERROR":
                            self.logger.error(flow_trace_msg)
                        else:
                            self.logger.info(flow_trace_msg)

                    except Exception as log_e:
                        self.logger.error(f"TraceCloser failed to log flowTrace message: {log_e}", exc_info=True)

                if uuid_generated_here:
                    if uuid_token:
                        try:
                            log_uuid_var.reset(uuid_token)
                        except Exception as e:
                             self.logger.error(f"TraceCloser failed to reset log_uuid: {e}", exc_info=True)
                    if data_token:
                        try:
                            current_log_data.reset(data_token)
                        except Exception as e:
                             self.logger.error(f"TraceCloser failed to reset current_log_data: {e}", exc_info=True)
        return wrapper
