#!/usr/bin/env python3
"""
Pricing Monkey data retrieval module for ActantEOD.

This module automates browser interactions to collect extended data from Pricing Monkey
including additional risk metrics (DV01 Gamma, Vega, %Delta, Theta) for scenario analysis.
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

# Navigation Configuration - Extended for 9 columns
NUM_TABS = 7
NUM_DOWN_ROWS = 7
NUM_RIGHT_COLUMNS = 8  # Extended from 4 to capture additional metrics

# Timing Constants
KEY_PRESS_PAUSE = 0.01
WAIT_FOR_BROWSER_TO_OPEN = 2.5
WAIT_AFTER_NAVIGATION = 0.05
WAIT_FOR_COPY_OPERATION = 0.5
WAIT_FOR_CELL_RENDERING = 5.0
WAIT_FOR_BROWSER_CLOSE = 0.5

# Extended column names for ActantEOD analysis
COLUMN_NAMES = [
    "Trade Amount", "Trade Description", "Strike", "Expiry Date", "Price",
    "DV01 Gamma", "Vega", "%Delta", "Theta"
]


class PMRetrievalError(Exception):
    """Custom exception for Pricing Monkey retrieval operations."""
    pass


def get_extended_pm_data():
    """
    Retrieves extended Pricing Monkey data for ActantEOD scenario analysis.
    
    Extended from ActantSOD version to capture 9 columns including risk metrics:
    Trade Amount, Trade Description, Strike, Expiry Date, Price, DV01 Gamma, Vega, %Delta, Theta
    
    Returns:
        pd.DataFrame: DataFrame with extended column set for risk analysis
        
    Raises:
        PMRetrievalError: If data retrieval or parsing fails
    """
    try:
        logger.info("Starting extended PM data retrieval for ActantEOD")
        
        # Step 1: Open browser
        logger.debug(f"Opening URL: {PRICING_MONKEY_URL}")
        webbrowser.open(PRICING_MONKEY_URL, new=2)
        time.sleep(WAIT_FOR_BROWSER_TO_OPEN)
        
        # Step 2: Navigate with keyboard shortcuts
        logger.debug(f"Navigating with {NUM_TABS} TAB presses")
        for i in range(NUM_TABS):
            send_keys('{TAB}', pause=KEY_PRESS_PAUSE)
        
        # Step 3: Press DOWN once to move to first data row
        logger.debug("Pressing DOWN arrow to reach first data row")
        send_keys('{DOWN}', pause=KEY_PRESS_PAUSE)
        
        # Step 4: Select rows with SHIFT+DOWN
        logger.debug(f"Selecting {NUM_DOWN_ROWS} rows with SHIFT+DOWN")
        send_keys(f'+{{DOWN {NUM_DOWN_ROWS}}}', pause=KEY_PRESS_PAUSE)
        
        # Step 5: Extend selection to capture all 9 columns
        logger.debug(f"Extending selection to {NUM_RIGHT_COLUMNS} columns with SHIFT+RIGHT")
        send_keys(f'+{{RIGHT {NUM_RIGHT_COLUMNS}}}', pause=KEY_PRESS_PAUSE)
        
        # Step 6: Wait for cells to render
        logger.debug(f"Waiting {WAIT_FOR_CELL_RENDERING} seconds for cell rendering")
        time.sleep(WAIT_FOR_CELL_RENDERING)
        
        # Step 7: Copy the extended data
        logger.debug("Copying selected data with CTRL+C")
        send_keys('^c', pause=KEY_PRESS_PAUSE)
        time.sleep(WAIT_FOR_COPY_OPERATION)
        
        # Step 8: Get clipboard content
        clipboard_content = pyperclip.paste()
        logger.debug(f"Clipboard content retrieved, length: {len(clipboard_content)} chars")
        
        # Step 9: Close browser tab
        logger.debug("Closing browser tab with CTRL+W")
        send_keys('^w', pause=KEY_PRESS_PAUSE)
        time.sleep(WAIT_FOR_BROWSER_CLOSE)
        
        # Step 10: Process clipboard into DataFrame
        logger.debug("Processing clipboard data into extended DataFrame")
        df = _process_extended_clipboard_data(clipboard_content)
        
        if df.empty:
            raise PMRetrievalError("Clipboard content could not be processed into valid DataFrame")
        
        logger.info(f"Successfully retrieved extended PM data: {len(df)} rows, {len(df.columns)} columns")
        return df
        
    except Exception as e:
        logger.error(f"Error retrieving extended PM data: {str(e)}", exc_info=True)
        raise PMRetrievalError(f"Failed to retrieve extended PM data: {str(e)}")


def _process_extended_clipboard_data(clipboard_content):
    """
    Process clipboard content into DataFrame with extended column set.
    
    Args:
        clipboard_content (str): Raw clipboard content from PM
        
    Returns:
        pd.DataFrame: Structured DataFrame with 9 columns for risk analysis
    """
    try:
        lines = clipboard_content.strip().split('\n')
        logger.debug(f"Processing {len(lines)} lines from clipboard")
        
        if len(lines) < 2:
            logger.warning(f"Insufficient data lines: {len(lines)}")
            
        data = [line.split('\t') for line in lines]
        df = pd.DataFrame(data)
        
        # Apply column names - handle variable column counts gracefully
        if len(df.columns) >= len(COLUMN_NAMES):
            df.columns = COLUMN_NAMES + [f"Extra_Col_{i}" for i in range(len(COLUMN_NAMES), len(df.columns))]
        else:
            df.columns = COLUMN_NAMES[:len(df.columns)]
            logger.warning(f"DataFrame has fewer columns than expected: {len(df.columns)} vs {len(COLUMN_NAMES)}")
        
        # Clean up data
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].str.replace('\r', '').replace('', pd.NA)
        
        # Convert numeric columns
        numeric_columns = ['Trade Amount', 'Strike', 'DV01 Gamma', 'Vega', 'Theta']
        for col in numeric_columns:
            if col in df.columns:
                try:
                    df[col] = df[col].astype(str).str.replace(',', '').str.strip()
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    logger.debug(f"Converted {col} to numeric")
                except Exception as e:
                    logger.warning(f"Error converting {col} to numeric: {e}")
        
        # Handle percentage column
        if '%Delta' in df.columns:
            try:
                df['%Delta'] = df['%Delta'].astype(str).str.replace('%', '').str.strip()
                df['%Delta'] = pd.to_numeric(df['%Delta'], errors='coerce') / 100
                logger.debug("Converted %Delta to decimal format")
            except Exception as e:
                logger.warning(f"Error converting %Delta: {e}")
        
        return df
        
    except Exception as e:
        logger.error(f"Error processing extended clipboard data: {e}", exc_info=True)
        return pd.DataFrame({'error': [f"Failed to process data: {str(e)}"]})


if __name__ == "__main__":
    # Test the extended retrieval
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    
    try:
        data = get_extended_pm_data()
        if not data.empty:
            logger.info(f"Retrieved data shape: {data.shape}")
            logger.info("\nFirst 3 rows:")
            print(data.head(3).to_string())
            logger.info(f"\nColumn types:")
            for col in data.columns:
                logger.info(f"{col}: {data[col].dtype}")
        else:
            logger.warning("Retrieved empty DataFrame")
    except PMRetrievalError as e:
        logger.error(f"Retrieval failed: {e}") 