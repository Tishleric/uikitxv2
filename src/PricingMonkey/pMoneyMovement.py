"""
pMoneyMovement - Retrieves market movement data from Pricing Monkey

This module automates browser interactions to collect market movement data
from Pricing Monkey and store it in a DataFrame for analysis.
"""

import time
import webbrowser
import pandas as pd
import pyperclip
import logging
from pywinauto.keyboard import send_keys

logger = logging.getLogger(__name__)

# Configuration Constants
PRICING_MONKEY_MOVEMENT_URL = "https://pricingmonkey.com/b/6feae2cb-9a47-4359-9401-a7dd191efd61"

# Selection Configuration
NUM_TABS = 9
NUM_ROWS_TO_SELECT = 420  # Changed from 350 to 420 (6 scenarios × 70 rows)
NUM_COLUMNS_TO_SELECT = 7

# Treasury Math Constants
TICKS_PER_POINT = 32  # 32/32nds in a full point
BASIS_POINTS_INCREMENT = 2  # 1bp = 2/32nds

# Scenario labels for underlying categories
SCENARIOS = {
    'base': {'display_name': 'Base', 'bp_adjustment': 0},
    '-4bp': {'display_name': '-4bp', 'bp_adjustment': -4},
    '-8bp': {'display_name': '-8bp', 'bp_adjustment': -8},
    '-12bp': {'display_name': '-12bp', 'bp_adjustment': -12},
    '-16bp': {'display_name': '-16bp', 'bp_adjustment': -16},
    '-64bp': {'display_name': '-64bp', 'bp_adjustment': -64}
}

# Column Headers (as shown in screenshot)
COLUMN_HEADERS = [
    "Trade Description", 
    "Underlying", 
    "Strike", 
    "Implied Vol (Daily BP)", 
    "DV01 Gamma", 
    "Theta", 
    "%Delta", 
    "Vega"
]

# Timing Constants
KEY_PRESS_PAUSE = 0.01
WAIT_FOR_BROWSER_TO_OPEN = 2.5
WAIT_AFTER_NAVIGATION = 0.05
WAIT_FOR_COPY_OPERATION = 0.2
WAIT_FOR_CELL_RENDERING = 20.0  # Increased from 10.0 to 20.0 seconds for cells to render
WAIT_FOR_BROWSER_CLOSE = 0.5
WAIT_FOR_UNDERLYING_CELL = 15.0  # Increased from 7.0 to 15.0 seconds

class PMMovementError(Exception):
    """Custom exception for Pricing Monkey Movement operations."""
    pass

def parse_treasury_price(price_str):
    """
    Parse a Treasury price string in the format "105-20.00" into its components.
    
    Args:
        price_str (str): Treasury price string (e.g., "105-20.00")
        
    Returns:
        tuple: (whole_number, ticks, decimal)
    """
    try:
        # Handle potential whitespace
        price_str = price_str.strip()
        
        # Remove any trailing \r from clipboard content
        price_str = price_str.rstrip('\r')
        
        # Split main components
        whole_part, fractional_part = price_str.split('-')
        whole_number = int(whole_part)
        
        # Handle the decimal part if present
        if '.' in fractional_part:
            ticks_part, decimal_part = fractional_part.split('.')
            ticks = int(ticks_part)
            
            # Convert decimal_part to the proper fraction, preserving true decimal values
            # For .5, keep it as 5 (meaning half a tick)
            # For .05, keep it as 5 (from a differently formatted string)
            # For other decimals, convert appropriately
            if decimal_part == '5':
                decimal = 5
            elif decimal_part == '05':
                decimal = 5
            else:
                decimal = int(decimal_part) if decimal_part else 0
        else:
            ticks = int(fractional_part)
            decimal = 0
            
        return (whole_number, ticks, decimal)
    except Exception as e:
        logger.error(f"Error parsing Treasury price '{price_str}': {str(e)}")
        # Return a default placeholder value
        return (100, 0, 0)

