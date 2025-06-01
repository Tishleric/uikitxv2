"""
Browser automation module for Pricing Monkey data retrieval.

This module contains clean, reusable functions for automating browser interactions
to collect data from Pricing Monkey and parse it into a structured DataFrame.
"""

import time
import webbrowser
import pandas as pd
import pyperclip
import logging
from pywinauto.keyboard import send_keys

logger = logging.getLogger(__name__)

# Configuration Constants
PRICING_MONKEY_URL = "https://pricingmonkey.com/b/a05cfbe3-30cc-4c08-8bde-601051682959"

# Navigation Configuration
NUM_TABS = 7
NUM_DOWN_ROWS = 7
NUM_RIGHT_COLUMNS = 4

# Timing Constants
KEY_PRESS_PAUSE = 0.01
WAIT_FOR_BROWSER_TO_OPEN = 2.5
WAIT_AFTER_NAVIGATION = 0.05
WAIT_FOR_COPY_OPERATION = 0.5
WAIT_FOR_CELL_RENDERING = 5.0
WAIT_FOR_BROWSER_CLOSE = 0.5

# Column Names for DataFrame
COLUMN_NAMES = ["Trade Amount", "Trade Description", "Strike", "Expiry Date", "Price"]


class PMSimpleRetrievalError(Exception):
    """Custom exception for Pricing Monkey Simple Retrieval operations."""
    pass


def get_simple_data():
    """
    Retrieves simple data from Pricing Monkey by automating browser interactions.
    
    The function:
    1. Opens the Pricing Monkey URL
    2. Navigates using keyboard shortcuts (7 TABs, 1 DOWN)
    3. Selects data (SHIFT + 7 DOWN, SHIFT + 2 RIGHT)
    4. Copies the data to clipboard
    5. Parses the clipboard content into a DataFrame
    6. Closes the browser tab
    
    Returns:
        pd.DataFrame: DataFrame with Trade Amount, Trade Description, Strike, Expiry Date, Price columns
        
    Raises:
        PMSimpleRetrievalError: If data retrieval or parsing fails
    """
    try:
        logger.info("Starting simple data retrieval from Pricing Monkey")
        
        # Step 1: Open browser
        logger.debug(f"Opening URL: {PRICING_MONKEY_URL}")
        webbrowser.open(PRICING_MONKEY_URL, new=2)
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
        
        # Step 4: Select rows with SHIFT+DOWN
        logger.debug(f"Selecting rows: SHIFT + DOWN × {NUM_DOWN_ROWS}")
        send_keys(f'+{{DOWN {NUM_DOWN_ROWS}}}', pause=KEY_PRESS_PAUSE)
        logger.debug("Row selection complete")
        
        # Step 5: Extend selection to columns with SHIFT+RIGHT
        logger.debug(f"Extending selection: SHIFT + RIGHT × {NUM_RIGHT_COLUMNS}")
        send_keys(f'+{{RIGHT {NUM_RIGHT_COLUMNS}}}', pause=KEY_PRESS_PAUSE)
        logger.debug("Column selection complete")
        
        # Step 6: Wait for cells to render
        logger.debug(f"Waiting {WAIT_FOR_CELL_RENDERING} seconds for cells to render")
        time.sleep(WAIT_FOR_CELL_RENDERING)
        logger.debug("Cell rendering wait complete")
        
        # Step 7: Copy the data
        logger.debug("Copying selected data with CTRL+C")
        send_keys('^c', pause=KEY_PRESS_PAUSE)
        time.sleep(WAIT_FOR_COPY_OPERATION)
        logger.debug("Copy operation complete")
        
        # Step 8: Get clipboard content
        clipboard_content = pyperclip.paste()
        logger.debug(f"Clipboard content retrieved, length: {len(clipboard_content)} chars")
        
        # Step 9: Close the browser tab
        logger.debug("Closing browser tab with CTRL+W")
        send_keys('^w', pause=KEY_PRESS_PAUSE)
        time.sleep(WAIT_FOR_BROWSER_CLOSE)
        logger.debug("Browser tab closed")
        
        # Step 10: Process the clipboard content
        logger.debug("Processing clipboard data into DataFrame")
        df = process_clipboard_data(clipboard_content)
        
        if df.empty:
            raise PMSimpleRetrievalError("Clipboard content could not be processed into a valid DataFrame")
        
        logger.info(f"Successfully retrieved data: {len(df)} rows, {len(df.columns)} columns")
        
        return df
        
    except Exception as e:
        logger.error(f"Error retrieving data: {str(e)}", exc_info=True)
        raise PMSimpleRetrievalError(f"Failed to retrieve data: {str(e)}")


