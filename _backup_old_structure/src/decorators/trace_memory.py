# src/decorators/trace_memory.py

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
    """
    Function decorator that tracks memory usage before and after function execution.
    
    This decorator captures the memory usage (RSS) before calling the decorated function,
    measures it again after execution, and calculates the delta in megabytes. The memory
    delta is stored in the shared context for other decorators to access.
    """
    
    # DB_LOG_PREFIX = "MEMORY_TRACE_LOG:" # REMOVED - No longer emitting DB log directly
    BYTES_TO_MB = 1 / (1024 * 1024)

    def __init__(self):
        """
        Initialize the TraceMemory decorator.
        
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
            callable: The wrapped function with memory usage tracking.
        """
        self.logger = logging.getLogger(func.__module__)
        self.func_name = func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            """
            Wrapper function that adds memory usage tracking.
            
            Args:
                *args: Variable positional arguments passed to the wrapped function.
                **kwargs: Variable keyword arguments passed to the wrapped function.
                
            Returns:
                Any: The return value from the wrapped function.
            """
            if CURRENT_PROCESS is None:
                 self.logger.warning(f"Could not get process handle for {self.func_name}, skipping memory trace.")
                 return func(*args, **kwargs)

            initial_log_uuid = log_uuid_var.get()
            initial_uuid_short = initial_log_uuid[:8] if initial_log_uuid else "NO_UUID"
            data_dict = current_log_data.get()

            mem_start_rss_mb = None
            result = None
            mem_delta_mb = None

            try:
                try:
                    # Measure start memory
                    mem_info_start = CURRENT_PROCESS.memory_info()
                    mem_start_rss_mb = mem_info_start.rss * self.BYTES_TO_MB
                    # --- Keep Console Log ---
                    self.logger.debug(f"Start Memory RSS {self.func_name} ({initial_uuid_short}): {mem_start_rss_mb:.2f} MB")
                    # --- End Console Log ---
                except Exception as mem_e:
                    self.logger.warning(f"Could not get start memory usage for {self.func_name} ({initial_uuid_short}): {mem_e}")

                # Execute the wrapped function
                result = func(*args, **kwargs)

            finally:
                 # Measure end memory and calculate delta
                 if mem_start_rss_mb is not None: # Only proceed if start measurement succeeded
                    try:
                        mem_info_end = CURRENT_PROCESS.memory_info()
                        mem_end_rss_mb = mem_info_end.rss * self.BYTES_TO_MB
                        # --- Keep Console Log ---
                        self.logger.debug(f"End Memory RSS {self.func_name} ({initial_uuid_short}): {mem_end_rss_mb:.2f} MB")
                        # --- End Console Log ---

                        mem_delta_mb = mem_end_rss_mb - mem_start_rss_mb

                        # --- Update Context ---
                        if data_dict is not None:
                            data_dict['memory_delta_mb'] = round(mem_delta_mb, 3)
                        else:
                            # Log warning if context is missing
                            self.logger.warning(f"TraceMemory: Context data dictionary not found for {self.func_name} ({initial_uuid_short}). Memory delta will not be added to context.")
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

                    except Exception as mem_e:
                        self.logger.warning(f"Could not get end memory usage or calculate delta for {self.func_name} ({initial_uuid_short}): {mem_e}")
                 else:
                    # Log if delta couldn't be calculated because start failed
                    self.logger.debug(f"Skipping Memory delta calculation for {self.func_name} ({initial_uuid_short}) as start measurement failed.")

            return result # Return the original function's result
        return wrapper