def format_treasury_price(whole, ticks, decimal=0):
    """
    Format components into a Treasury price string.
    
    Args:
        whole (int): Whole number part
        ticks (int): Tick/32nds part
        decimal (int): Decimal part
        
    Returns:
        str: Formatted price string (e.g., "105-20.00")
    """
    if decimal == 5:
        # For half ticks, use .5 format
        return f"{whole}-{ticks:02d}.5"
    elif decimal > 0:
        # For other decimals, use standard format
        return f"{whole}-{ticks:02d}.{decimal:02d}"
    else:
        # No decimal part
        return f"{whole}-{ticks:02d}"

def adjust_treasury_price(price_str, basis_points):
    """
    Adjust a Treasury price by a specified number of basis points.
    
    Args:
        price_str (str): Treasury price string (e.g., "105-20.00")
        basis_points (int): Number of basis points to adjust (+/-)
        
    Returns:
        str: Adjusted price string
    """
    whole, ticks, decimal = parse_treasury_price(price_str)
    
    # Calculate tick adjustment (1bp = 2 ticks)
    tick_adjustment = basis_points * BASIS_POINTS_INCREMENT
    
    # Convert to total ticks including decimal part for precise calculation
    total_ticks = ticks
    if decimal == 5:
        total_ticks += 0.5
    
    # Apply adjustment to total ticks
    new_total_ticks = total_ticks + tick_adjustment
    
    # Calculate new whole number and ticks
    new_whole = whole
    
    # Handle rollovers
    while new_total_ticks >= TICKS_PER_POINT:
        new_total_ticks -= TICKS_PER_POINT
        new_whole += 1
        
    # Handle underflows
    while new_total_ticks < 0:
        new_total_ticks += TICKS_PER_POINT
        new_whole -= 1
    
    # Extract integer and decimal parts
    new_ticks = int(new_total_ticks)
    new_decimal = 0
    
    # Check if there's a fractional part to represent as .5
    if new_total_ticks - new_ticks >= 0.4:  # Use 0.4 as threshold to account for float precision issues
        new_decimal = 5
    
    return format_treasury_price(new_whole, new_ticks, new_decimal)

def split_dataframe_by_expiry(df):
    """
    Splits the market movement DataFrame into separate DataFrames by expiry (1st, 2nd, etc.)
    
    Args:
        df (pd.DataFrame): The complete market movement DataFrame
        
    Returns:
        dict: Dictionary with keys as expiry names (1st, 2nd, etc.) and values as filtered DataFrames
    """
    if df.empty or 'Trade Description' not in df.columns:
        logger.warning("Cannot split DataFrame: empty or missing 'Trade Description' column")
        return {'1st': df}  # Return original DataFrame as fallback
    
    # Extract expiry from Trade Description column
    def extract_expiry(desc):
        if not isinstance(desc, str):
            return None
        words = desc.split()
        if len(words) > 0:
            # First word should be the expiry (1st, 2nd, etc.)
            return words[0]
        return None
    
    # Add expiry column
    df['expiry'] = df['Trade Description'].apply(extract_expiry)
    
    # Get unique expiries
    expiries = df['expiry'].dropna().unique()
    logger.info(f"Found {len(expiries)} unique expiries: {', '.join(expiries)}")
    
    # Create dictionary of DataFrames by expiry
    result = {}
    for expiry in expiries:
        expiry_df = df[df['expiry'] == expiry].copy()
        expiry_df = expiry_df.drop(columns=['expiry'])  # Remove temporary column
        
        # Sort by Strike value to ensure correct line plotting
        if 'Strike' in expiry_df.columns:
            expiry_df = expiry_df.sort_values(by='Strike')
            logger.debug(f"Sorted DataFrame for expiry '{expiry}' by Strike values")
        
        result[expiry] = expiry_df
        logger.debug(f"Created DataFrame for expiry '{expiry}' with {len(expiry_df)} rows")
    
    return result

