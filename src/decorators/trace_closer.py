# src/decorators/trace_closer.py

import logging
import functools
import uuid
import contextvars
import datetime
import json
from zoneinfo import ZoneInfo
import os
import getpass
import socket

from .context_vars import log_uuid_var, current_log_data

NY_TZ = ZoneInfo("America/New_York")

class TraceCloser:
    """
    Decorator that captures execution context and generates summary logs.
    
    This decorator is designed to be the outermost decorator in a stack.
    It manages the context variables for trace IDs and collects metric data
    from inner decorators for final summary logs.
    """
    FLOW_TRACE_PREFIX = "FLOW_TRACE:"

    def __init__(self):
        """
        Initializes the decorator and retrieves machine/user IDs.
        Uses standard library functions compatible with Windows.
        Allows overrides via environment variables MACHINE_ID and USER_ID.
        Stores values using the keys 'machine' and 'user'.
        """
        self.logger = logging.getLogger(__name__)

        machine_name = "unknown_machine"
        user_name = "unknown_user"
        try:
            machine_name = socket.gethostname()
        except Exception as e:
            self.logger.warning(f"Could not retrieve hostname: {e}")
        try:
            user_name = getpass.getuser()
        except Exception as e:
            self.logger.warning(f"Could not retrieve user name: {e}")

        self.machine = os.environ.get("MACHINE_ID", machine_name)
        self.user = os.environ.get("USER_ID", user_name)

    def __call__(self, func):
        """
        Makes the TraceCloser instance callable as a decorator.
        
        Args:
            func: The function to be decorated.
            
        Returns:
            function: The wrapped function with context management and logging.
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            """
            Wrapper function that manages execution context and generates summary logs.
            
            Args:
                *args: Variable length argument list for the wrapped function.
                **kwargs: Arbitrary keyword arguments for the wrapped function.
                
            Returns:
                Any: The result of the wrapped function.
                
            Raises:
                Exception: Re-raises any exception from the wrapped function after logging it.
            """
            existing_uuid = log_uuid_var.get()
            uuid_token = None
            data_token = None
            uuid_generated_here = False
            data_dict = None
            current_log_uuid = None

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
                current_log_uuid = existing_uuid
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
                 self.logger.error(f"Exception in {func.__name__} ({current_log_uuid[:8] if current_log_uuid else 'NO_UUID'}): {e!r}", exc_info=True)
                 raise
            finally:
                final_data = current_log_data.get()

                if final_data is not None:
                    try:
                        func_name = final_data.get('function_name', func.__name__)
                        end_time_utc = datetime.datetime.now(datetime.timezone.utc)
                        end_time_ny = end_time_utc.astimezone(NY_TZ)
                        timestamp_str = end_time_ny.strftime('%m/%d/%y %H:%M:%S')
                        timestamp_iso = end_time_utc.isoformat()

                        log_level = "INFO"
                        message = ""
                        metric_duration = None
                        metric_cpu = None
                        metric_memory = None

                        if 'error' in final_data:
                            log_level = "ERROR"
                            message = f"Error: {final_data['error']}"
                        else:
                            metric_duration = final_data.get('duration_s')
                            metric_cpu = final_data.get('cpu_delta')
                            metric_memory = final_data.get('memory_delta_mb')

                            duration_str = f"{metric_duration:.3f}" if isinstance(metric_duration, (int, float)) else 'N/A'
                            memory_str = f"{metric_memory:.3f}" if isinstance(metric_memory, (int, float)) else 'N/A'
                            cpu_str = f"{metric_cpu:.2f}" if isinstance(metric_cpu, (int, float)) else 'N/A'

                            message_parts = ["Executed"]
                            if duration_str != 'N/A': message_parts.append(f"in {duration_str}s")
                            if memory_str != 'N/A': message_parts.append(f"using {memory_str}mb delta")
                            if cpu_str != 'N/A': message_parts.append(f"with {cpu_str}% delta")

                            if len(message_parts) > 1:
                                message = " ".join(message_parts) + "."
                            else:
                                message = "Executed successfully (no metrics)."

                        flow_trace_data = {
                            "timestamp": timestamp_str,
                            "timestamp_iso": timestamp_iso,
                            "machine": self.machine,
                            "user": self.user,
                            "level": log_level,
                            "function": func_name,
                            "message": message,
                            "metric_duration_s": metric_duration,
                            "metric_cpu_delta": metric_cpu,
                            "metric_memory_delta_mb": metric_memory,
                        }
                        flow_trace_msg = f"{self.FLOW_TRACE_PREFIX}{json.dumps(flow_trace_data)}"

                        if log_level == "ERROR":
                            self.logger.error(flow_trace_msg)
                        else:
                            self.logger.info(flow_trace_msg)

                    except Exception as log_e:
                        self.logger.error(f"TraceCloser failed to log final flowTrace message: {log_e}", exc_info=True)
                else:
                     self.logger.warning(f"TraceCloser: No final log data found in context for {func.__name__}, skipping final DB log.")

                if uuid_generated_here:
                    if uuid_token:
                        try:
                            log_uuid_var.reset(uuid_token)
                        except ValueError: pass
                        except Exception as e:
                             self.logger.error(f"TraceCloser failed to reset log_uuid: {e}", exc_info=True)
                    if data_token:
                        try:
                            current_log_data.reset(data_token)
                        except ValueError: pass
                        except Exception as e:
                             self.logger.error(f"TraceCloser failed to reset current_log_data: {e}", exc_info=True)
        return wrapper
