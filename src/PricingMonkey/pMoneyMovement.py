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
NUM_ROWS_TO_SELECT = 70
NUM_COLUMNS_TO_SELECT = 7

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
WAIT_FOR_CELL_RENDERING = 7.0  # New longer wait for cells to render
WAIT_FOR_BROWSER_CLOSE = 0.5

class PMMovementError(Exception):
    """Custom exception for Pricing Monkey Movement operations."""
    pass

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

def get_market_movement_data_df():
    """
    Convenience function that returns the market movement data as a dictionary of DataFrames by expiry,
    without saving to CSV. Useful for direct integration with the dashboard.
    
    Returns:
        dict: Dictionary with expiry names (1st, 2nd, etc.) as keys and DataFrames as values
        
    Raises:
        PMMovementError: If data retrieval fails
    """
    try:
        df = get_market_movement_data(save_to_csv=False)
        expiry_dfs = split_dataframe_by_expiry(df)
        
        # Print DataFrames for debugging when called from dashboard
        print("\n=== MARKET MOVEMENT DATA (called from dashboard) ===")
        for expiry, expiry_df in sorted(expiry_dfs.items()):
            print(f"\n=== {expiry} EXPIRY ({'empty' if expiry_df.empty else f'{len(expiry_df)} rows'}) ===")
            if not expiry_df.empty:
                print(expiry_df.head(3).to_string())
                print("...")
                if len(expiry_df) > 3:
                    print(expiry_df.tail(2).to_string())
                print(f"[{len(expiry_df)} rows total]")
        
        return expiry_dfs
    except PMMovementError as e:
        logger.error(f"Failed to get market movement data: {str(e)}")
        # Return an empty dictionary with the same structure
        return {'1st': pd.DataFrame(columns=COLUMN_HEADERS)}

def get_market_movement_data(num_rows=NUM_ROWS_TO_SELECT, num_columns=NUM_COLUMNS_TO_SELECT, save_to_csv=True):
    """
    Main function to retrieve market movement data from Pricing Monkey.
    
    Args:
        num_rows: Number of rows to select (default: 70)
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
        
        # Step 4: Select data with SHIFT+DOWN multiple times
        logger.debug(f"Selecting data: SHIFT + DOWN × {num_rows}")
        logger.debug(f"Sending key sequence: '+{{DOWN {num_rows}}}'")
        send_keys('+{DOWN ' + str(num_rows) + '}', pause=KEY_PRESS_PAUSE)
        logger.debug("SHIFT + DOWN selection complete")
        
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
            
        # Display a preview of the data
        logger.info("\nFirst 5 rows of market movement data:")
        logger.info(df.head())
        
        # Show column data types
        logger.info("\nColumn data types:")
        for col in df.columns:
            logger.info(f"Column '{col}': {df[col].dtype}")
        
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
        
        # Attempt to convert numeric columns
        numeric_cols = []
        for col in df.columns:
            if col != '%Delta':  # Skip %Delta as we already processed it
                try:
                    df[col] = pd.to_numeric(df[col])
                    numeric_cols.append(col)
                except (ValueError, TypeError):
                    # Keep as string if conversion fails
                    pass
        
        if '%Delta' in df.columns and df['%Delta'].dtype.kind in 'fc':  # Check if float or complex
            numeric_cols.append('%Delta')
            
        logger.debug(f"Converted {len(numeric_cols)} columns to numeric type: {', '.join(numeric_cols) if numeric_cols else 'none'}")
                
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
            
            # Split by expiry and print each dataframe
            logger.info("\nSplitting data by expiry...")
            expiry_dfs = split_dataframe_by_expiry(movement_data)
            logger.info(f"Split into {len(expiry_dfs)} expiry dataframes")
            
            # Print first few rows of each expiry dataframe
            for expiry, df in expiry_dfs.items():
                logger.info(f"\n{expiry} expiry data ({len(df)} rows):")
                print(f"=== {expiry} EXPIRY ({'empty' if df.empty else f'{len(df)} rows'}) ===")
                if not df.empty:
                    print(df.head(3).to_string())
                    print("...")
                    if len(df) > 3:
                        print(df.tail(2).to_string())
                    print(f"[{len(df)} rows total]")
                
        else:
            logger.warning("Retrieved empty DataFrame")
            
    except PMMovementError as e:
        logger.error(f"Market movement retrieval failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        
    logger.info("Standalone pMoneyMovement.py test finished") 