def split_dataframe_by_expiry_and_underlying(df):
    """
    Splits the market movement DataFrame into separate DataFrames by both expiry and underlying value.
    Uses row indices to determine the underlying category (base, -4bp, -8bp, -12bp, -16bp).
    
    Args:
        df (pd.DataFrame): The complete market movement DataFrame
        
    Returns:
        dict: Nested dictionary with structure {underlying: {expiry: dataframe}}
    """
    if df.empty or 'Trade Description' not in df.columns:
        logger.warning("Cannot split DataFrame: empty or missing required columns")
        # Return minimal structure with metadata
        return {
            'data': {'base': {'1st': df}},
            'metadata': {key: [] for key in SCENARIOS.keys()}
        }
    
    # Extract expiry from Trade Description column
    def extract_expiry(desc):
        if not isinstance(desc, str):
            return None
        words = desc.split()
        if len(words) > 0:
            # First word should be the expiry (1st, 2nd, etc.)
            return words[0]
        return None
    
    # Add expiry column
    df['expiry'] = df['Trade Description'].apply(extract_expiry)
    
    # Get unique expiries
    expiries = sorted(df['expiry'].dropna().unique())
    logger.info(f"Found {len(expiries)} unique expiries: {', '.join(expiries)}")
    
    # Get scenario values from the dataframe attributes if they exist
    scenario_values = {key: [] for key in SCENARIOS.keys()}
    
    # Try to get values from dataframe attributes if they exist
    for scenario_key in SCENARIOS.keys():
        attr_name = f"{scenario_key}_values"
        if hasattr(df, attr_name):
            scenario_values[scenario_key] = getattr(df, attr_name)
    
    # If we don't have the values stored, extract them from the dataframe
    if not any(scenario_values.values()):
        logger.warning("No stored scenario values, will extract from DataFrame rows")
        
        # Extract approximate ranges based on row indices
        total_rows = len(df)
        rows_per_scenario = total_rows // len(SCENARIOS)
        
        # Extract unique underlying values from each section
        if 'Underlying' in df.columns:
            for i, scenario_key in enumerate(SCENARIOS.keys()):
                start_idx = i * rows_per_scenario
                end_idx = (i + 1) * rows_per_scenario
                if end_idx <= total_rows:
                    scenario_df = df.iloc[start_idx:end_idx]
                    scenario_values[scenario_key] = scenario_df['Underlying'].unique().tolist() if not scenario_df.empty else []
    
    # Split DataFrame by row ranges
    total_rows = len(df)
    rows_per_scenario = total_rows // len(SCENARIOS)
    
    # Create dataframe slices for each scenario
    scenario_dfs = {}
    for i, scenario_key in enumerate(SCENARIOS.keys()):
        start_idx = i * rows_per_scenario
        end_idx = (i + 1) * rows_per_scenario
        if end_idx <= total_rows:
            scenario_dfs[scenario_key] = df.iloc[start_idx:end_idx].copy()
        else:
            # Handle case where we've reached the end of the dataframe
            scenario_dfs[scenario_key] = df.iloc[start_idx:].copy()
    
    # Create final result structure
    final_result = {
        'data': {key: {} for key in SCENARIOS.keys()},
        'metadata': {key: vals for key, vals in scenario_values.items()}
    }
    
    # Process each scenario and expiry
    for scenario_key, scenario_df in scenario_dfs.items():
        # Skip if empty
        if scenario_df.empty:
            continue
            
        # Split this scenario by expiry
        for expiry in expiries:
            expiry_df = scenario_df[scenario_df['expiry'] == expiry].copy()
            
            # Skip if this expiry is empty for this scenario
            if expiry_df.empty:
                continue
                
            # Remove temporary column
            expiry_df = expiry_df.drop(columns=['expiry'])
            
            # Sort by Strike value for correct line plotting
            if 'Strike' in expiry_df.columns:
                expiry_df = expiry_df.sort_values(by='Strike')
                logger.debug(f"Sorted DataFrame for {scenario_key}/{expiry} by Strike values")
            
            # Store in the result structure
            final_result['data'][scenario_key][expiry] = expiry_df
            logger.debug(f"Created DataFrame for {scenario_key}/{expiry} with {len(expiry_df)} rows")
    
    # Count total DataFrames for logging
    total_dfs = sum(len(expiry_dict) for expiry_dict in final_result['data'].values())
    logger.info(f"Split data into {len(final_result['data'])} underlying groups with {total_dfs} total DataFrames")
    
    return final_result

