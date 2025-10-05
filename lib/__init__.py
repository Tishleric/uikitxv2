"""UIKitXv2 - Trading Dashboard Components and Utilities"""

__version__ = "2.0.0"

import os

# In headless/remote contexts (e.g., BigBrother sidecar), avoid importing heavy UI deps
_HEADLESS = os.environ.get("UIKITXV2_HEADLESS", "0") == "1"

if not _HEADLESS:
    # Re-export main modules for convenient imports
    from . import components  # type: ignore
    from . import monitoring  # type: ignore
    from . import trading  # type: ignore
    # from . import utils  # Utils module not implemented yet

    # Make submodule contents directly accessible
    # This enables: from components import Button
    # Instead of: from lib.components import Button
    import sys
    sys.modules['components'] = components
    sys.modules['monitoring'] = monitoring
    sys.modules['trading'] = trading
    # sys.modules['utils'] = utils  # Utils module not implemented yet