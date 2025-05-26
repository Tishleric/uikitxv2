import datetime
import pandas as pd
import re
import logging

from futures_utils import get_optiondate_list, get_clean_option_dates_and_assets
from pricing_monkey_adapter import convert_handle_tick_to_decimal, interpret_pm_ordinal_to_index, parse_pm_expiry_date

logger = logging.getLogger(__name__)

def get_underlying(trade_description):
    if trade_description.startswith("RX"):
        return "FGBL"
    elif trade_description.startswith("TU"):    
        return "ZT"
    elif trade_description.startswith("FV"):
        return "ZF"
    elif trade_description.startswith("TY"):    
        return "ZN"
    elif trade_description.startswith("US"):    
        return "ZB"
    elif "10y note" in trade_description:
        return "ZN"

def get_asset_type(trade_description):
    for asset in ["RX", "TY", "FV", "TU", "US"]:
        if trade_description.startswith(asset):
            return 'FUTURE'
    return 'FUTR-OP'

def get_option_type(trade_description):
    return 'C' if 'call' in trade_description.lower() else 'P'

def add_trade_data(trade, set_dates, data):
    """
    Add trade data to the output data structure using direct PM values.
    
    Args:
        trade (dict): Trade dictionary with 'Trade Description', 'Trade Amount', 'Strike', 'Price'
        set_dates (list): DEPRECATED - no longer used, kept for backward compatibility
        data (dict): Output data structure to append to
    """
    trade_description = trade["Trade Description"]
    trade_amount = trade["Trade Amount"]
    pm_strike = trade.get("Strike", "")
    pm_price = trade.get("Price", "")
    pm_expiry_date = trade.get("Expiry Date", "")
    
    underlying = get_underlying(trade_description)
    asset_type = get_asset_type(trade_description)
    option_type = get_option_type(trade_description)
    run_date = datetime.date.today().strftime("%m/%d/%Y")

    long_short = 'L' if trade_amount > 0 else 'S'
    put_call = 'P' if option_type == 'P' else 'C'
    quantity = abs(trade_amount)
    
    lot_size = 1000  # Assuming a default lot size of 1000
    
    # Use PM price directly instead of closes lookup
    # Determine instrument type for proper price conversion (32nds vs 64ths)
    instrument_type = "future" if asset_type == 'FUTURE' else "option"
    price_decimal = convert_handle_tick_to_decimal(pm_price, instrument_type) if pm_price else None
    if price_decimal is None:
        logger.warning(f"Invalid price '{pm_price}' for trade: {trade_description}")
        price_decimal = ""
    
    if asset_type == 'FUTURE':
        put_call = ""
        # Use PM expiry date for futures
        expire_date = parse_pm_expiry_date(pm_expiry_date) if pm_expiry_date else ""
        asset = underlying
        american = ''
        # Futures have no strike price
        strike_price = ""
    else:
        # Use new clean asset logic
        list_of_dates, symbols, pm_shift_needed = get_clean_option_dates_and_assets()
        
        # Extract ordinal from trade description (1st, 2nd, 3rd, etc.)
        ordinal_match = re.search(r'(\d+(?:st|nd|rd|th))', trade_description)
        if ordinal_match:
            pm_ordinal = ordinal_match.group(1)
            asset_index = interpret_pm_ordinal_to_index(pm_ordinal, pm_shift_needed)
            
            if asset_index >= 0 and asset_index < len(symbols):
                expire_date = datetime.datetime.strptime(list_of_dates[asset_index], "%Y-%m-%d").strftime("%m/%d/%Y")
                asset = symbols[asset_index]
            else:
                # Invalid ordinal - use defaults
                expire_date = ""
                asset = underlying
                logger.warning(f"Invalid ordinal '{pm_ordinal}' in trade: {trade_description}")
        else:
            # No ordinal found - treat as future
            expire_date = ""
            asset = underlying
            logger.warning(f"No ordinal found in option trade: {trade_description}")
        
        american = 'Y'
        # Use PM strike directly for options
        strike_price = pm_strike if pm_strike else ""

    data["ACCOUNT"].append("SHAH")
    data["UNDERLYING"].append(underlying)
    data["ASSET"].append(asset)
    data["RUN_DATE"].append(run_date)
    data["PRODUCT_CODE"].append(asset_type)
    data["LONG_SHORT"].append(long_short)
    data["PUT_CALL"].append(put_call)
    data["STRIKE_PRICE"].append(strike_price)
    data["QUANTITY"].append(quantity)
    data["EXPIRE_DATE"].append(expire_date)
    data["LOT_SIZE"].append(lot_size)
    data["PRICE_TODAY"].append(price_decimal)
    data["IS_AMERICAN"].append(american)
    data["DESCRIPTION"].append(trade_description)