def get_market_movement_data_df():
    """
    Convenience function that returns the market movement data as a nested dictionary of DataFrames 
    by both underlying and expiry, without saving to CSV. Useful for direct integration with the dashboard.
    
    Returns:
        dict: Nested dictionary with structure {underlying: {expiry: dataframe}}
        
    Raises:
        PMMovementError: If data retrieval fails
    """
    try:
        df = get_market_movement_data(save_to_csv=False)
        result = split_dataframe_by_expiry_and_underlying(df)
        
        # Print DataFrames for debugging when called from dashboard
        print("\n=== MARKET MOVEMENT DATA (called from dashboard) ===")
        
        # Count total rows
        total_rows = 0
        for underlying, expiry_dict in result['data'].items():
            for expiry, df in expiry_dict.items():
                total_rows += len(df)
        
        print(f"Retrieved {total_rows} total rows across {len(result['data'])} underlying values")
        
        # Print sample of data
        for underlying, expiry_dict in result['data'].items():
            print(f"\n=== {underlying.upper()} UNDERLYING ===")
            for expiry, df in sorted(expiry_dict.items()):
                print(f"  -- {expiry} EXPIRY ({'empty' if df.empty else f'{len(df)} rows'})")
                if not df.empty:
                    print(df.head(2).to_string())
                    print("  ...")
        
        return result
    except PMMovementError as e:
        logger.error(f"Failed to get market movement data: {str(e)}")
        # Return an empty dictionary with the same structure
        return {'data': {'base': {'1st': pd.DataFrame(columns=COLUMN_HEADERS)}}, 'metadata': {'base_underlying_values': [], 'plus_1bp_values': [], 'minus_1bp_values': []}}

