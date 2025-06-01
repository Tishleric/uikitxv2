# src/decorators/trace_closer.py

import logging
import functools
import uuid
import contextvars # Keep for general contextvar usage if needed elsewhere
import datetime
import json # Make sure json is imported
from zoneinfo import ZoneInfo
import os
import getpass # Standard library for getting user name
import socket  # Standard library for getting hostname

# --- Import context vars from the new central file ---
from .context_vars import log_uuid_var, current_log_data
# ---

NY_TZ = ZoneInfo("America/New_York")

class TraceCloser:
    """
    Outermost decorator that initializes and finalizes trace context for function calls.
    
    This decorator should be the outermost decorator in the stack. It sets up the
    initial context for the function call, including generating a UUID for tracking,
    and handles finalizing logs when the function completes. It captures machine and
    user information, combines all metrics collected by other decorators, and produces
    a final flow trace log.
    
    Recommended decorator order: TraceCloser(outermost) -> TraceMemory -> TraceCpu -> TraceTime(innermost)
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

        # --- Cross-platform retrieval for machine and user ID ---
        machine_name = "unknown_machine" # Default fallback
        user_name = "unknown_user"       # Default fallback
        try:
            # socket.gethostname() works on Windows and Unix-like systems
            machine_name = socket.gethostname()
        except Exception as e:
            self.logger.warning(f"Could not retrieve hostname: {e}")
        try:
            # getpass.getuser() works on Windows and Unix-like systems
            user_name = getpass.getuser()
        except Exception as e:
            # This might fail in certain environments (e.g., no controlling terminal)
            self.logger.warning(f"Could not retrieve user name: {e}")

        # Allow environment variables to override detected values
        # Store internally with the keys we want in the final log payload ('machine', 'user')
        self.machine = os.environ.get("MACHINE_ID", machine_name)
        self.user = os.environ.get("USER_ID", user_name)
        # --- End ID retrieval ---


    def __call__(self, func):
        """
        Make the class callable as a decorator.
        
        Args:
            func (callable): The function to be decorated.
            
        Returns:
            callable: The wrapped function with tracing setup and finalization.
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            """
            Wrapper function that manages trace context for the decorated function.
            
            Sets up trace context before function execution, captures metrics during
            execution, and finalizes logs after execution completes or if an exception occurs.
            
            Args:
                *args: Variable positional arguments passed to the wrapped function.
                **kwargs: Variable keyword arguments passed to the wrapped function.
                
            Returns:
                Any: The return value from the wrapped function.
                
            Raises:
                Exception: Re-raises any exception from the wrapped function.
            """
            existing_uuid = log_uuid_var.get()
            uuid_token = None
            data_token = None
            uuid_generated_here = False
            data_dict = None
            current_log_uuid = None # Initialize

            if existing_uuid is None:
                current_log_uuid = str(uuid.uuid4()) # Assign generated UUID
                data_dict = {}
                try:
                    uuid_token = log_uuid_var.set(current_log_uuid)
                    data_token = current_log_data.set(data_dict)
                    uuid_generated_here = True
                except Exception as e:
                    self.logger.error(f"TraceCloser failed to set context: {e}", exc_info=True)
                    raise
            else:
                current_log_uuid = existing_uuid # Use existing UUID
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
                 # Log the exception immediately for console visibility
                 self.logger.error(f"Exception in {func.__name__} ({current_log_uuid[:8] if current_log_uuid else 'NO_UUID'}): {e!r}", exc_info=True)
                 raise
            finally:
                # Retrieve final data from context
                final_data = current_log_data.get()

                if final_data is not None: # Check if data dict exists
                    try:
                        # Use the original function name from context if available
                        func_name = final_data.get('function_name', func.__name__)
                        end_time_utc = datetime.datetime.now(datetime.timezone.utc)
                        end_time_ny = end_time_utc.astimezone(NY_TZ)
                        timestamp_str = end_time_ny.strftime('%m/%d/%y %H:%M:%S') # Timestamp for display message
                        timestamp_iso = end_time_utc.isoformat() # ISO format for potential DB use later

                        log_level = "INFO"
                        message = ""
                        # --- NEW: Prepare metric values for payload ---
                        metric_duration = None
                        metric_cpu = None
                        metric_memory = None

                        if 'error' in final_data:
                            log_level = "ERROR"
                            message = f"Error: {final_data['error']}"
                        else:
                            # --- Retrieve metrics from context for successful calls ---
                            metric_duration = final_data.get('duration_s') # Keep as None if not found
                            metric_cpu = final_data.get('cpu_delta')
                            metric_memory = final_data.get('memory_delta_mb')
                            # --- End Retrieve metrics ---

                            # --- Build the display message ---
                            duration_str = f"{metric_duration:.3f}" if isinstance(metric_duration, (int, float)) else 'N/A'
                            memory_str = f"{metric_memory:.3f}" if isinstance(metric_memory, (int, float)) else 'N/A'
                            cpu_str = f"{metric_cpu:.2f}" if isinstance(metric_cpu, (int, float)) else 'N/A'

                            message_parts = ["Executed"]
                            if duration_str != 'N/A': message_parts.append(f"in {duration_str}s")
                            if memory_str != 'N/A': message_parts.append(f"using {memory_str}mb memory delta")
                            if cpu_str != 'N/A': message_parts.append(f"with {cpu_str}% cpu delta")

                            if len(message_parts) > 1:
                                message = " ".join(message_parts) + "."
                            else:
                                message = "Executed successfully (no metrics)."
                            # --- End Build display message ---


                        # Payload for FLOW_TRACE (using final keys)
                        flow_trace_data = {
                            "timestamp": timestamp_str,       # Display timestamp
                            "timestamp_iso": timestamp_iso,   # ISO timestamp for DB
                            "machine": self.machine,
                            "user": self.user,
                            "level": log_level,
                            "function": func_name,
                            "message": message,
                            # --- NEW: Add raw metrics to payload ---
                            "metric_duration_s": metric_duration,
                            "metric_cpu_delta": metric_cpu,
                            "metric_memory_delta_mb": metric_memory,
                            # --- End Add raw metrics ---
                        }
                        # --- End Payload ---
                        flow_trace_msg = f"{self.FLOW_TRACE_PREFIX}{json.dumps(flow_trace_data)}"

                        # Log the final message for the DB handler
                        if log_level == "ERROR":
                            self.logger.error(flow_trace_msg)
                        else:
                            self.logger.info(flow_trace_msg)

                    except Exception as log_e:
                        self.logger.error(f"TraceCloser failed to log final flowTrace message: {log_e}", exc_info=True)
                else:
                     self.logger.warning(f"TraceCloser: No final log data found in context for {func.__name__}, skipping final DB log.")


                # Reset context if generated here
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
