# src/decorators/trace_time.py

import logging
import functools
import time
import json
import datetime
from zoneinfo import ZoneInfo
import uuid
import contextvars

from .context_vars import log_uuid_var, current_log_data

NY_TZ = ZoneInfo("America/New_York")

class TraceTime:
    """
    Decorator that tracks and logs function execution time.
    
    This decorator captures function start/end times, calculates duration,
    logs execution details, and updates a context with timing information.
    """
    def __init__(self, log_args=True, log_return=True):
        """
        Initialize the TraceTime decorator.
        
        Args:
            log_args (bool, optional): Whether to log function arguments. Defaults to True.
            log_return (bool, optional): Whether to log function return values. Defaults to True.
        """
        self.log_args = log_args
        self.log_return = log_return
        self.logger = None
        self.func_name = None

    def __call__(self, func):
        """
        Make the TraceTime instance callable as a decorator.
        
        Args:
            func: The function to be decorated.
            
        Returns:
            function: The wrapped function with timing functionality.
        """
        self.logger = logging.getLogger(func.__module__)
        self.func_name = func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            """
            Wrapper function that adds timing functionality.
            
            Args:
                *args: Variable length argument list for the wrapped function.
                **kwargs: Arbitrary keyword arguments for the wrapped function.
                
            Returns:
                Any: The result of the wrapped function.
                
            Raises:
                Exception: Re-raises any exception from the wrapped function.
            """
            current_log_uuid = log_uuid_var.get()
            uuid_short = current_log_uuid[:8] if current_log_uuid else "NO_UUID"
            data_dict = current_log_data.get()

            start_time_perf = time.perf_counter()
            start_time_utc = datetime.datetime.now(datetime.timezone.utc)
            start_time_ny = start_time_utc.astimezone(NY_TZ)
            timestamp_console_str = start_time_ny.strftime('%m/%d/%y %H:%M:%S')

            if data_dict is not None:
                data_dict['function_name'] = self.func_name
                data_dict['start_timestamp_iso'] = start_time_utc.isoformat()
            else:
                self.logger.warning(f"TraceTime: Context data dictionary not found for {self.func_name} ({uuid_short}). Duration will not be added to context.")

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

                return result

            except Exception as e:
                end_time_perf = time.perf_counter()
                duration_s = end_time_perf - start_time_perf

                if data_dict is not None:
                    data_dict['error'] = str(e)
                    data_dict['duration_s'] = round(duration_s, 3)

                error_duration_msg = f"Exception in {self.func_name} ({uuid_short}) occurred after {duration_s:.3f}s"
                self.logger.debug(error_duration_msg)

                raise
        return wrapper 