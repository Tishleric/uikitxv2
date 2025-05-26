"""
pMoneySimpleRetrieval - Simple data retrieval script for Pricing Monkey

This module automates browser interactions to collect a specific set of data
from Pricing Monkey and parse it into a structured DataFrame.
"""

import time
import webbrowser
import pandas as pd
import pyperclip
import logging
import io
import datetime
import csv
import re
import os
import pytz
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

# SOD CSV Headers and Constants
SOD_HEADERS = ["ACCOUNT", "UNDERLYING", "ASSET", "RUN_DATE", "PRODUCT_CODE", 
               "LONG_SHORT", "PUT_CALL", "STRIKE_PRICE", "QUANTITY", "EXPIRE_DATE", 
               "LOT_SIZE", "PRICE_TODAY", "IS_AMERICAN"]
DEFAULT_ACCOUNT = "SHAH"
DEFAULT_UNDERLYING = "ZN"
DEFAULT_FUTURE_ASSET = "ZN"
DEFAULT_FUTURE_LOT_SIZE = "1000.0"
DEFAULT_OUTPUT_FILENAME = "PricingMonkey_SOD_Output.csv"

# Regular expressions for parsing
OPTION_PATTERN = re.compile(r'(\d+(?:st|nd|rd|th))\s+.*?(put|call|put option|call option)', re.IGNORECASE)
EXPIRY_ORD_PATTERN = re.compile(r'(\d+)(?:st|nd|rd|th)')

class PMSimpleRetrievalError(Exception):
    """Custom exception for Pricing Monkey Simple Retrieval operations."""
    pass

# Helper Functions for Data Transformation

def _determine_instrument_type(trade_description):
    """
    Determine if an instrument is a future or an option based on its description.
    
    Args:
        trade_description (str): The trade description from Pricing Monkey.
        
    Returns:
        str: "future" or "option"
    """
    if not isinstance(trade_description, str) or not trade_description.strip():
        # Default to future if description is missing
        return "future"
    
    # If it contains ordinals like "1st", "2nd" and mentions "put" or "call", it's an option
    match = OPTION_PATTERN.search(trade_description)
    if match:
        return "option"
    
    return "future"

