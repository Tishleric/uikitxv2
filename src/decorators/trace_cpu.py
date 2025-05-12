# src/decorators/trace_cpu.py

import logging
import functools
import time
import json
import psutil

# --- Import context vars from the new central file ---
from .context_vars import log_uuid_var, current_log_data
# ---

class TraceCpu:
    """
    Decorator that tracks and logs CPU usage during function execution.
    
    This decorator measures CPU usage before and after the wrapped function,
    calculates the delta, and adds the information to the execution context
    for summarization by TraceCloser.
    """
    # DB_LOG_PREFIX = "CPU_TRACE_LOG:" # REMOVED - No longer emitting DB log directly

    def __init__(self):
        """
        Initialize the TraceCpu decorator.
        
        Sets up the decorator with None values for logger and function name,
        which will be filled in when the decorator is applied to a function.
        """
        self.logger = None
        self.func_name = None

    def __call__(self, func):
        """
        Make the TraceCpu instance callable as a decorator.
        
        Args:
            func: The function to be decorated.
            
        Returns:
            function: The wrapped function with CPU usage tracking.
        """
        self.logger = logging.getLogger(func.__module__)
        self.func_name = func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            """
            Wrapper function that adds CPU usage tracking.
            
            Args:
                *args: Variable length argument list for the wrapped function.
                **kwargs: Arbitrary keyword arguments for the wrapped function.
                
            Returns:
                Any: The result of the wrapped function.
            """
            initial_log_uuid = log_uuid_var.get()
            initial_uuid_short = initial_log_uuid[:8] if initial_log_uuid else "NO_UUID"
            data_dict = current_log_data.get()

            cpu_start = None
            result = None
            cpu_delta = None

            try:
                try:
                    # Measure start CPU
                    cpu_start = psutil.cpu_percent(interval=0.01)
                    self.logger.debug(f"Start CPU {self.func_name} ({initial_uuid_short}): {cpu_start:.1f}%")
                except Exception as cpu_e:
                    self.logger.warning(f"Could not get start CPU usage for {self.func_name} ({initial_uuid_short}): {cpu_e}")

                # Execute the wrapped function
                result = func(*args, **kwargs)

            finally:
                # Measure end CPU and calculate delta
                if cpu_start is not None:
                    try:
                        cpu_end = psutil.cpu_percent(interval=None)
                        self.logger.debug(f"End CPU {self.func_name} ({initial_uuid_short}): {cpu_end:.1f}%")

                        cpu_delta = cpu_end - cpu_start

                        if data_dict is not None:
                            data_dict['cpu_delta'] = round(cpu_delta, 2)
                        else:
                            self.logger.warning(f"TraceCpu: Context data dictionary not found for {self.func_name} ({initial_uuid_short}). CPU delta will not be added to context.")

                    except Exception as cpu_e:
                        self.logger.warning(f"Could not get end CPU usage or calculate delta for {self.func_name} ({initial_uuid_short}): {cpu_e}")
                else:
                    self.logger.debug(f"Skipping CPU delta calculation for {self.func_name} ({initial_uuid_short}) as start measurement failed.")

            return result
        return wrapper