def get_market_movement_data(num_rows=NUM_ROWS_TO_SELECT, num_columns=NUM_COLUMNS_TO_SELECT, save_to_csv=True):
    """
    Main function to retrieve market movement data from Pricing Monkey.
    
    Args:
        num_rows: Number of rows to select (default: 420)
        num_columns: Number of columns to select (default: 7)
        save_to_csv: Whether to save the data to a CSV file (default: True)
    
    Returns:
        pd.DataFrame: DataFrame containing the market movement data
    
    Raises:
        PMMovementError: If any step in the process fails
    """
    try:
        logger.info(f"Starting market movement data retrieval (rows={num_rows}, columns={num_columns})")
        
        # Step 1: Open browser
        logger.debug(f"Opening URL: {PRICING_MONKEY_MOVEMENT_URL}")
        webbrowser.open(PRICING_MONKEY_MOVEMENT_URL, new=2)
        time.sleep(WAIT_FOR_BROWSER_TO_OPEN)
        logger.debug("Browser opened, waiting for page to load")
        
        # Step 2: Navigate with keyboard shortcuts
        logger.debug(f"Navigating with {NUM_TABS} TAB presses")
        for i in range(NUM_TABS):
            send_keys('{TAB}', pause=KEY_PRESS_PAUSE)
            logger.debug(f"TAB press {i+1}/{NUM_TABS} complete")
        
        # Step 3: Press DOWN once to move to first row
        logger.debug("Pressing DOWN arrow once")
        send_keys('{DOWN}', pause=KEY_PRESS_PAUSE)
        logger.debug("DOWN arrow press complete")
        
        # New Step: Move to Underlying column and select all base values at once
        logger.debug("Moving to underlying column")
        send_keys('{RIGHT}', pause=KEY_PRESS_PAUSE)
        logger.debug(f"Waiting {WAIT_FOR_UNDERLYING_CELL} seconds for underlying cell to be ready")
        time.sleep(WAIT_FOR_UNDERLYING_CELL)
        
        # Select all 70 base underlying values
        logger.debug("Selecting all 70 base underlying values")
        send_keys('+{DOWN 69}', pause=KEY_PRESS_PAUSE)
        time.sleep(WAIT_AFTER_NAVIGATION)
        
        # Copy the selected values
        logger.debug("Copying base underlying values")
        send_keys('^c', pause=WAIT_FOR_COPY_OPERATION)
        time.sleep(WAIT_FOR_COPY_OPERATION)
        
        # Parse the multiline clipboard content
        base_underlying_values = pyperclip.paste().strip().split('\n')
        logger.info(f"Collected {len(base_underlying_values)} base underlying values")
        
        # Log some sample values to verify
        if len(base_underlying_values) > 0:
            logger.info(f"First base value: {base_underlying_values[0]}")
            if len(base_underlying_values) > 60:
                logger.info(f"Last few base values: {base_underlying_values[-10:]}")
        
        # Generate scenario values for each base value
        scenario_values = {}
        for scenario_key, scenario_info in SCENARIOS.items():
            if scenario_key == 'base':
                scenario_values[scenario_key] = base_underlying_values
                continue
                
            bp_adjustment = scenario_info['bp_adjustment']
            scenario_values[scenario_key] = [adjust_treasury_price(val, bp_adjustment) for val in base_underlying_values]
            logger.info(f"Generated {scenario_key} values with {bp_adjustment}bp adjustment")
        
        # Process each scenario in sequence after the base one
        scenario_keys = list(SCENARIOS.keys())
        
        # For each scenario beyond the base
        for i, scenario_key in enumerate(scenario_keys[1:], 1):
            # Move down 70 times to reach the next section
            logger.debug(f"Moving down 70 more times to reach {scenario_key} section")
            for _ in range(70):
                send_keys('{DOWN}', pause=KEY_PRESS_PAUSE)
            time.sleep(WAIT_AFTER_NAVIGATION)
            
            # Prepare clipboard data for scenario values
            logger.debug(f"Preparing {scenario_key} data for pasting")
            scenario_clipboard = '\n'.join(scenario_values[scenario_key])
            
            # Paste the scenario data
            logger.debug(f"Pasting {scenario_key} data")
            pyperclip.copy(scenario_clipboard)
            time.sleep(WAIT_FOR_COPY_OPERATION)
            send_keys('^v', pause=WAIT_FOR_COPY_OPERATION)
            time.sleep(WAIT_FOR_COPY_OPERATION)
        
        # Navigate to the bottom: move to the last row + left once
        logger.debug("Navigating to bottom position for selection")
        for i in range(69):  # Navigate to the last row
            send_keys('{DOWN}', pause=KEY_PRESS_PAUSE)
        send_keys('{LEFT}', pause=KEY_PRESS_PAUSE)
        time.sleep(WAIT_AFTER_NAVIGATION)
        
        # Select all 420 rows from bottom (6 scenarios × 70 rows each)
        logger.debug(f"Selecting all data: SHIFT + UP × {num_rows}")
        logger.debug(f"Sending key sequence: '+{{UP {num_rows}}}'")
        send_keys('+{UP ' + str(num_rows) + '}', pause=KEY_PRESS_PAUSE)
        logger.debug("SHIFT + UP selection complete")
        
        # Step 5: Extend selection with SHIFT+RIGHT
        logger.debug(f"Extending selection: SHIFT + RIGHT × {num_columns}")
        logger.debug(f"Sending key sequence: '+{{RIGHT {num_columns}}}'")
        send_keys('+{RIGHT ' + str(num_columns) + '}', pause=KEY_PRESS_PAUSE)
        logger.debug("SHIFT + RIGHT selection extension complete")
        
        # Step 6: Wait for cells to render
        logger.debug(f"Waiting {WAIT_FOR_CELL_RENDERING} seconds for cells to render")
        time.sleep(WAIT_FOR_CELL_RENDERING)
        logger.debug("Cell rendering wait complete")
        
        # Step 7: Copy the data
        logger.debug("Copying selected data with CTRL+C")
        send_keys('^c', pause=WAIT_FOR_COPY_OPERATION)
        logger.debug("Copy operation complete")
        
        # Step 8: Get clipboard content
        clipboard_content = pyperclip.paste()
        logger.debug(f"Clipboard content retrieved, length: {len(clipboard_content)} chars")
        
        # Step 9: Close the browser tab
        logger.debug("Closing browser tab with CTRL+W")
        send_keys('^w', pause=WAIT_FOR_BROWSER_CLOSE)
        logger.debug("Browser tab closed")
        
        # Step 10: Process the clipboard content
        logger.debug("Processing clipboard data into DataFrame")
        df = process_clipboard_data(clipboard_content)
        
        if df.empty:
            raise PMMovementError("Clipboard content could not be processed into a valid DataFrame")
        
        if 'error' in df.columns and len(df) == 1:
            error_msg = df['error'].iloc[0]
            raise PMMovementError(f"Error in processed data: {error_msg}")
        
        logger.info(f"Successfully retrieved market movement data: {len(df)} rows, {len(df.columns)} columns")
        logger.info(f"Retrieved data shape: {df.shape}")
        
        # Save to CSV if requested
        if save_to_csv:
            csv_path = 'market_movement_data.csv'
            df.to_csv(csv_path, index=False)
            logger.info(f"Data saved to {csv_path} for reference")
        
        # Store the scenario values for later grouping
        for scenario_key, values in scenario_values.items():
            setattr(df, f"{scenario_key}_values", values)
        
        return df
        
    except Exception as e:
        logger.error(f"Error retrieving market movement data: {str(e)}", exc_info=True)
        raise PMMovementError(f"Failed to retrieve market movement data: {str(e)}")

