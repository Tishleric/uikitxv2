# Import Structure Rules

## Overview

This project uses a specific import strategy to maintain consistency and avoid circular dependencies. The approach uses a module alias in dashboard.py to make the local `src` directory appear as the `uikitxv2` package.

## Dashboard Import Rules

1. **Module Alias Setup**: Dashboard must initialize the module alias before imports:
   ```python
   import src
   sys.modules['uikitxv2'] = src
   ```

2. **All Imports Must Use 'uikitxv2' Namespace**:
   ```python
   # Correct ✅
   from uikitxv2.components import Button, Grid
   from uikitxv2.utils.colour_palette import default_theme
   
   # Incorrect ❌
   from src.components import Button, Grid  
   ```

3. **No Relative Imports Outside Current Directory**:
   ```python
   # Incorrect in dashboard.py ❌
   from ..src.components import Button
   ```

## Component Import Rules

1. **Use Relative Imports Within Same Directory**:
   ```python
   # In component implementations (src/components/button.py) ✅
   from ..core.base_component import BaseComponent  # Going up one level to src/, then to core/
   from ..utils.colour_palette import default_theme
   ```

2. **Imports in __init__.py Files Must Use Relative Paths**:
   ```python 
   # In src/components/__init__.py ✅
   from .button import Button
   from .tabs import Tabs
   
   # Incorrect ❌
   from uikitxv2.components.button import Button 
   ```

3. **Never Import Using Absolute Paths Within the Package**:
   ```python
   # Incorrect ❌
   from src.components.button import Button
   ```

## Benefits

- Avoids circular imports that occur when mixing import styles
- Prevents import errors when running dashboard.py
- Maintains consistent relative imports within package
- Enables easier package distribution later if needed

## Troubleshooting

If you encounter import errors:
1. Check that the sys.path is correctly set up to include the project root
2. Verify the module alias is defined before any package imports
3. Ensure all imports use the correct style based on their location:
   - Dashboard → uikitxv2 namespace
   - Within src → relative imports 