# uikitxv2/src/__init__.py

# Use explicit relative imports for sub-packages/modules within 'src'

# Corrected import for components
from .components import *

# Add similar corrected imports if you import other sub-packages/modules here
# Example:
# from .core import *
# from .utils import *
# from .lumberjack import *
# from .decorators import *
# from .PricingMonkey import *

# You might want to be more specific about what you import, e.g.:
# from .components import Button, Container, Grid, DataTable # etc.
# from .utils import default_theme
# ... and so on

# Using 'import *' is generally discouraged in __init__.py files
# as it can pollute the namespace and make it unclear where names come from.
# Consider explicitly importing the classes/functions you want to expose
# directly from the 'src' package level.

# For now, the primary fix is changing 'from components import *' to 'from .components import *'