def _get_option_asset_and_expiry_date(trade_description, current_est_dt):
    """
    Determine the asset code and expiry date for an option based on its description
    and the current date/time.
    
    Handles rolling expiries (Mon/Wed/Fri) with proper date calculation based on:
    - The option's ordinal number (1st, 2nd, 3rd, etc.)
    - The current date in US Eastern time
    - The 3 PM EST cutoff rule (if current time is past 3 PM EST on an expiry day, 
      that day doesn't count as an expiry)
    
    Args:
        trade_description (str): The trade description from Pricing Monkey.
        current_est_dt (datetime.datetime): Current datetime in US/Eastern timezone.
        
    Returns:
        tuple: (asset_code, expiry_date) where:
               - asset_code (str): "OZN" for Friday, "VY" for Monday, "WY" for Wednesday,
                 or empty string if can't determine.
               - expiry_date (datetime.date or None): Calculated expiry date or None if
                 can't determine.
    """
    logger.debug(f"Determining asset code for option description: '{trade_description}'")
    logger.debug(f"Current EST time: {current_est_dt}")
    
    if not isinstance(trade_description, str) or not trade_description.strip():
        logger.warning("Empty or invalid trade description for option asset code")
        return ("", None)
    
    # Extract ordinal number from description (1st, 2nd, 3rd, etc.)
    match = EXPIRY_ORD_PATTERN.search(trade_description)
    if not match:
        logger.warning(f"No expiry ordinal found in: '{trade_description}'")
        return ("", None)
    
    try:
        # Get the ordinal number
        ordinal_num = int(match.group(1))
        logger.debug(f"Found expiry ordinal number: {ordinal_num}")
        
        # Initialize date iteration variables
        target_expiry_date = None
        day_to_check = current_est_dt.date()
        expiries_found = 0
        
        # Handle 3 PM EST cutoff rule for the current day
        current_weekday = current_est_dt.weekday()  # 0=Mon, 1=Tue, ..., 6=Sun
        is_expiry_day = current_weekday in [0, 2, 4]  # Mon, Wed, Fri
        
        # If it's an expiry day and past 3 PM EST, start checking from tomorrow
        if is_expiry_day and current_est_dt.hour >= 15:
            logger.debug(f"Current time past 3 PM EST on {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][current_weekday]}, starting from tomorrow")
            day_to_check += datetime.timedelta(days=1)
        else:
            logger.debug(f"Starting date iteration from today: {day_to_check}")
        
        # Iterate through future dates to find the Nth valid expiry day
        max_days_to_check = 50  # Safety guard against infinite loops
        for _ in range(max_days_to_check):
            check_weekday = day_to_check.weekday()
            is_check_expiry_day = check_weekday in [0, 2, 4]  # Mon, Wed, Fri
            
            if is_check_expiry_day:
                # Skip if it's the current day and we've determined it's past cutoff
                if day_to_check == current_est_dt.date() and current_est_dt.hour >= 15 and is_expiry_day:
                    logger.debug(f"Skipping current day {day_to_check} as it's past 3 PM EST")
                else:
                    # Valid expiry day found
                    expiries_found += 1
                    logger.debug(f"Found expiry #{expiries_found}: {day_to_check} ({['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][check_weekday]})")
                    
                    # If this is the Nth expiry we're looking for, we're done
                    if expiries_found == ordinal_num:
                        target_expiry_date = day_to_check
                        break
            
            # Move to next day
            day_to_check += datetime.timedelta(days=1)
        
        # Determine asset code from the found expiry date
        if target_expiry_date is None:
            logger.error(f"Could not find the {ordinal_num}th expiry date within {max_days_to_check} days")
            return ("", None)
        
        # Map weekday to asset code
        target_weekday = target_expiry_date.weekday()
        if target_weekday == 0:  # Monday
            asset_code = "VY"
        elif target_weekday == 2:  # Wednesday
            asset_code = "WY"
        elif target_weekday == 4:  # Friday
            asset_code = "OZN"
        else:
            # Should not happen given our loop logic
            logger.error(f"Unexpected target weekday: {target_weekday}")
            return ("", target_expiry_date)
        
        logger.info(f"Assigned asset code '{asset_code}' for {ordinal_num}th expiry on {target_expiry_date} ({['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][target_weekday]})")
        return (asset_code, target_expiry_date)
        
    except (ValueError, IndexError) as e:
        logger.warning(f"Error parsing ordinal number: {str(e)}")
        return ("", None)

def _get_put_call_from_description(trade_description, instrument_type):
    """
    Extract put/call information from the trade description.
    
    Args:
        trade_description (str): The trade description from Pricing Monkey.
        instrument_type (str): "future" or "option".
        
    Returns:
        str: "P" for put, "C" for call, or empty string for futures.
    """
    if instrument_type != "option" or not isinstance(trade_description, str):
        return ""
    
    lower_desc = trade_description.lower()
    if 'put' in lower_desc:
        return "P"
    elif 'call' in lower_desc:
        return "C"
    
    return ""

def _format_date_for_sod(date_input):
    """
    Format a date into MM/DD/YYYY format for SOD file.
    
    Args:
        date_input: A date representation (datetime, pd.Timestamp, or string).
        
    Returns:
        str: Formatted date string or empty string if input is invalid.
    """
    if pd.isna(date_input) or date_input == "":
        return ""
    
    try:
        # Convert to datetime if it's a string
        if isinstance(date_input, str):
            # Log for debugging
            logger.debug(f"Parsing date string: '{date_input}'")
            
            # Handle PM format like "21-May-2025 14:00 Chicago"
            if "Chicago" in date_input:
                parts = date_input.split()
                if len(parts) >= 2:
                    date_part = parts[0]  # Extract just the date part
                    try:
                        # Try to parse with explicit format
                        date_obj = datetime.datetime.strptime(date_part, "%d-%b-%Y").date()
                        logger.debug(f"Successfully parsed Chicago date: {date_obj}")
                        return date_obj.strftime('%m/%d/%Y')
                    except ValueError:
                        logger.debug(f"Failed to parse Chicago date with explicit format")
            
            # Try different formats
            for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d-%b-%Y', '%d %b %Y']:
                try:
                    date_obj = datetime.datetime.strptime(date_input.strip(), fmt).date()
                    logger.debug(f"Parsed date '{date_input}' with format '{fmt}': {date_obj}")
                    return date_obj.strftime('%m/%d/%Y')
                except ValueError:
                    continue
            
            # If none of the above formats worked, try pandas
            logger.debug(f"Trying pandas date parsing for: '{date_input}'")
            date_obj = pd.to_datetime(date_input, errors='coerce')
            if pd.isna(date_obj):
                logger.warning(f"Failed to parse date: '{date_input}'")
                return ""
            return date_obj.strftime('%m/%d/%Y')
            
        # If it's already a datetime or pandas Timestamp
        elif isinstance(date_input, (datetime.date, datetime.datetime, pd.Timestamp)):
            return date_input.strftime('%m/%d/%Y')
        
        return ""
    except Exception as e:
        logger.warning(f"Error formatting date {date_input}: {str(e)}")
        return ""

