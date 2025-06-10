# Dashboard Path Fix Documentation

## Problem
When running `python pnl_dashboard.py` without arguments, the dashboard failed to load the sample CSV data (`GE_XCME.ZN_20250610_103938.csv`). The issue occurred because:

1. **Relative Path Dependencies**: The script used `sys.path.append('../lib')` which assumes the current working directory is NEW
2. **Import Failures**: Local modules (`csv_parser`, `pnl_calculations`, etc.) couldn't be found when running from different directories
3. **Data Directory Mismatch**: The default "." parameter pointed to the current working directory, not where the CSV file actually exists

## Solution
Made the dashboard robust to being run from any directory by using absolute paths based on the script's location:

### Key Changes in `pnl_dashboard.py`:

1. **Script Directory Detection**:
   ```python
   # Get the directory where this script is located
   SCRIPT_DIR = Path(__file__).parent.resolve()
   ```

2. **Absolute Path Setup**:
   ```python
   # Add the lib directory to Python path (it's in the parent directory)
   LIB_PATH = SCRIPT_DIR.parent / "lib"
   sys.path.insert(0, str(LIB_PATH))
   
   # Add the script directory to Python path so we can import local modules
   sys.path.insert(0, str(SCRIPT_DIR))
   ```

3. **Updated Main Entry Point**:
   ```python
   if __name__ == "__main__":
       # Use the script directory as the data directory
       app = create_app(str(SCRIPT_DIR))
       print(f"Looking for CSV files in: {SCRIPT_DIR}")
   ```

4. **Enhanced Debugging Output**:
   - Shows exactly where it's searching for CSV files
   - Lists found CSV files
   - Provides detailed error messages with stack traces

## Benefits
- **Location Independent**: Dashboard works regardless of current working directory
- **No Manual Path Setup**: Users don't need to `cd` to specific directories
- **Better Error Messages**: Clear feedback about what's happening during data loading
- **Maintains Compatibility**: Existing functionality unchanged, just more robust

## Testing
Run `test_dashboard_fix.py` to verify the fix works from multiple directories:
```bash
python NEW/test_dashboard_fix.py
```

This test:
1. Runs the dashboard from within NEW directory
2. Runs the dashboard from parent directory  
3. Verifies CSV data loads correctly
4. Confirms expirations are available

## Usage
Now the dashboard can be run from anywhere:
```bash
# From project root
python NEW/pnl_dashboard.py

# From NEW directory
cd NEW
python pnl_dashboard.py

# From any other location
python /path/to/NEW/pnl_dashboard.py
```

All will correctly find and load the CSV data file. 