def process_clipboard_data(clipboard_content):
    """
    Process the clipboard content into a structured DataFrame using predefined column headers.
    
    Args:
        clipboard_content (str): Raw clipboard content
        
    Returns:
        pd.DataFrame: Structured DataFrame with market movement data
    """
    try:
        # Split into lines and handle tab-delimited data
        lines = clipboard_content.strip().split('\n')
        logger.debug(f"Clipboard content split into {len(lines)} lines")
        
        if len(lines) < 2:
            logger.warning(f"Very few lines found in clipboard: {len(lines)}. Content snippet: {clipboard_content[:100]}...")
            
        data = [line.split('\t') for line in lines]
        
        # Create DataFrame
        df = pd.DataFrame(data)
        logger.debug(f"Initial DataFrame created with shape: {df.shape}")
        
        # Use predefined column headers instead of first row
        if len(df.columns) == len(COLUMN_HEADERS):
            df.columns = COLUMN_HEADERS
            logger.debug(f"Applied predefined column headers: {COLUMN_HEADERS}")
        elif len(df.columns) < len(COLUMN_HEADERS):
            # If we have fewer columns than headers, use as many as we can
            headers_to_use = COLUMN_HEADERS[:len(df.columns)]
            df.columns = headers_to_use
            logger.warning(f"DataFrame has fewer columns ({len(df.columns)}) than expected ({len(COLUMN_HEADERS)}). Using subset of headers: {headers_to_use}")
        else:
            # If we have more columns than headers, use headers plus generic names
            headers_to_use = COLUMN_HEADERS + [f"Column_{i}" for i in range(len(COLUMN_HEADERS), len(df.columns))]
            df.columns = headers_to_use
            logger.warning(f"DataFrame has more columns ({len(df.columns)}) than expected ({len(COLUMN_HEADERS)}). Added generic names: {headers_to_use[len(COLUMN_HEADERS):]}")
        
        # Clean up data (remove \r, loading states, etc.)
        for col in df.columns:
            if df[col].dtype == 'object':
                # Remove \r
                df[col] = df[col].str.replace('\r', '')
                # Replace "Loading..." with NaN
                df[col] = df[col].replace('Loading...', pd.NA)
        
        # Special handling for %Delta column - strip % and convert to float
        if '%Delta' in df.columns:
            logger.debug("Processing %Delta column - stripping % symbol and converting to float")
            try:
                # Remove % symbols and convert to float
                df['%Delta'] = df['%Delta'].str.replace('%', '').astype(float) / 100.0
                logger.debug("Successfully converted %Delta column to float")
            except Exception as e:
                logger.warning(f"Error converting %Delta column to float: {str(e)}")
        
        # Ensure all numeric columns are properly converted, even if they have commas
        numeric_columns = ['Strike', 'Implied Vol (Daily BP)', 'DV01 Gamma', 'Theta', 'Vega']
        for col in numeric_columns:
            if col in df.columns:
                try:
                    # First, check if we need to remove commas
                    if df[col].dtype == 'object':
                        # Remove commas and convert to numeric
                        df[col] = df[col].astype(str).str.replace(',', '').str.strip()
                        logger.debug(f"Removed commas from {col} column")
                    
                    # Convert to numeric (handles remaining formatting issues)
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    logger.debug(f"Successfully converted {col} to numeric type: {df[col].dtype}")
                except Exception as e:
                    logger.warning(f"Error converting {col} to numeric: {str(e)}")
        
        # Log column data types after conversion
        logger.debug("Column data types after conversion:")
        for col in df.columns:
            logger.debug(f"Column '{col}': {df[col].dtype}")
        
        return df
        
    except Exception as e:
        logger.error(f"Error processing clipboard data: {str(e)}", exc_info=True)
        # Return empty DataFrame with error information
        return pd.DataFrame({'error': [f"Failed to process data: {str(e)}"]})