def process_trades(trade_data_input):
    """
    Process trades using external trade data with direct PM Strike and Price values.
    
    Args:
        trade_data_input (list[dict]): List of trade dictionaries with 'Trade Description', 'Trade Amount', 'Strike', 'Price'
        
    Returns:
        pd.DataFrame: Processed trades DataFrame
    """
    header_fields = [
        "ACCOUNT",
        "UNDERLYING",
        "ASSET",
        "RUN_DATE",
        "PRODUCT_CODE",
        "LONG_SHORT",
        "PUT_CALL",
        "STRIKE_PRICE",
        "QUANTITY",
        "EXPIRE_DATE",
        "LOT_SIZE",
        "PRICE_TODAY",
        "IS_AMERICAN",
        "DESCRIPTION"
    ]
    
    data = {header_field: [] for header_field in header_fields}
    
    # Process each trade with clean logic - no more complex transformations
    for trade in trade_data_input:
        add_trade_data(trade, None, data)  # set_dates no longer needed
    
    return pd.DataFrame(data)

if __name__ == "__main__":
    header_fields = [
        "ACCOUNT",
        "UNDERLYING",
        "ASSET",
        "RUN_DATE",
        "PRODUCT_CODE",
        "LONG_SHORT",
        "PUT_CALL",
        "STRIKE_PRICE",
        "QUANTITY",
        "EXPIRE_DATE",
        "LOT_SIZE",
        "PRICE_TODAY",
        "IS_AMERICAN",
        "DESCRIPTION"
    ]
    # Test data for backward compatibility
    data = {header_field: [] for header_field in header_fields}
    trade_data = [
        {"Trade Description": "TYM5", "Trade Amount": 500, "Strike": "", "Price": "", "Expiry Date": "18-Jun-2025 14:00 Chicago"},
        {"Trade Description": "1st 10y note 25 out put", "Trade Amount": -100, "Strike": "", "Price": "", "Expiry Date": ""},
        {"Trade Description": "1st 10y note 50 out put", "Trade Amount": 200, "Strike": "", "Price": "", "Expiry Date": ""},
        {"Trade Description": "2nd 10y note 25 out put", "Trade Amount": 150, "Strike": "", "Price": "", "Expiry Date": ""},
        {"Trade Description": "2nd 10y note 50 out put", "Trade Amount": 100, "Strike": "", "Price": "", "Expiry Date": ""},
        {"Trade Description": "2nd 10y note 100 out put", "Trade Amount": 200, "Strike": "", "Price": "", "Expiry Date": ""},
        {"Trade Description": "3rd 10y note 25 out put", "Trade Amount": 50, "Strike": "", "Price": "", "Expiry Date": ""},
        {"Trade Description": "3rd 10y note 75 out put", "Trade Amount": 100, "Strike": "", "Price": "", "Expiry Date": ""},
        {"Trade Description": "RXM5", "Trade Amount": 10, "Strike": "", "Price": "", "Expiry Date": "15-Jun-2025 14:00 Chicago"}
    ]

    # Use new clean processing - no more complex transformations
    for trade in trade_data:
        add_trade_data(trade, None, data)
    print(pd.DataFrame(data))

    pd.DataFrame(data).drop(columns=["DESCRIPTION"]).to_csv("actant.csv", index=False)