def process_clipboard_data(clipboard_content):
    """
    Process the clipboard content into a structured DataFrame.
    
    Args:
        clipboard_content (str): Raw clipboard content
        
    Returns:
        pd.DataFrame: Structured DataFrame with specified columns
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
        
        # Assign column names
        if len(df.columns) == len(COLUMN_NAMES):
            df.columns = COLUMN_NAMES
            logger.debug(f"Applied column names: {COLUMN_NAMES}")
        elif len(df.columns) < len(COLUMN_NAMES):
            # If we have fewer columns than expected, use as many as we can
            headers_to_use = COLUMN_NAMES[:len(df.columns)]
            df.columns = headers_to_use
            logger.warning(f"DataFrame has fewer columns ({len(df.columns)}) than expected ({len(COLUMN_NAMES)}). Using subset of headers: {headers_to_use}")
        else:
            # If we have more columns than expected, use expected names plus generic names
            headers_to_use = COLUMN_NAMES + [f"Column_{i}" for i in range(len(COLUMN_NAMES), len(df.columns))]
            df.columns = headers_to_use
            logger.warning(f"DataFrame has more columns ({len(df.columns)}) than expected ({len(COLUMN_NAMES)}). Added generic names: {headers_to_use[len(COLUMN_NAMES):]}")
        
        # Clean up data
        for col in df.columns:
            if df[col].dtype == 'object':
                # Remove \r
                df[col] = df[col].str.replace('\r', '')
                # Replace empty strings with NaN
                df[col] = df[col].replace('', pd.NA)
        
        # Handle numeric columns
        if 'Strike' in df.columns:
            try:
                # Remove commas and convert to numeric
                df['Strike'] = df['Strike'].astype(str).str.replace(',', '').str.strip()
                df['Strike'] = pd.to_numeric(df['Strike'], errors='coerce')
                logger.debug(f"Successfully converted Strike to numeric type: {df['Strike'].dtype}")
            except Exception as e:
                logger.warning(f"Error converting Strike to numeric: {str(e)}")
        
        if 'Trade Amount' in df.columns:
            try:
                # Remove commas and convert to numeric
                df['Trade Amount'] = df['Trade Amount'].astype(str).str.replace(',', '').str.strip()
                df['Trade Amount'] = pd.to_numeric(df['Trade Amount'], errors='coerce')
                logger.debug(f"Successfully converted Trade Amount to numeric type: {df['Trade Amount'].dtype}")
            except Exception as e:
                logger.warning(f"Error converting Trade Amount to numeric: {str(e)}")
        
        # Log column data types after conversion
        logger.debug("Column data types after conversion:")
        for col in df.columns:
            logger.debug(f"Column '{col}': {df[col].dtype}")
        
        return df
        
    except Exception as e:
        logger.error(f"Error processing clipboard data: {str(e)}", exc_info=True)
        # Return empty DataFrame with error information
        return pd.DataFrame({'error': [f"Failed to process data: {str(e)}"]})


if __name__ == "__main__":
    # Setup basic logging for standalone testing
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    
    logger.info("Testing browser automation module")
    
    try:
        # Execute the retrieval function
        retrieved_data = get_simple_data()
        
        if not retrieved_data.empty:
            logger.info(f"Retrieved data shape: {retrieved_data.shape}")
            
            # Show the raw retrieved data
            logger.info("\nFirst 5 rows of retrieved data:")
            print(retrieved_data.head(5).to_string())
            
            # Show column information
            logger.info("\nColumn data types:")
            for col in retrieved_data.columns:
                logger.info(f"Column '{col}': {retrieved_data[col].dtype}")
        else:
            logger.warning("Retrieved empty DataFrame")
            
    except PMSimpleRetrievalError as e:
        logger.error(f"Data retrieval failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        
    logger.info("Browser automation test finished") 