def try_alternative_selection_strategy(attempt=1):
    """
    Alternative selection strategies if the default one fails.
    
    Args:
        attempt (int): The attempt number, to try different strategies
        
    Returns:
        str: Clipboard content if successful, None otherwise
    """
    logger.info(f"Trying alternative selection strategy (attempt {attempt})")
    
    try:
        if attempt == 1:
            # Try selecting row by row with individual arrow presses
            logger.debug("Strategy 1: Individual row selection with +{DOWN}")
            send_keys('{DOWN}', pause=KEY_PRESS_PAUSE)  # First position cursor
            time.sleep(WAIT_AFTER_NAVIGATION)
            
            # Select first row
            send_keys('+{DOWN}', pause=KEY_PRESS_PAUSE)
            time.sleep(WAIT_AFTER_NAVIGATION)
            
            # Extend by 10 rows at a time, 7 times (70 rows)
            for i in range(7):
                logger.debug(f"Extending selection by 10 rows (batch {i+1}/7)")
                send_keys('+{DOWN 10}', pause=KEY_PRESS_PAUSE)
                time.sleep(WAIT_AFTER_NAVIGATION * 2)  # Slightly longer wait
            
            # Select columns
            logger.debug("Extending selection horizontally with +{RIGHT 7}")
            send_keys('+{RIGHT 7}', pause=KEY_PRESS_PAUSE)
            time.sleep(WAIT_AFTER_NAVIGATION)
            
        elif attempt == 2:
            # Try with fewer rows, maybe data is shorter
            logger.debug("Strategy 2: Selecting fewer rows (30 instead of 70)")
            send_keys('{DOWN}', pause=KEY_PRESS_PAUSE)
            time.sleep(WAIT_AFTER_NAVIGATION)
            send_keys('+{DOWN 30}', pause=KEY_PRESS_PAUSE)
            time.sleep(WAIT_AFTER_NAVIGATION * 2)  # Slightly longer wait
            send_keys('+{RIGHT 7}', pause=KEY_PRESS_PAUSE)
            time.sleep(WAIT_AFTER_NAVIGATION)
        
        # Wait for cells to render fully (adding this to alternative strategies as well)
        logger.debug(f"Waiting {WAIT_FOR_CELL_RENDERING} seconds for cells to render")
        time.sleep(WAIT_FOR_CELL_RENDERING)
        logger.debug("Cell rendering wait complete")
        
        # Copy the selection
        logger.debug("Copying selection with ^c")
        send_keys('^c', pause=KEY_PRESS_PAUSE)
        time.sleep(WAIT_FOR_COPY_OPERATION * 2)  # Double the wait time for copy
        
        # Check if we got data
        clipboard_content = pyperclip.paste()
        if clipboard_content:
            logger.debug(f"Alternative strategy {attempt} successful, got {len(clipboard_content)} chars")
            return clipboard_content
        else:
            logger.warning(f"Alternative strategy {attempt} failed, clipboard empty")
            return None
            
    except Exception as e:
        logger.error(f"Error in alternative selection strategy {attempt}: {str(e)}")
        return None

