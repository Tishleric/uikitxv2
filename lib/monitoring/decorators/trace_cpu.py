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
    Function decorator that tracks CPU usage before and after function execution.
    
    This decorator captures the CPU percentage before calling the decorated function,
    measures it again after execution, and calculates the delta. The CPU delta is
    stored in the shared context for other decorators to access.
    """
    
    # DB_LOG_PREFIX = "CPU_TRACE_LOG:" # REMOVED - No longer emitting DB log directly

    def __init__(self):
        """
        Initialize the TraceCpu decorator.
        
        Sets up initial state for function name and logger that will be populated
        during decoration.
        """
        self.logger = None
        self.func_name = None

    def __call__(self, func):
        """
        Make the class callable as a decorator.
        
        Args:
            func (callable): The function to be decorated.
            
        Returns:
            callable: The wrapped function with CPU usage tracking.
        """
        self.logger = logging.getLogger(func.__module__)
        self.func_name = func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            """
            Wrapper function that adds CPU usage tracking.
            
            Args:
                *args: Variable positional arguments passed to the wrapped function.
                **kwargs: Variable keyword arguments passed to the wrapped function.
                
            Returns:
                Any: The return value from the wrapped function.
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
                    cpu_start = psutil.cpu_percent(interval=0.01) # Short interval before call
                    # --- Keep Console Log ---
                    self.logger.debug(f"Start CPU {self.func_name} ({initial_uuid_short}): {cpu_start:.1f}%")
                    # --- End Console Log ---
                except Exception as cpu_e:
                    self.logger.warning(f"Could not get start CPU usage for {self.func_name} ({initial_uuid_short}): {cpu_e}")

                # Execute the wrapped function
                result = func(*args, **kwargs)

            finally:
                # Measure end CPU and calculate delta
                if cpu_start is not None: # Only calculate delta if start measurement succeeded
                    try:
                        cpu_end = psutil.cpu_percent(interval=None) # Get current CPU after call
                        # --- Keep Console Log ---
                        self.logger.debug(f"End CPU {self.func_name} ({initial_uuid_short}): {cpu_end:.1f}%")
                        # --- End Console Log ---

                        cpu_delta = cpu_end - cpu_start

                        # --- Update Context ---
                        if data_dict is not None:
                            data_dict['cpu_delta'] = round(cpu_delta, 2)
                        else:
                            # Log warning if context is missing
                            self.logger.warning(f"TraceCpu: Context data dictionary not found for {self.func_name} ({initial_uuid_short}). CPU delta will not be added to context.")
                        # --- End Context Update ---

                        # --- REMOVED DB Log Emission Block ---
                        # final_log_uuid = log_uuid_var.get() # Get potentially updated UUID
                        # if final_log_uuid:
                        #     db_log_data = { ... }
                        #     db_log_msg = f"{self.DB_LOG_PREFIX}{json.dumps(db_log_data)}"
                        #     self.logger.info(db_log_msg)
                        # else:
                        #     self.logger.warning(...)
                        # --- End REMOVED Block ---

                    except Exception as cpu_e:
                        self.logger.warning(f"Could not get end CPU usage or calculate delta for {self.func_name} ({initial_uuid_short}): {cpu_e}")
                else:
                    # Log if delta couldn't be calculated because start failed
                    self.logger.debug(f"Skipping CPU delta calculation for {self.func_name} ({initial_uuid_short}) as start measurement failed.")


            return result # Return the original function's result
        return wrapper