def _parse_pm_price_to_decimal(price_input, instrument_type):
    """
    Parse a price string from Pricing Monkey to a decimal value.
    
    Args:
        price_input (str): The price string (e.g., "110-12" or "0-8").
        instrument_type (str): "future" or "option".
        
    Returns:
        float or None: The parsed decimal price or None if parsing fails.
    """
    if pd.isna(price_input) or price_input == "":
        return None
    
    try:
        # Check if it's already a numeric value
        try:
            price_val = float(price_input)
            return price_val
        except (ValueError, TypeError):
            pass
        
        # Try handle-tick format (110-12 or 0-8)
        if isinstance(price_input, str) and '-' in price_input:
            parts = price_input.split('-')
            if len(parts) == 2:
                handle = float(parts[0].strip())
                
                # Check if ticks part has a fractional component
                ticks_part = parts[1].strip()
                if '.' in ticks_part:
                    ticks_parts = ticks_part.split('.')
                    ticks = float(ticks_parts[0])
                    fraction = float('0.' + ticks_parts[1])
                else:
                    ticks = float(ticks_part)
                    fraction = 0.0
                
                # For futures: 32nds, for options: 64ths
                divisor = 32.0 if instrument_type == "future" else 64.0
                return handle + (ticks + fraction) / divisor
        
        # If all parsing attempts fail
        return None
    except Exception as e:
        logger.warning(f"Error parsing price {price_input}: {str(e)}")
        return None

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
        pd.DataFrame: DataFrame with Trade Amount, Trade Description, and Strike columns
        
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

