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
    Decorator that tracks and logs memory usage during function execution.
    
    This decorator measures memory usage before and after the wrapped function,
    calculates the delta, and adds the information to the execution context
    for summarization by TraceCloser.
    """
    # DB_LOG_PREFIX = "MEMORY_TRACE_LOG:" # REMOVED - No longer emitting DB log directly
    BYTES_TO_MB = 1 / (1024 * 1024)

    def __init__(self):
        """
        Initialize the TraceMemory decorator.
        
        Sets up the decorator with None values for logger and function name,
        which will be filled in when the decorator is applied to a function.
        """
        self.logger = None
        self.func_name = None

    def __call__(self, func):
        """
        Make the TraceMemory instance callable as a decorator.
        
        Args:
            func: The function to be decorated.
            
        Returns:
            function: The wrapped function with memory usage tracking.
        """
        self.logger = logging.getLogger(func.__module__)
        self.func_name = func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            """
            Wrapper function that adds memory usage tracking.
            
            Args:
                *args: Variable length argument list for the wrapped function.
                **kwargs: Arbitrary keyword arguments for the wrapped function.
                
            Returns:
                Any: The result of the wrapped function.
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
                    self.logger.debug(f"Start Memory RSS {self.func_name} ({initial_uuid_short}): {mem_start_rss_mb:.2f} MB")
                except Exception as mem_e:
                    self.logger.warning(f"Could not get start memory usage for {self.func_name} ({initial_uuid_short}): {mem_e}")

                # Execute the wrapped function
                result = func(*args, **kwargs)

            finally:
                 # Measure end memory and calculate delta
                 if mem_start_rss_mb is not None:
                    try:
                        mem_info_end = CURRENT_PROCESS.memory_info()
                        mem_end_rss_mb = mem_info_end.rss * self.BYTES_TO_MB
                        self.logger.debug(f"End Memory RSS {self.func_name} ({initial_uuid_short}): {mem_end_rss_mb:.2f} MB")

                        mem_delta_mb = mem_end_rss_mb - mem_start_rss_mb

                        if data_dict is not None:
                            data_dict['memory_delta_mb'] = round(mem_delta_mb, 3)
                        else:
                            self.logger.warning(f"TraceMemory: Context data dictionary not found for {self.func_name} ({initial_uuid_short}). Memory delta will not be added to context.")

                    except Exception as mem_e:
                        self.logger.warning(f"Could not get end memory usage or calculate delta for {self.func_name} ({initial_uuid_short}): {mem_e}")
                 else:
                    self.logger.debug(f"Skipping Memory delta calculation for {self.func_name} ({initial_uuid_short}) as start measurement failed.")

            return result
        return wrapper
