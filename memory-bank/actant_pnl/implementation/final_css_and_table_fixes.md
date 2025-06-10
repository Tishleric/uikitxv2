# Final CSS and Table Formatting Fixes

## Overview
This document summarizes the final fixes for CSS styling and table conditional formatting in the PnL Dashboard.

## CSS Loading Fix

### Issue
The dropdown (ComboBox) styling wasn't being applied from the `custom_styles.css` file.

### Root Cause
The assets folder path needed to be:
1. Converted to an absolute path using `os.path.abspath()`
2. Passed with the correct `__name__` parameter (crucial for different runners)
3. Have an explicit `assets_url_path` set

### Solution
Updated `create_app()` function in `pnl_dashboard.py`:

```python
def create_app(data_dir: str = ".") -> dash.Dash:
    # Get the assets folder path (it's in the parent directory)
    assets_folder_path = os.path.abspath(os.path.join(SCRIPT_DIR.parent, "assets"))
    
    # Create app with assets folder for CSS styling
    app = dash.Dash(
        __name__,  # Critical for assets to work with different runners
        assets_folder=assets_folder_path,
        assets_url_path='/assets/'  # Explicitly set the URL path
    )
    
    # Log for debugging
    print(f"[INFO] Assets folder path: {assets_folder_path}")
    if os.path.exists(assets_folder_path):
        print(f"[INFO] Assets folder exists with files: {os.listdir(assets_folder_path)}")
```

### Verification
- The dashboard now properly loads `custom_styles.css` from the assets folder
- Log output confirms: `[INFO] Assets folder exists with files: ['custom_styles.css']`
- Dropdown components now have the dark theme styling defined in the CSS

## Table Conditional Formatting Fix

### Issue
The PnL table was applying green/red conditional formatting to all columns instead of just the error columns.

### Solution
Modified `_create_pnl_only_table()` to:
1. Remove conditional formatting from PnL value columns (Actant PnL, TS from ATM, TS from Neighbor)
2. Keep green/red formatting ONLY for error columns (TS0 Error, TS-0.25 Error)
3. Removed unnecessary raw value storage for non-error columns

```python
# Only store raw values for error columns
"_ts0_diff_raw": row['ts0_diff'],
"_ts_neighbor_diff_raw": row['ts_neighbor_diff']

# Apply conditional formatting ONLY to error columns
for i, row in enumerate(table_data):
    # TS0 Error
    if row['_ts0_diff_raw'] < 0:
        style_data_conditional.append({
            'if': {'row_index': i, 'column_id': 'TS0 Error'},
            'color': '#ff4444'  # Red for negative
        })
    else:
        style_data_conditional.append({
            'if': {'row_index': i, 'column_id': 'TS0 Error'},
            'color': '#44ff44'  # Green for positive
        })
```

### Result
- PnL value columns now display in standard white text
- Only error columns show green (positive) or red (negative) values
- The shift column remains highlighted with the secondary background color

## Summary of All Dashboard Refinements

1. **Path Resolution** ✅
   - Dashboard loads data regardless of where it's run from
   - Uses absolute paths based on script location

2. **Shock Multiplier** ✅
   - Fixed from 4 to 16 to match Excel model
   - All calculations now use correct basis point values

3. **UI/UX Improvements** ✅
   - ComboBox (dropdown) replaces ListBox for expiration selection
   - Time to expiry shows with decimal places (e.g., "3.438 days")
   - Graphs display side-by-side with fixed 600x400 dimensions
   - Tables display side-by-side
   - Descriptive graph titles include variable type

4. **Mathematical Accuracy** ✅
   - Taylor Series neighbor calculation matches Excel exactly
   - Each position uses its own greeks to predict the next position

5. **CSS Styling** ✅
   - Dropdown components now properly styled with dark theme
   - Assets folder correctly loaded

6. **Table Formatting** ✅
   - Price and PnL tables separated
   - Shift (bp) column prominently displayed in the middle
   - Green/red conditional formatting only on error columns

The dashboard now provides an accurate, visually appealing, and user-friendly interface for analyzing option PnL data. 