def transform_df_to_sod_format(input_df):
    """
    Transform the raw DataFrame from Pricing Monkey into SOD format.
    
    Args:
        input_df (pd.DataFrame): The raw DataFrame from get_simple_data().
        
    Returns:
        list: A list of lists, where each inner list represents a row for the SOD CSV.
    """
    if input_df.empty:
        logger.warning("Cannot transform empty DataFrame to SOD format")
        return []
    
    logger.debug("Transforming DataFrame to SOD format")
    
    # Get current date for RUN_DATE
    run_date_str = _format_date_for_sod(datetime.datetime.now().date())
    
    # Initialize the output rows list
    sod_rows = []
    
    # Process each row in the input DataFrame
    for idx, row in input_df.iterrows():
        try:
            # Extract data from the row
            trade_amount_str = str(row.get("Trade Amount", ""))
            trade_description = str(row.get("Trade Description", ""))
            strike_str = str(row.get("Strike", ""))
            expiry_date_str = str(row.get("Expiry Date", ""))
            price_str = str(row.get("Price", ""))
            
            # Convert trade amount to numeric
            try:
                trade_amount = pd.to_numeric(trade_amount_str.replace(',', ''), errors='coerce')
                if pd.isna(trade_amount):
                    trade_amount = 0
            except:
                trade_amount = 0
            
            # Determine instrument type
            instrument_type = _determine_instrument_type(trade_description)
            logger.debug(f"Row {idx}: Determined instrument type: {instrument_type} for '{trade_description}'")
            
            # ACCOUNT: Always "SHAH"
            account = DEFAULT_ACCOUNT
            
            # UNDERLYING: Always "ZN"
            underlying = DEFAULT_UNDERLYING
            
            # ASSET
            if instrument_type == "future":
                asset = DEFAULT_FUTURE_ASSET
                logger.info(f"Row {idx}: Using default future asset: {asset}")
            else:
                # Get current EST time for accurate expiry determination
                current_est_dt = datetime.datetime.now(pytz.timezone('US/Eastern'))
                asset, calculated_expiry = _get_option_asset_and_expiry_date(trade_description, current_est_dt)
                logger.info(f"Row {idx}: Assigned option asset code: '{asset}' for '{trade_description}'")
                logger.debug(f"Row {idx}: Calculated expiry date: {calculated_expiry}, PM expiry date: {expiry_date_str}")
            
            # PRODUCT_CODE
            product_code = "FUTURE" if instrument_type == "future" else "FUTR-OP"
            
            # LONG_SHORT
            if trade_amount > 0:
                long_short = "L"
            elif trade_amount < 0:
                long_short = "S"
            else:
                long_short = ""
            
            # PUT_CALL
            put_call = _get_put_call_from_description(trade_description, instrument_type)
            
            # STRIKE_PRICE
            strike_price = strike_str if instrument_type == "option" else ""
            
            # QUANTITY (absolute value)
            quantity = abs(trade_amount)
            quantity_str = f"{quantity:.1f}" if instrument_type == "future" else str(int(quantity))
            
            # EXPIRE_DATE
            expire_date = _format_date_for_sod(expiry_date_str)
            
            # LOT_SIZE
            lot_size = DEFAULT_FUTURE_LOT_SIZE if instrument_type == "future" else ""
            
            # PRICE_TODAY
            decimal_price = _parse_pm_price_to_decimal(price_str, instrument_type)
            price_today = str(decimal_price) if decimal_price is not None else ""
            
            # IS_AMERICAN
            is_american = "Y" if instrument_type == "option" else ""
            
            # Create the SOD row
            sod_row = [
                account, underlying, asset, run_date_str, product_code,
                long_short, put_call, strike_price, quantity_str, expire_date,
                lot_size, price_today, is_american
            ]
            
            sod_rows.append(sod_row)
            
        except Exception as e:
            logger.error(f"Error processing row {idx}: {str(e)}", exc_info=True)
    
    logger.info(f"Transformed {len(sod_rows)} rows to SOD format")
    return sod_rows

def save_sod_to_csv(sod_data_rows, filename=DEFAULT_OUTPUT_FILENAME):
    """
    Save the SOD data to a CSV file.
    
    Args:
        sod_data_rows (list): A list of lists, where each inner list represents a row for the SOD CSV.
        filename (str): The output filename.
        
    Returns:
        str: The full path to the saved file, or empty string if save failed.
    """
    if not sod_data_rows:
        logger.warning("No SOD data to save")
        return ""
    
    try:
        # Determine the output path (project root directory)
        output_path = os.path.abspath(filename)
        logger.debug(f"Saving SOD data to {output_path}")
        
        with open(output_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write headers
            writer.writerow(SOD_HEADERS)
            
            # Write data rows
            for row in sod_data_rows:
                writer.writerow(row)
        
        logger.info(f"Successfully saved SOD data to {output_path}")
        return output_path
    
    except Exception as e:
        logger.error(f"Error saving SOD data to CSV: {str(e)}", exc_info=True)
        return ""

if __name__ == "__main__":
    # Setup basic logging for standalone use
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    
    logger.info("Running pMoneySimpleRetrieval.py in standalone mode")
    
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
            
            # Transform to SOD format and save to CSV
            try:
                logger.info("\nTransforming data to SOD format...")
                sod_data = transform_df_to_sod_format(retrieved_data)
                
                if sod_data:
                    # Save to CSV
                    csv_path = save_sod_to_csv(sod_data)
                    if csv_path:
                        logger.info(f"SOD data successfully saved to: {csv_path}")
                        
                        # Display the first few rows of SOD data
                        logger.info(f"\nFirst {min(5, len(sod_data))} rows of SOD data:")
                        for i, row in enumerate(sod_data[:5]):
                            print(f"Row {i+1}: {row}")
                    else:
                        logger.error("Failed to save SOD data to CSV")
                else:
                    logger.warning("No SOD data was generated from the transformation")
            except Exception as e:
                logger.error(f"Error during transformation and saving: {str(e)}", exc_info=True)
        else:
            logger.warning("Retrieved empty DataFrame")
            
    except PMSimpleRetrievalError as e:
        logger.error(f"Data retrieval failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        
    logger.info("Standalone pMoneySimpleRetrieval.py test finished") 