"""UIKitXv2 - Trading Dashboard Components and Utilities"""

__version__ = "2.0.0"

# Re-export main modules for convenient imports
from . import components
from . import monitoring  
from . import trading
from . import utils

# Make submodule contents directly accessible
# This enables: from components import Button
# Instead of: from lib.components import Button
import sys
sys.modules['components'] = components
sys.modules['monitoring'] = monitoring
sys.modules['trading'] = trading
sys.modules['utils'] = utils 