if __name__ == "__main__":
    # Setup basic logging for standalone use
    logging.basicConfig(level=logging.DEBUG,  # Changed to DEBUG for more detail during testing
                        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    
    logger.info("Running pMoneyMovement.py in standalone mode")
    
    try:
        try:
            # First try with default parameters
            movement_data = get_market_movement_data()
        except PMMovementError as e:
            logger.warning(f"First attempt failed: {str(e)}")
            logger.info("Trying alternative selection strategy...")
            
            # Try the first alternative strategy
            clipboard_content = try_alternative_selection_strategy(attempt=1)
            if clipboard_content:
                movement_data = process_clipboard_data(clipboard_content)
                logger.info("Alternative strategy 1 successful")
            else:
                # Try the second alternative strategy
                logger.info("Trying second alternative strategy...")
                clipboard_content = try_alternative_selection_strategy(attempt=2)
                if clipboard_content:
                    movement_data = process_clipboard_data(clipboard_content)
                    logger.info("Alternative strategy 2 successful")
                else:
                    # Try with fewer rows directly
                    logger.info("Trying main function with fewer rows...")
                    try:
                        movement_data = get_market_movement_data(num_rows=30)
                        logger.info("Reduced row count approach successful")
                    except Exception as e2:
                        logger.error(f"Reduced row count attempt also failed: {str(e2)}")
                        raise PMMovementError("All selection strategies failed")
        
        if not movement_data.empty:
            logger.info(f"Retrieved data shape: {movement_data.shape}")
            
            # Save to CSV for backup/debugging
            try:
                csv_path = "market_movement_data.csv"
                movement_data.to_csv(csv_path, index=False)
                logger.info(f"Data saved to {csv_path} for reference")
            except Exception as e:
                logger.warning(f"Could not save CSV: {str(e)}")
                
            logger.info("\nFirst 5 rows of market movement data:")
            print(movement_data.head(5).to_string())
            
            # Show column information for better debugging
            logger.info("\nColumn data types:")
            for col in movement_data.columns:
                logger.info(f"Column '{col}': {movement_data[col].dtype}")
            
            # Split by both expiry and underlying and print each dataframe
            logger.info("\nSplitting data by expiry and underlying...")
            result = split_dataframe_by_expiry_and_underlying(movement_data)
            
            # Count total DataFrames
            total_dfs = sum(len(inner_dict) for inner_dict in result['data'].values())
            logger.info(f"Split into {len(result['data'])} underlying groups with {total_dfs} total DataFrames")
            
            # Print sample of data
            for underlying, expiry_dict in result['data'].items():
                logger.info(f"\n=== {underlying.upper()} UNDERLYING ===")
                for expiry, df in sorted(expiry_dict.items()):
                    logger.info(f"  -- {expiry} EXPIRY ({'empty' if df.empty else f'{len(df)} rows'})")
                    if not df.empty and len(df) > 0:
                        print(df.head(1).to_string())
                        print("  ...")
                
        else:
            logger.warning("Retrieved empty DataFrame")
            
    except PMMovementError as e:
        logger.error(f"Market movement retrieval failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        
    logger.info("Standalone pMoneyMovement.py test finished") 