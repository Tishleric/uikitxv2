import logging
import functools
import uuid
import contextvars

# Import the shared context variable
from .logger_decorator import log_uuid_var

class TraceCloser:
    """
    An outermost decorator responsible for setting and resetting the log_uuid context variable.
    Ensures a unique log_uuid is available for the duration of the wrapped function call
    and cleans it up afterwards.
    """
    def __init__(self):
        # Logger setup can be minimal or omitted if this decorator doesn't log itself
        self.logger = logging.getLogger(__name__) # Use __name__ for module-level logger

    def __call__(self, func):
        # No need to capture func_name here unless TraceCloser logs based on it

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            existing_uuid = log_uuid_var.get()
            token = None
            uuid_generated_here = False

            if existing_uuid is None:
                # No UUID in context, generate and set one
                current_log_uuid = str(uuid.uuid4())
                try:
                    token = log_uuid_var.set(current_log_uuid)
                    uuid_generated_here = True
                    # Optional: debug log that TraceCloser set the context
                    # self.logger.debug(f"TraceCloser set log_uuid: {current_log_uuid[:8]} for {func.__name__}")
                except Exception as e:
                    self.logger.error(f"TraceCloser failed to set log_uuid: {e}", exc_info=True)
                    # Decide how to proceed - perhaps call func without context?
                    # return func(*args, **kwargs) # Option: proceed without context
                    raise # Option: re-raise, maybe context is critical
            # else:
                # UUID already exists, TraceCloser does nothing but ensures finally runs
                # self.logger.debug(f"TraceCloser found existing log_uuid: {existing_uuid[:8]} for {func.__name__}")
                # pass

            try:
                # Execute the wrapped function (which includes all inner decorators)
                result = func(*args, **kwargs)
                return result
            finally:
                # Reset the context variable *only* if this instance set it
                if uuid_generated_here and token:
                    try:
                        log_uuid_var.reset(token)
                        # Optional: debug log reset
                        # self.logger.debug(f"TraceCloser reset log_uuid for {func.__name__}")
                    except Exception as e:
                        self.logger.error(f"TraceCloser failed to reset log_uuid: {e}", exc_info=True)
                # else:
                    # If UUID existed before, this TraceCloser instance doesn't reset it
                    # self.logger.debug(f"TraceCloser ({func.__name__}) did not reset pre-existing UUID.")
                    # pass


        return wrapper

# Optional: Define a simple alias for convenience
trace_closer = TraceCloser 