import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import os
import sys
import pandas as pd
import requests
import json
import math # For rounding prices
import re   # For regex parsing of spot price
import time
import webbrowser
import pyperclip
import sqlite3
from pywinauto.keyboard import send_keys
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

# --- Import components from package ---
try:
    from components import DataTable, Button, Grid
    from components.themes import default_theme
    from trading.ladder import decimal_to_tt_bond_format, csv_to_sqlite_table, query_sqlite_table
    from trading.tt_api import (
        TTTokenManager, 
        TT_API_KEY, TT_API_SECRET, TT_SIM_API_KEY, TT_SIM_API_SECRET,
        APP_NAME, COMPANY_NAME, ENVIRONMENT, TOKEN_FILE
    )
    print("Successfully imported components, theme, price_formatter, and TT REST API tools")
except ImportError as e:
    print(f"Error importing components: {e}")
    sys.exit(1)
# --- End Imports ---

# --- Initialize Dash App ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Scenario Ladder"

# Define data directory path
ladderTest_dir = os.path.dirname(os.path.abspath(__file__))  # Keep for backward compatibility

# Use paths relative to project root (for data files that have been moved)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
MOCK_DATA_FILE = os.path.join(project_root, "data", "input", "ladder", "my_working_orders_response.json")
MOCK_SPOT_PRICE_STR = "110-08.5" # Mock spot price in Pricing Monkey dash-decimal format

# --- Actant Data SQLite Constants ---
ACTANT_CSV_FILE = os.path.join(project_root, "data", "input", "sod", "SampleSOD.csv")
ACTANT_DB_FILEPATH = os.path.join(project_root, "data", "output", "ladder", "actant_data.db")
ACTANT_TABLE_NAME = "actant_sod_fills"

# --- PnL Calculation Constants ---
# One basis point (BP) equals 2 display ticks, where each display tick is 1/32
BP_DECIMAL_PRICE_CHANGE = 0.0625  # 2 * (1/32) = 1/16 = 0.0625
DOLLARS_PER_BP = 62.5  # $62.5 per basis point

# Pricing Monkey constants
PM_URL = "https://pricingmonkey.com/b/e9172aaf-2cb4-4f2c-826d-92f57d3aea90"
PM_WAIT_FOR_BROWSER_OPEN = 3.0
PM_WAIT_BETWEEN_ACTIONS = 0.5
PM_WAIT_FOR_COPY = 1.0
PM_KEY_PRESS_PAUSE = 0.1

# --- Constants ---
TT_API_BASE_URL = "https://ttrestapi.trade.tt"
PRICE_INCREMENT_DECIMAL = 1.0 / 64.0  # For ZN-like instruments
DATATABLE_ID = 'scenario-ladder-table'
MESSAGE_DIV_ID = 'scenario-ladder-message'
STORE_ID = 'scenario-ladder-store' # For triggering load and potentially storing state
USE_MOCK_DATA = False # Flag to switch between mock and live data

def parse_and_convert_pm_price(price_str):
    """
    Parse a price string from Pricing Monkey format "XXX-YY.ZZ" or "XXX-YY.ZZZ"
    and convert it to both decimal and special string format.
    
    Args:
        price_str (str): Price string from Pricing Monkey, e.g. "110-09.00" or "110-09.75"
        
    Returns:
        tuple: (decimal_price, special_string_price) or (None, None) if parsing fails
    """
    # Clean the string (trim whitespace, handle potential CR/LF)
    price_str = price_str.strip() if price_str else ""
    
    # Pattern for "XXX-YY.ZZ" or "XXX-YY.ZZZ" (allowing for 1, 2 or 3 decimal places)
    pattern = r"(\d+)-(\d{1,2})\.(\d{1,3})"
    match = re.match(pattern, price_str)
    
    if not match:
        print(f"Failed to parse price string: '{price_str}'")
        return None, None
        
    whole_points = int(match.group(1))
    thirty_seconds_part = int(match.group(2))
    fractional_part_str = match.group(3)
    
    # Convert fractional part to its decimal value (e.g., "5" -> 0.5, "75" -> 0.75, "125" -> 0.125)
    # This handles cases like ".5" and ".50" both correctly evaluating to 0.5 for calculation
    fraction_as_decimal = float("0." + fractional_part_str)
    
    # Convert to decimal price: whole_points + (thirty_seconds_part + fraction_as_decimal) / 32.0
    decimal_price = whole_points + (thirty_seconds_part + fraction_as_decimal) / 32.0
    
    # Generate special string format
    # For exact 32nds (e.g. "110-09.00" or "110-09.0"), use format "110'090"
    # For fractional 32nds (e.g. "110-09.75" or "110-09.5"), use format "110'0975" or "110'095"
    if fractional_part_str == "00" or fractional_part_str == "0":
        special_string_price = f"{whole_points}'{thirty_seconds_part:02d}0"
    else:
        special_string_price = f"{whole_points}'{thirty_seconds_part:02d}{fractional_part_str}"
    
    print(f"Converted '{price_str}' to decimal: {decimal_price}, special format: '{special_string_price}'")
    return decimal_price, special_string_price

def convert_tt_special_format_to_decimal(price_str):
    """
    Convert a TT special string format price (e.g. "110'065") to decimal.
    
    Args:
        price_str (str): Price string in TT format, e.g. "110'065" or "110'0875"
        
    Returns:
        float: Decimal price or None if parsing fails
    """
    price_str = price_str.strip() if price_str else ""
    
    # Pattern for "XXX'YYZZ" format where YY is 32nds and ZZ is optional fractional part
    pattern = r"(\d+)'(\d{2,4})"
    match = re.match(pattern, price_str)
    
    if not match:
        print(f"Failed to parse TT special format price: '{price_str}'")
        return None
        
    whole_points = int(match.group(1))
    fractional_str = match.group(2)
    
    if len(fractional_str) == 2:  # Just 32nds, no fraction (e.g., "110'08")
        thirty_seconds_part = int(fractional_str)
        fraction_part = 0
    elif len(fractional_str) == 3:  # 32nds with single-digit fraction (e.g., "110'085")
        thirty_seconds_part = int(fractional_str[0:2])
        fraction_part = int(fractional_str[2]) / 10.0
    elif len(fractional_str) == 4:  # 32nds with two-digit fraction (e.g., "110'0875")
        thirty_seconds_part = int(fractional_str[0:2])
        fraction_part = int(fractional_str[2:4]) / 100.0
    else:
        print(f"Unexpected fractional format: '{fractional_str}'")
        return None

    # Calculate decimal: whole_points + (thirty_seconds_part + fraction_part) / 32.0
    decimal_price = whole_points + (thirty_seconds_part + fraction_part) / 32.0
    
    print(f"Converted '{price_str}' to decimal: {decimal_price}")
    return decimal_price

def load_actant_zn_fills(csv_filepath):
    """
    Load ZN futures fill data from Actant CSV file.
    
    Args:
        csv_filepath (str): Path to the Actant CSV file
        
    Returns:
        list: List of dictionaries containing fill data with 'price' and 'qty' keys
    """
    print(f"Loading Actant ZN fills from: {csv_filepath}")
    try:
        fills_df = pd.read_csv(csv_filepath)
        
        # Filter for ZN futures only
        zn_future_fills = fills_df[(fills_df['ASSET'] == 'ZN') & 
                                   (fills_df['PRODUCT_CODE'] == 'FUTURE')]
        
        if zn_future_fills.empty:
            print("No ZN futures found in Actant data")
            return []
            
        print(f"Found {len(zn_future_fills)} ZN future fills in Actant data")
        
        # Process each fill
        processed_fills = []
        for _, row in zn_future_fills.iterrows():
            # Convert price from TT special format to decimal
            price_str = row.get('PRICE_TODAY')
            price = convert_tt_special_format_to_decimal(price_str)
            
            if price is None:
                print(f"Skipping fill with invalid price: {price_str}")
                continue
                
            # Get quantity and adjust sign based on long/short
            quantity = float(row.get('QUANTITY', 0))
            if pd.isna(quantity) or quantity == 0:
                print(f"Skipping fill with invalid quantity: {quantity}")
                continue
                
            side = row.get('LONG_SHORT', '')
            if side == 'S':  # Short position
                quantity = -quantity
            
            processed_fills.append({
                'price': price,
                'qty': int(quantity)  # Ensure quantity is an integer
            })
            
        print(f"Processed {len(processed_fills)} valid ZN future fills")
        return processed_fills
        
    except Exception as e:
        print(f"Error loading Actant ZN fills: {e}")
        return []

def load_actant_zn_fills_from_db(db_filepath, table_name):
    """
    Load ZN futures fill data from SQLite database.
    
    Args:
        db_filepath (str): Path to the SQLite database file
        table_name (str): Name of the table containing fill data
        
    Returns:
        list: List of dictionaries containing fill data with 'price' and 'qty' keys
    """
    print(f"Loading Actant ZN fills from DB: {db_filepath}, table: {table_name}")
    
    try:
        if not os.path.exists(db_filepath):
            print(f"Actant DB file not found: {db_filepath}")
            return []
            
        # Query the database for all relevant columns
        columns = ["PRICE_TODAY", "QUANTITY", "LONG_SHORT", "ASSET", "PRODUCT_CODE"]
        query = f"SELECT {', '.join(columns)} FROM {table_name}"
        
        try:
            # Use the imported query_sqlite_table function if available
            df = query_sqlite_table(db_filepath, table_name, columns=columns)
        except (NameError, TypeError):
            # Fall back to direct SQLite connection if query_sqlite_table isn't available
            print("Falling back to direct SQLite connection")
            conn = sqlite3.connect(db_filepath)
            df = pd.read_sql_query(query, conn)
            conn.close()
        
        if df.empty:
            print(f"No data found in {table_name}")
            return []
            
        # Filter for ZN futures
        zn_future_fills = df[(df['ASSET'] == 'ZN') & (df['PRODUCT_CODE'] == 'FUTURE')]
        
        if zn_future_fills.empty:
            print("No ZN futures found in database")
            return []
            
        print(f"Found {len(zn_future_fills)} ZN future fills in database")
        
        # Process each fill
        processed_fills = []
        for _, row in zn_future_fills.iterrows():
            # Convert price from TT special format to decimal
            price_str = row.get('PRICE_TODAY')
            price = convert_tt_special_format_to_decimal(price_str)
            
            if price is None:
                print(f"Skipping fill with invalid price: {price_str}")
                continue
                
            # Get quantity and adjust sign based on long/short
            quantity = float(row.get('QUANTITY', 0))
            if pd.isna(quantity) or quantity == 0:
                print(f"Skipping fill with invalid quantity: {quantity}")
                continue
                
            side = row.get('LONG_SHORT', '')
            if side == 'S':  # Short position
                quantity = -quantity
            
            processed_fills.append({
                'price': price,
                'qty': int(quantity)  # Ensure quantity is an integer
            })
            
        print(f"Processed {len(processed_fills)} valid ZN future fills from database")
        return processed_fills
        
    except Exception as e:
        print(f"Error loading Actant ZN fills from DB: {e}")
        return []

def calculate_baseline_from_actant_fills(actant_fills, spot_decimal_price):
    """
    Calculate baseline position and P&L at spot price based on Actant fill data.
    
    Args:
        actant_fills (list): List of dictionaries with 'price' and 'qty' keys
        spot_decimal_price (float): Current spot price in decimal format
        
    Returns:
        dict: Dictionary with 'base_pos' and 'base_pnl' keys
    """
    if not actant_fills or spot_decimal_price is None:
        print("No fills or invalid spot price - using zero baseline")
        return {'base_pos': 0, 'base_pnl': 0.0}

    # Sort fills by price (ascending) to process them in sequence
    sorted_fills = sorted(actant_fills, key=lambda x: x['price'])
    
    current_position = 0
    realized_pnl = 0.0
    
    # Initialize evaluation price with the first fill price
    if sorted_fills:
        current_eval_price = sorted_fills[0]['price']
    else:
        return {'base_pos': 0, 'base_pnl': 0.0}
    
    print("\n--- Baseline P&L Calculation from Actant Fills ---")
    print(f"Starting price (first fill): {decimal_to_tt_bond_format(current_eval_price)} ({current_eval_price})")
    print(f"Target spot price: {decimal_to_tt_bond_format(spot_decimal_price)} ({spot_decimal_price})")
    
    for fill in sorted_fills:
        fill_price = fill['price']
        fill_qty = fill['qty']
        
        # P&L from price movement with current position
        price_movement = fill_price - current_eval_price
        if abs(price_movement) > 0.000001:  # Avoid floating point comparison issues
            bp_movement = price_movement / BP_DECIMAL_PRICE_CHANGE
            pnl_increment = bp_movement * DOLLARS_PER_BP * current_position
            realized_pnl += pnl_increment
            
            print(f"\nPosition before fill: {current_position}")
            print(f"Price movement: {current_eval_price} to {fill_price} = {price_movement:.7f}")
            print(f"BP movement: {price_movement:.7f} / {BP_DECIMAL_PRICE_CHANGE} = {bp_movement:.3f} BPs")
            print(f"P&L increment: {bp_movement:.3f} BPs * ${DOLLARS_PER_BP}/BP * {current_position} = ${pnl_increment:.2f}")
            print(f"Running P&L: ${realized_pnl:.2f}")
        
        # Update position with current fill
        current_position += fill_qty
        print(f"Fill executed: {'BUY' if fill_qty > 0 else 'SELL'} {abs(fill_qty)} @ {decimal_to_tt_bond_format(fill_price)}")
        print(f"New position after fill: {current_position}")
        
        # Update evaluation price for next iteration
        current_eval_price = fill_price
    
    # Calculate P&L adjustment from last fill to spot price
    price_movement_to_spot = spot_decimal_price - current_eval_price
    if abs(price_movement_to_spot) > 0.000001:  # Avoid floating point comparison issues
        bp_movement_to_spot = price_movement_to_spot / BP_DECIMAL_PRICE_CHANGE
        pnl_increment_to_spot = bp_movement_to_spot * DOLLARS_PER_BP * current_position
        realized_pnl += pnl_increment_to_spot
        
        print(f"\nFinal position: {current_position}")
        print(f"Price movement to spot: {current_eval_price} to {spot_decimal_price} = {price_movement_to_spot:.7f}")
        print(f"BP movement: {price_movement_to_spot:.7f} / {BP_DECIMAL_PRICE_CHANGE} = {bp_movement_to_spot:.3f} BPs")
        print(f"P&L increment to spot: {bp_movement_to_spot:.3f} BPs * ${DOLLARS_PER_BP}/BP * {current_position} = ${pnl_increment_to_spot:.2f}")
        print(f"Final P&L at spot: ${realized_pnl:.2f}")
    
    result = {
        'base_pos': current_position,
        'base_pnl': round(realized_pnl, 2)
    }
    print(f"\nBaseline Result: Position = {result['base_pos']}, P&L at spot = ${result['base_pnl']:.2f}")
    return result

# Initialize mock spot price by parsing the string format
MOCK_SPOT_DECIMAL_PRICE, MOCK_SPOT_SPECIAL_STRING_PRICE = parse_and_convert_pm_price(MOCK_SPOT_PRICE_STR)
if MOCK_SPOT_DECIMAL_PRICE is None:
    print(f"CRITICAL ERROR: Failed to parse MOCK_SPOT_PRICE_STR: {MOCK_SPOT_PRICE_STR}. Mock spot price will be None.")
else:
    print(f"Initialized Mock Spot Price: '{MOCK_SPOT_SPECIAL_STRING_PRICE}' (Decimal: {MOCK_SPOT_DECIMAL_PRICE})")

# --- App Layout ---
app.layout = dbc.Container([
    dcc.Store(id=STORE_ID, data={'initial_load_trigger': True}), # Trigger initial load
    dcc.Store(id='spot-price-store', data={
        'decimal_price': MOCK_SPOT_DECIMAL_PRICE if USE_MOCK_DATA and MOCK_SPOT_DECIMAL_PRICE is not None else None,
        'special_string_price': MOCK_SPOT_SPECIAL_STRING_PRICE if USE_MOCK_DATA and MOCK_SPOT_SPECIAL_STRING_PRICE is not None else None
    }), # Store for spot price
    dcc.Store(id='baseline-store', data={
        'base_pos': 0,
        'base_pnl': 0.0
    }), # Store for baseline position/P&L from Actant fills
    html.H2("Scenario Ladder", style={"textAlign": "center", "color": "#18F0C3", "marginBottom": "20px"}),
    dbc.Row([
        dbc.Col(
            Button(id="refresh-data-button", label="Refresh Data", theme=default_theme).render(),
            width={"size": 4, "offset": 4},
            className="mb-3 d-flex justify-content-center",
        ),
    ]),
    html.Div(id='baseline-display', style={"textAlign": "center", "color": "#18F0C3", "marginBottom": "10px"}),
    html.Div(id='spot-price-error-div', style={"textAlign": "center", "color": "red", "marginBottom": "10px"}),
    html.Div(id=MESSAGE_DIV_ID, children="Loading working orders...", style={"textAlign": "center", "color": "white", "marginBottom": "20px"}),
    html.Div(
        id=f"{DATATABLE_ID}-wrapper",
        children=[
            Grid(
                id="scenario-ladder-grid",
                children=[
                    DataTable(
                        id=DATATABLE_ID,
                        columns=[
                            {'name': 'Working Qty', 'id': 'my_qty', "type": "numeric"},
                            {'name': 'Price', 'id': 'price', "type": "text"},
                            {'name': 'Projected PnL', 'id': 'projected_pnl', "type": "numeric", "format": {"specifier": "$,.2f"}},
                            {'name': 'Pos', 'id': 'position_debug', "type": "numeric"},
                            {'name': 'Risk', 'id': 'risk', "type": "numeric"},
                            {'name': 'Breakeven', 'id': 'breakeven', "type": "numeric", "format": {"specifier": ".2f"}}
                        ],
                data=[], # Start with no data
                theme=default_theme,
                style_cell={
                    'backgroundColor': 'black', 'color': 'white', 'font-family': 'monospace',
                    'fontSize': '12px', 'height': '22px', 'maxHeight': '22px', 'minHeight': '22px',
                    'width': '16.66%', 'textAlign': 'center', 'padding': '0px', 'margin': '0px', 'border': '1px solid #444'
                },
                style_header={
                    'backgroundColor': '#333333', 'color': 'white', 'height': '28px',
                    'padding': '0px', 'textAlign': 'center', 'fontWeight': 'bold', 'border': '1px solid #444'
                },
                style_data_conditional=[
                    {
                        'if': {
                            'filter_query': '{working_qty_side} = "1"', # Buy side
                            'column_id': 'my_qty'
                        },
                        'color': '#1E88E5'  # Blue
                    },
                    {
                        'if': {
                            'filter_query': '{working_qty_side} = "2"', # Sell side
                            'column_id': 'my_qty'
                        },
                        'color': '#E53935'  # Red
                    },
                    {
                        'if': {
                            'filter_query': '{is_exact_spot} = 1',
                            'column_id': 'price'
                        },
                        'backgroundColor': '#228B22',  # ForestGreen
                        'color': 'white'
                    },
                    {
                        'if': {
                            'filter_query': '{is_below_spot} = 1',
                            'column_id': 'price'
                        },
                        'borderBottom': '2px solid #228B22'  # Green bottom border
                    },
                    {
                        'if': {
                            'filter_query': '{is_above_spot} = 1',
                            'column_id': 'price'
                        },
                        'borderTop': '2px solid #228B22'  # Green top border
                    },
                    {
                        'if': {
                            'filter_query': '{projected_pnl} > 0',
                            'column_id': 'projected_pnl'
                        },
                        'color': '#4CAF50'  # Green for positive PnL
                    },
                    {
                        'if': {
                            'filter_query': '{projected_pnl} < 0',
                            'column_id': 'projected_pnl'
                        },
                        'color': '#F44336'  # Red for negative PnL
                    },
                    {
                        'if': {
                            'filter_query': '{position_debug} > 0',
                            'column_id': 'position_debug'
                        },
                        'color': '#1E88E5'  # Blue for long position
                    },
                    {
                        'if': {
                            'filter_query': '{position_debug} < 0',
                            'column_id': 'position_debug'
                        },
                        'color': '#E53935'  # Red for short position
                    },
                    {
                        'if': {
                            'filter_query': '{risk} > 0',
                            'column_id': 'risk'
                        },
                        'color': '#1E88E5'  # Blue for long position (risk)
                    },
                    {
                        'if': {
                            'filter_query': '{risk} < 0',
                            'column_id': 'risk'
                        },
                        'color': '#E53935'  # Red for short position (risk)
                    },
                    {
                        'if': {
                            'filter_query': '{breakeven} > 0',
                            'column_id': 'breakeven'
                        },
                        'color': '#4CAF50'  # Green for positive breakeven
                    },
                    {
                        'if': {
                            'filter_query': '{breakeven} < 0',
                            'column_id': 'breakeven'
                        },
                        'color': '#F44336'  # Red for negative breakeven
                    }
                ],
                page_size=100 # Adjust as needed, or make it dynamic
            ).render()
                ], # Close the Grid children list
                theme=default_theme, # Pass theme to Grid
            ).render() # Close and render the Grid
        ],
        style={'display': 'none'} # Initially hidden until data loads or message changes
    )
], fluid=True, style={"backgroundColor": "black", "padding": "10px", "minHeight": "100vh"})

print("Dash layout defined for Scenario Ladder")

# --- Callback to Fetch and Process Orders ---
@app.callback(
    Output(DATATABLE_ID, 'data'),
    Output(f"{DATATABLE_ID}-wrapper", 'style'),
    Output(MESSAGE_DIV_ID, 'children'),
    Output(MESSAGE_DIV_ID, 'style'),
    Output('baseline-store', 'data'),
    Output('baseline-display', 'children'),
    Input(STORE_ID, 'data'),
    Input('spot-price-store', 'data'), # Add spot price store as input
    Input('refresh-data-button', 'n_clicks'), # Add refresh button as input
    State(DATATABLE_ID, 'data'),      # Add State for current table data
    State('baseline-store', 'data')   # Add State for baseline data
)
def load_and_display_orders(store_data, spot_price_data, n_clicks, current_table_data, baseline_data):
    print("Callback triggered: load_and_display_orders")
    triggered_input_info = dash.callback_context.triggered[0]
    context_id = triggered_input_info['prop_id']
    
    # Handle different trigger sources
    # 1. If triggered by the refresh button or initial load, do a full data refresh
    # Note: When app first loads, context_id is '.' with no specific component
    is_initial_app_load = (context_id == '.')
    is_store_trigger = (context_id == f'{STORE_ID}.data')
    
    # Full refresh needed if:
    # - Button clicked, OR
    # - Initial app load with initial_load_trigger, OR
    # - Store data trigger with initial_load_trigger
    full_refresh_needed = (
        context_id == 'refresh-data-button.n_clicks' or
        (is_initial_app_load and store_data and store_data.get('initial_load_trigger')) or
        (is_store_trigger and store_data and store_data.get('initial_load_trigger'))
    )
    
    # Log the current trigger context for debugging
    print(f"Trigger context: '{context_id}', Initial load: {is_initial_app_load}, Full refresh needed: {full_refresh_needed}")
    
    # 2. If triggered only by spot price update, just update spot indicators on existing data
    if context_id == 'spot-price-store.data' and spot_price_data and not full_refresh_needed:
        # Use current_table_data from State
        if current_table_data and len(current_table_data) > 0:
            print(f"Spot price update only. current_table_data has {len(current_table_data)} rows.")
            # Use existing baseline data if available
            base_pos = baseline_data.get('base_pos', 0) if baseline_data else 0
            base_pnl = baseline_data.get('base_pnl', 0.0) if baseline_data else 0.0
            updated_data = update_data_with_spot_price(current_table_data, spot_price_data, base_pos, base_pnl)
            # No need to update baseline on spot price change only
            return updated_data, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        else:
            # Table not populated yet, or empty. Let the full load logic run if initial_load_trigger is set.
            print("Spot price update, but current_table_data is empty. Letting full load proceed.")
    
    # If not an initial load or refresh button click, don't proceed with full refresh
    if not full_refresh_needed:
        print("Callback skipped: not triggered by initial load or refresh button")
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        
    # Log the trigger
    if context_id == 'refresh-data-button.n_clicks':
        print(f"Full refresh triggered by button click ({n_clicks})")
    elif is_initial_app_load:
        print("Full refresh triggered by initial app load (context_id='.')")
    elif is_store_trigger:
        print(f"Full refresh triggered by store update with initial_load_trigger={store_data.get('initial_load_trigger')}")
    else:
        print(f"Full refresh triggered by unknown source: {context_id}")

    orders_data = []
    error_message_str = ""

    # --- Extract Spot Price Consistently (Step 3a of Plan v2) ---
    spot_decimal_val = None
    if spot_price_data and 'decimal_price' in spot_price_data:
        spot_decimal_val = spot_price_data.get('decimal_price')
        if spot_decimal_val is not None:
            print(f"Extracted spot_decimal_val: {spot_decimal_val}")
        else:
            print("spot_price_data present, but decimal_price is None.")
    else:
        print("spot_price_data is None or does not contain 'decimal_price'.")

    if USE_MOCK_DATA:
        print(f"Using mock data from: {MOCK_DATA_FILE}")
        try:
            with open(MOCK_DATA_FILE, 'r') as f:
                api_response = json.load(f)
            orders_data = api_response.get('orders', [])
            if not orders_data and isinstance(api_response, list): # Handle if root is a list
                 orders_data = api_response
            print(f"Loaded {len(orders_data)} orders from mock file.")
        except Exception as e:
            error_message_str = f"Error loading mock data: {e}"
            print(error_message_str)
            orders_data = [] # Ensure it's a list
    else:
        print("Fetching live data from TT API...")
        try:
            token_manager = TTTokenManager(
                api_key=TT_API_KEY if USE_MOCK_DATA else TT_SIM_API_KEY,
                api_secret=TT_API_SECRET if USE_MOCK_DATA else TT_SIM_API_SECRET,
                app_name=APP_NAME,
                company_name=COMPANY_NAME,
                environment=ENVIRONMENT,
                token_file_base=TOKEN_FILE
            )
            token = token_manager.get_token()
            if not token:
                error_message_str = "Failed to acquire TT API token."
                print(error_message_str)
            else:
                service = "ttledger"
                endpoint = "/orders" # Fetches working orders by default
                url = f"{TT_API_BASE_URL}/{service}/{token_manager.env_path_segment}{endpoint}"
                
                request_id = token_manager.create_request_id()
                # Potentially add instrumentId filter here if needed, e.g. from tt_config or a new constant
                # params = {"requestId": request_id, "instrumentId": "YOUR_INSTRUMENT_ID_HERE"} 
                params = {"requestId": request_id} # For now, get all working orders
                
                headers = {
                    "x-api-key": token_manager.api_key,
                    "accept": "application/json",
                    "Authorization": f"Bearer {token}"
                }

                print(f"Making API request to {url} with params: {params}")
                response = requests.get(url, headers=headers, params=params, timeout=30)
                response.raise_for_status()
                
                api_response = response.json()
                orders_data = api_response.get('orders', [])
                if not orders_data and isinstance(api_response, list): orders_data = api_response
                print(f"Received {len(orders_data)} orders from API.")
                
                # Optionally save the live response for inspection
                # live_response_path = os.path.join(ladderTest_dir, "live_working_orders_response.json")
                # with open(live_response_path, 'w') as f:
                #     json.dump(api_response, f, indent=2)
                # print(f"Live response saved to {live_response_path}")

        except requests.exceptions.HTTPError as http_err:
            error_message_str = f"HTTP error fetching orders: {http_err} - {http_err.response.text if http_err.response else 'No response text'}"
            print(error_message_str)
        except Exception as e:
            error_message_str = f"Error fetching live orders: {e}"
            print(error_message_str)
        
        if error_message_str: # If API call failed, ensure orders_data is empty list
            orders_data = []

    # --- Process orders and build ladder ---
    ladder_table_data = []
    
    # Filter for relevant working orders (status '1') and valid price/qty
    # The mock data seems to be already filtered for working orders with status '1'
    processed_orders = []
    if isinstance(orders_data, list): # Ensure orders_data is a list before iterating
        for order in orders_data:
            if isinstance(order, dict) and \
               order.get('orderStatus') == '1' and \
               isinstance(order.get('price'), (int, float)) and \
               isinstance(order.get('leavesQuantity'), (int, float)) and \
               order.get('leavesQuantity') > 0 and \
               order.get('side') in ['1', '2']: # Ensure side is valid
                processed_orders.append({
                    'price': float(order['price']),
                    'qty': float(order['leavesQuantity']),
                    'side': order.get('side') 
                })
    print(f"Processed {len(processed_orders)} relevant working orders.")

    # --- Adjust Early Exit for "No working orders" (Step 3b of Plan v2) ---
    if not processed_orders and not error_message_str and spot_decimal_val is None:
        # No relevant orders found, no API error, AND no spot price available
        message_text = "No working orders or spot price found to display."
        print(message_text)
        message_style_visible = {'textAlign': 'center', 'color': 'orange', 'marginBottom': '20px', 'display': 'block'}
        table_style_hidden = {'display': 'none'}
        # Use existing baseline_results and baseline_display_text if computed, else defaults
        final_baseline_results = baseline_data if baseline_data else {'base_pos': 0, 'base_pnl': 0.0}
        final_baseline_display_text = "No Actant data available"
        return [], table_style_hidden, message_text, message_style_visible, final_baseline_results, final_baseline_display_text
    elif error_message_str and not processed_orders : # Prioritize API/load error message if it exists and no orders processed
        message_text = error_message_str
        print(f"Displaying error: {message_text}")
        message_style_visible = {'textAlign': 'center', 'color': 'red', 'marginBottom': '20px', 'display': 'block'} # Error in red
        table_style_hidden = {'display': 'none'}
        return [], table_style_hidden, message_text, message_style_visible
    elif not processed_orders and error_message_str: # Should be caught by above, but as a safeguard
        message_text = error_message_str
        print(f"Displaying error (safeguard): {message_text}")

    # Process Actant fill data to get baseline position and P&L
    actant_fills = []
    baseline_results = {'base_pos': 0, 'base_pnl': 0.0}
    baseline_display_text = "No Actant data available"
    
    try:
        # Step 1: Check if CSV exists and update the SQLite database
        if os.path.exists(ACTANT_CSV_FILE):
            try:
                # Check if csv_to_sqlite_table function is available
                if 'csv_to_sqlite_table' in globals() or 'csv_to_sqlite_table' in locals():
                    print(f"Updating SQLite DB from {ACTANT_CSV_FILE}...")
                    success = csv_to_sqlite_table(ACTANT_CSV_FILE, ACTANT_DB_FILEPATH, ACTANT_TABLE_NAME)
                    if success:
                        print(f"Successfully updated {ACTANT_TABLE_NAME} in {ACTANT_DB_FILEPATH}")
                    else:
                        print(f"Failed to update SQLite DB, will try direct CSV reading")
                        
                        # Fall back to direct CSV reading if SQLite update fails
                        if not os.path.exists(ACTANT_DB_FILEPATH):
                            print(f"SQLite DB not found after update attempt, falling back to direct CSV")
                            actant_fills = load_actant_zn_fills(ACTANT_CSV_FILE)
                else:
                    print("csv_to_sqlite_table function not available, using direct CSV reading")
                    actant_fills = load_actant_zn_fills(ACTANT_CSV_FILE)
            except Exception as e:
                print(f"Error updating SQLite DB: {e}, falling back to direct CSV reading")
                actant_fills = load_actant_zn_fills(ACTANT_CSV_FILE)
        else:
            print(f"Actant CSV file not found: {ACTANT_CSV_FILE}")
            
        # Step 2: If no fills loaded yet, try to read from SQLite if the DB file exists
        if not actant_fills and os.path.exists(ACTANT_DB_FILEPATH):
            try:
                print(f"Loading Actant data from SQLite DB {ACTANT_DB_FILEPATH}")
                actant_fills = load_actant_zn_fills_from_db(ACTANT_DB_FILEPATH, ACTANT_TABLE_NAME)
            except Exception as e:
                print(f"Error loading from SQLite DB: {e}")
                # Already tried or will try direct CSV reading if needed
            
        print(f"Loaded {len(actant_fills)} Actant ZN fills")
            
        # Step 3: Calculate baseline position and P&L if we have fills and spot price
        if spot_decimal_val is not None and actant_fills:
            # Calculate baseline position and P&L
            baseline_results = calculate_baseline_from_actant_fills(actant_fills, spot_decimal_val)
                
            # Prepare display text
            pos_str = f"Long {baseline_results['base_pos']}" if baseline_results['base_pos'] > 0 else \
                     f"Short {-baseline_results['base_pos']}" if baseline_results['base_pos'] < 0 else "FLAT"
            pnl_str = f"${baseline_results['base_pnl']:.2f}"
            baseline_display_text = f"Current Position: {pos_str}, Realized P&L @ Spot: {pnl_str}"
            print(f"Baseline from Actant: {baseline_display_text}")
        else:
            print("Either spot price or Actant fills not available for baseline calculation")
    except Exception as e:
        print(f"Error processing Actant data: {e}")
        baseline_display_text = f"Error processing Actant data: {str(e)}"
        
    if processed_orders or spot_decimal_val is not None:
        # --- Calculate Overall Raw Min/Max Prices (Step 3d of Plan v2) ---
        current_min_raw_price = None
        current_max_raw_price = None

        if processed_orders:
            order_prices = [
                float(o['price']) for o in processed_orders
                if isinstance(o.get('price'), (int, float)) and o.get('price') is not None
            ]
            if order_prices:  # Ensure list is not empty
                min_order_val = min(order_prices)
                max_order_val = max(order_prices)
                current_min_raw_price = min_order_val
                current_max_raw_price = max_order_val
                print(f"Min/Max from orders: {min_order_val}/{max_order_val}")

        if spot_decimal_val is not None:
            print(f"Considering spot_decimal_val for range: {spot_decimal_val}")
            if current_min_raw_price is None or spot_decimal_val < current_min_raw_price:
                current_min_raw_price = spot_decimal_val
            if current_max_raw_price is None or spot_decimal_val > current_max_raw_price:
                current_max_raw_price = spot_decimal_val
        
        print(f"Overall raw min/max before rounding: {current_min_raw_price}/{current_max_raw_price}")

        # If current_min_raw_price is still None, means no valid prices from orders and no spot price.
        # This should ideally not be reached if the parent 'if' condition is robust.
        # However, if it is, we can't proceed.
        if current_min_raw_price is None:
            print("No valid price data (orders or spot) to form ladder. Returning empty.")
            message_text = "No price data available to display ladder."
            message_style_visible = {'textAlign': 'center', 'color': 'orange', 'marginBottom': '20px', 'display': 'block'}
            table_style_hidden = {'display': 'none'}
            # Use existing baseline_results and baseline_display_text if computed, else defaults
            final_baseline_results = baseline_results if 'baseline_results' in locals() else {'base_pos': 0, 'base_pnl': 0.0}
            final_baseline_display_text = baseline_display_text if 'baseline_display_text' in locals() else "No Actant data"
            return [], table_style_hidden, message_text, message_style_visible, final_baseline_results, final_baseline_display_text

        # Round to nearest tick using current_min_raw_price and current_max_raw_price
        ladder_min_price = math.floor(current_min_raw_price / PRICE_INCREMENT_DECIMAL) * PRICE_INCREMENT_DECIMAL
        ladder_max_price = math.ceil(current_max_raw_price / PRICE_INCREMENT_DECIMAL) * PRICE_INCREMENT_DECIMAL
        
        print(f"Ladder min/max after initial rounding: {ladder_min_price}/{ladder_max_price}")

        # --- Add Padding (Step 3e of Plan v2) ---
        ladder_min_price -= PRICE_INCREMENT_DECIMAL
        ladder_max_price += PRICE_INCREMENT_DECIMAL

        # Re-round for precision after padding
        ladder_min_price = round(ladder_min_price / PRICE_INCREMENT_DECIMAL) * PRICE_INCREMENT_DECIMAL
        ladder_max_price = round(ladder_max_price / PRICE_INCREMENT_DECIMAL) * PRICE_INCREMENT_DECIMAL
        
        print(f"Ladder min/max after padding and re-rounding: {ladder_min_price}/{ladder_max_price}")
        
        # --- Ensure num_levels is Positive (Step 3f of Plan v2) ---
        num_levels = round((ladder_max_price - ladder_min_price) / PRICE_INCREMENT_DECIMAL) + 1
        if num_levels <= 0:
            num_levels = 1 # Ensure at least one level if rounding leads to non-positive
        
        print(f"Final Ladder Price Range: {decimal_to_tt_bond_format(ladder_min_price)} to {decimal_to_tt_bond_format(ladder_max_price)}, Levels: {num_levels}")

        current_price_level = ladder_max_price
        epsilon = PRICE_INCREMENT_DECIMAL / 100.0 # For float comparisons
        
        for _ in range(num_levels):
            formatted_price = decimal_to_tt_bond_format(current_price_level)
            my_qty_at_level = 0
            # Determine side for this level. Assumes all orders at one price level have the same side.
            # If multiple orders at the same price level, the side of the first one encountered will be used.
            # This should be fine as they are *my* working orders.
            side_at_level = "" 
            
            for order in processed_orders:
                if abs(order['price'] - current_price_level) < epsilon:
                    my_qty_at_level += order['qty']
                    if not side_at_level: # Capture side from the first order matching this price level
                        side_at_level = order['side']
            
            # Create the row data with spot price indicators
            row_data = {
                'price': formatted_price,
                'my_qty': int(my_qty_at_level) if my_qty_at_level > 0 else "", # Show int or empty
                'working_qty_side': side_at_level if my_qty_at_level > 0 else "", # Add side for styling
                'decimal_price_val': current_price_level, # Store the decimal price
                # Spot price indicators (default to 0, handled by update_data_with_spot_price)
                'is_exact_spot': 0,
                'is_below_spot': 0,
                # Spot price indicators (default to 0, handled by update_data_with_spot_price)
                'is_exact_spot': 0,
                'is_below_spot': 0,
                # Position and risk fields (will be calculated in update_data_with_spot_price)
                'position_debug': 0,
                'risk': 0,
                # Breakeven field (will be calculated in update_data_with_spot_price)
                'breakeven': 0,
            }
            
            ladder_table_data.append(row_data)
            current_price_level -= PRICE_INCREMENT_DECIMAL
            # Correct for potential floating point drift by re-calculating based on fixed increment
            current_price_level = round(current_price_level / PRICE_INCREMENT_DECIMAL) * PRICE_INCREMENT_DECIMAL

        # Apply spot price indicators to the ladder data if spot price is available
        if spot_price_data and spot_price_data.get('decimal_price') is not None: # Check key existence
            # Use baseline position and P&L for PnL projections
            ladder_table_data = update_data_with_spot_price(
                ladder_table_data, 
                spot_price_data, # This contains spot_decimal_val
                base_position=baseline_results['base_pos'],
                base_pnl=baseline_results['base_pnl']
            )
        
        print(f"Generated {len(ladder_table_data)} rows for the ladder.")
        message_text = "" # Clear message if table has data
        message_style_hidden = {'display': 'none'}
        table_style_visible = {'display': 'block', 'width': '600px', 'margin': 'auto'} # Ensure table is centered
        return ladder_table_data, table_style_visible, message_text, message_style_hidden, baseline_results, baseline_display_text
    else: # Should only be hit if not (processed_orders or spot_decimal_val is not None)
          # This means processed_orders is empty AND spot_decimal_val is None.
          # This case should have been caught by the modified early exit.
        # --- Review Final else Block Message (Step 3g of Plan v2) ---
        message_text = error_message_str if error_message_str else "No working orders or spot price available to display ladder."
        print(f"Final fallback: {message_text}")
        message_style_visible = {'textAlign': 'center', 'color': 'red' if error_message_str else 'white', 'marginBottom': '20px', 'display': 'block'}
        table_style_hidden = {'display': 'none'}
        empty_baseline = {'base_pos': 0, 'base_pnl': 0.0}
        # If baseline was calculated successfully earlier, use that display
        display_text = baseline_display_text if 'baseline_display_text' in locals() and baseline_display_text else "No position data available"
        return [], table_style_hidden, message_text, message_style_visible, empty_baseline, display_text



# --- Callback to Get Spot Price from Pricing Monkey ---
@app.callback(
    Output('spot-price-store', 'data'),
    Output('spot-price-error-div', 'children'),
    Input('refresh-data-button', 'n_clicks'),
    prevent_initial_call=True
)
def fetch_spot_price_from_pm(n_clicks):
    """
    Fetch spot price from Pricing Monkey using UI automation.
    Opens the Pricing Monkey URL, navigates through the UI using keyboard shortcuts,
    copies the price from the clipboard, and then closes the browser tab.
    
    When USE_MOCK_DATA is True, returns the mock spot price instead of
    fetching from Pricing Monkey.
    
    Args:
        n_clicks: Button click count
        
    Returns:
        dict: Spot price data with decimal and string representations
        str: Error message (if any)
    """
    if n_clicks is None or n_clicks == 0:
        raise PreventUpdate
    
    # If using mock data, return the mock spot price
    if USE_MOCK_DATA:
        print(f"Using mock spot price for refresh (button clicks: {n_clicks})")
        if MOCK_SPOT_DECIMAL_PRICE is not None:
            return {
                'decimal_price': MOCK_SPOT_DECIMAL_PRICE,
                'special_string_price': MOCK_SPOT_SPECIAL_STRING_PRICE
            }, ""  # Empty error message
        else:
            # This case should ideally not happen if parsing was successful at startup
            return {
                'decimal_price': None,
                'special_string_price': None
            }, "Error: Mock spot price not initialized."
    
    print(f"Fetching spot price from Pricing Monkey ({n_clicks} clicks)")
    
    try:
        # Open the Pricing Monkey URL
        print(f"Opening URL: {PM_URL}")
        webbrowser.open(PM_URL, new=2)
        time.sleep(PM_WAIT_FOR_BROWSER_OPEN)  # Wait for browser to open
        
        # Navigate to the target element using keyboard shortcuts
        print("Pressing TAB 10 times to navigate")
        send_keys('{TAB 10}', pause=PM_KEY_PRESS_PAUSE, with_spaces=True)
        time.sleep(PM_WAIT_BETWEEN_ACTIONS)
        
        print("Pressing DOWN to select price")
        send_keys('{DOWN}', pause=PM_KEY_PRESS_PAUSE)
        time.sleep(PM_WAIT_BETWEEN_ACTIONS)
        
        # Copy the value to clipboard
        print("Copying to clipboard")
        send_keys('^c', pause=PM_KEY_PRESS_PAUSE)
        time.sleep(PM_WAIT_FOR_COPY)
        
        # Get the clipboard content
        clipboard_content = pyperclip.paste()
        print(f"Clipboard content: '{clipboard_content}'")
        
        # Close the browser tab
        print("Closing browser tab")
        send_keys('^w', pause=PM_KEY_PRESS_PAUSE)
        time.sleep(PM_WAIT_BETWEEN_ACTIONS)
        
        # Process the clipboard content
        decimal_price, special_string_price = parse_and_convert_pm_price(clipboard_content)
        
        if decimal_price is None:
            error_msg = f"Failed to parse price from clipboard: '{clipboard_content}'"
            print(error_msg)
            return {'decimal_price': None, 'special_string_price': None}, error_msg
        
        # Return the parsed data
        return {
            'decimal_price': decimal_price,
            'special_string_price': special_string_price
        }, ""
        
    except Exception as e:
        error_msg = f"Error fetching spot price: {str(e)}"
        print(error_msg)
        return {'decimal_price': None, 'special_string_price': None}, error_msg

def update_data_with_spot_price(existing_data, spot_price_data, base_position=0, base_pnl=0.0):
    """
    Update existing ladder data with spot price indicators based on decimal comparison.
    Handles exact matches and midpoints (marking the top border of the base tick).
    
    Calculates Projected PnL based on:
    1. Starting with baseline position and P&L at the spot price from Actant fills
    2. Accumulating PnL based on position and price changes between consecutive price levels
    3. PnL at each level = PnL of previous level + (position * price change in basis points * $63)
    
    The position_debug field shows the accumulated position AFTER any working orders at that
    price level are executed. The projected_pnl uses the position BEFORE orders at the current
    row are executed (i.e., using the position resulting from all previous fills).
    
    Args:
        existing_data (list): Current DataTable data (list of dictionaries, each with 'decimal_price_val')
        spot_price_data (dict): Spot price data from spot-price-store (contains 'decimal_price')
        base_position (int): Starting position at spot price from Actant fills (default: 0)
        base_pnl (float): Starting P&L at spot price from Actant fills (default: 0.0)
        
    Returns:
        list: Updated DataTable data with spot price indicators and PnL values
    """
    if not existing_data or not spot_price_data:
        print("update_data_with_spot_price: No existing_data or spot_price_data, returning existing.")
        return existing_data
    
    spot_decimal_price = spot_price_data.get('decimal_price')
    if spot_decimal_price is None:
        print("update_data_with_spot_price: spot_decimal_price is None, returning existing.")
        return existing_data
        
    print(f"Updating existing data ({len(existing_data)} rows) with spot price: {spot_decimal_price}")
    # Add logging for spot price in the specific format
    special_string_spot = spot_price_data.get('special_string_price', '')
    print(f"\nSpot Price ({special_string_spot}): Decimal = {int(spot_decimal_price)} + {((spot_decimal_price % 1) * 32):.2f}/32 = {spot_decimal_price}")
    
    # Create a copy of existing data to avoid modifying the original
    output_data = [row.copy() for row in existing_data]

    # Determine the base tick for the spot price (floor to the nearest tick)
    epsilon = PRICE_INCREMENT_DECIMAL / 100.0  # For float comparisons
    base_tick_for_spot_decimal = math.floor(spot_decimal_price / PRICE_INCREMENT_DECIMAL) * PRICE_INCREMENT_DECIMAL
    base_tick_for_spot_decimal = round(base_tick_for_spot_decimal / PRICE_INCREMENT_DECIMAL) * PRICE_INCREMENT_DECIMAL

    # Check if the spot price is an exact match to its base tick
    is_spot_exact_tick = abs(spot_decimal_price - base_tick_for_spot_decimal) < epsilon

    print(f"Spot Price: {spot_decimal_price}, Base Tick for Spot: {base_tick_for_spot_decimal}, Is Exact: {is_spot_exact_tick}")

    # Find the pivot index for the spot price (or the closest price below spot)
    spot_pivot_idx = len(output_data)  # Default to end of list if not found
    for i, row in enumerate(output_data):
        row_price = row.get('decimal_price_val')
        if row_price is None:
            continue
        if row_price <= spot_decimal_price:
            spot_pivot_idx = i
            break
    
    print(f"Spot pivot index: {spot_pivot_idx} out of {len(output_data)} rows")
    
    # Reset all indicators and set initial PnL values to 0
    for row in output_data:
        row['is_exact_spot'] = 0
        row['is_below_spot'] = 0
        row['is_above_spot'] = 0
        row['projected_pnl'] = 0
        # Optional: Add a debugging field to see position at each level
        row['position_debug'] = 0
        row['risk'] = 0
        row['breakeven'] = 0
    
    # Mark the spot price level(s)
    for row in output_data:
        row_price = row.get('decimal_price_val')
        if row_price is None:
            continue

        # Case 1: Spot price is an exact match for this row's price
        if abs(row_price - spot_decimal_price) < epsilon:
            row['is_exact_spot'] = 1
        # Case 2: This row's price is the base tick for a midpoint spot price
        elif not is_spot_exact_tick and abs(row_price - base_tick_for_spot_decimal) < epsilon:
            row['is_above_spot'] = 1  # Spot is above this base tick, mark this row's top border
    
    # ----- NEW IMPLEMENTATION: CUMULATIVE PNL CALCULATION -----
    
    # PASS 1: Calculate positions and PnL's for prices at and below spot
    current_position = base_position  # Start with baseline position at spot
    accumulated_pnl = base_pnl  # Start with baseline P&L at spot
    previous_price = spot_decimal_price
    
    print(f"\n--- P&L Projections with Baseline: Pos={base_position}, PnL=${base_pnl:.2f} ---")
    
    for i in range(spot_pivot_idx, len(output_data)):
        row = output_data[i]
        current_price = row.get('decimal_price_val')
        if current_price is None:
            continue
        
        # Calculate incremental PnL for this step using position BEFORE orders at this level
        price_diff = current_price - previous_price
        bp_diff = price_diff / BP_DECIMAL_PRICE_CHANGE
        pnl_increment = bp_diff * DOLLARS_PER_BP * current_position
        
        # Calculate cumulative PnL (previous level PnL + increment)
        row['projected_pnl'] = round(accumulated_pnl + pnl_increment, 2)
        
        # Log detailed PnL calculation for steps with non-zero positions
        special_string_price = row.get('price', '')
        special_string_prev_price = decimal_to_tt_bond_format(previous_price) if i > spot_pivot_idx else special_string_spot
        
        if current_position != 0:
            print(f"\n--- PnL Calculation for Level Below Spot ---")
            print(f"Previous Level: {special_string_prev_price} ({previous_price})")
            print(f"Current Level: {special_string_price} ({current_price})")
            print(f"Position for this step: {current_position} contracts")
            print(f"Price Difference (Current - Previous): {current_price} - {previous_price} = {price_diff:.7f}")
            print(f"Basis Points Moved in this step: {price_diff:.7f} / {BP_DECIMAL_PRICE_CHANGE} = {bp_diff:.3f} BPs")
            print(f"PnL Increment for this step: {bp_diff:.3f} BPs * ${DOLLARS_PER_BP}/BP * {current_position} = ${pnl_increment:.2f}")
            print(f"PnL from Previous Level: ${accumulated_pnl:.2f}")
            print(f"Total PnL for Current Level: ${accumulated_pnl:.2f} + ${pnl_increment:.2f} = ${row['projected_pnl']}")
        
        # Update accumulators for next iteration
        accumulated_pnl = row['projected_pnl']
        previous_price = current_price
        
        # Update position based on orders at this level
        qty = row.get('my_qty')
        side = row.get('working_qty_side')
        
        if qty and qty != "":  # If there's a quantity
            qty = int(qty)
            if side == '1':  # Buy order
                current_position += qty
            elif side == '2':  # Sell order
                current_position -= qty
        
        # Store the position AFTER processing orders at this level
        row['position_debug'] = current_position
        # Calculate risk as position multiplied by 15.625
        row['risk'] = current_position * 15.625
        
        # Calculate breakeven as Projected PnL / Risk (showing 0 if either value is 0)
        if row['projected_pnl'] != 0 and row['risk'] != 0:
            row['breakeven'] = row['projected_pnl'] / row['risk']
        else:
            row['breakeven'] = 0
    
    # PASS 2: Calculate positions and PnL's for prices above spot
    current_position = base_position  # Reset to baseline position for above-spot calculation
    accumulated_pnl = base_pnl  # Reset to baseline P&L
    previous_price = spot_decimal_price
    
    for i in range(spot_pivot_idx - 1, -1, -1):
        row = output_data[i]
        current_price = row.get('decimal_price_val')
        if current_price is None:
            continue
        
        # Calculate incremental PnL for this step using position BEFORE orders at this level
        price_diff = current_price - previous_price
        bp_diff = price_diff / BP_DECIMAL_PRICE_CHANGE
        pnl_increment = bp_diff * DOLLARS_PER_BP * current_position
        
        # Calculate cumulative PnL (previous level PnL + increment)
        row['projected_pnl'] = round(accumulated_pnl + pnl_increment, 2)
        
        # Log detailed PnL calculation for steps with non-zero positions
        special_string_price = row.get('price', '')
        special_string_prev_price = decimal_to_tt_bond_format(previous_price) if i < spot_pivot_idx - 1 else special_string_spot
        
        if current_position != 0:
            print(f"\n--- PnL Calculation for Level Above Spot ---")
            print(f"Previous Level: {special_string_prev_price} ({previous_price})")
            print(f"Current Level: {special_string_price} ({current_price})")
            print(f"Position for this step: {current_position} contracts")
            print(f"Price Difference (Current - Previous): {current_price} - {previous_price} = {price_diff:.7f}")
            print(f"Basis Points Moved in this step: {price_diff:.7f} / {BP_DECIMAL_PRICE_CHANGE} = {bp_diff:.3f} BPs")
            print(f"PnL Increment for this step: {bp_diff:.3f} BPs * ${DOLLARS_PER_BP}/BP * {current_position} = ${pnl_increment:.2f}")
            print(f"PnL from Previous Level: ${accumulated_pnl:.2f}")
            print(f"Total PnL for Current Level: ${accumulated_pnl:.2f} + ${pnl_increment:.2f} = ${row['projected_pnl']}")
        
        # Update accumulators for next iteration
        accumulated_pnl = row['projected_pnl']
        previous_price = current_price
        
        # Update position based on orders at this level
        qty = row.get('my_qty')
        side = row.get('working_qty_side')
        
        if qty and qty != "":  # If there's a quantity
            qty = int(qty)
            if side == '1':  # Buy order
                current_position += qty
            elif side == '2':  # Sell order
                current_position -= qty
                
        # Store the position AFTER processing orders at this level
        row['position_debug'] = current_position
        # Calculate risk as position multiplied by 15.625
        row['risk'] = current_position * 15.625
        
        # Calculate breakeven as Projected PnL / Risk (showing 0 if either value is 0)
        if row['projected_pnl'] != 0 and row['risk'] != 0:
            row['breakeven'] = row['projected_pnl'] / row['risk']
        else:
            row['breakeven'] = 0
    
    # Sort back to original order (high to low price should be the same)
    # This is a safeguard in case the original data had a different sorting
    output_data.sort(key=lambda x: float('-inf') if x.get('decimal_price_val') is None else x.get('decimal_price_val'), reverse=True)
    
    # Log some debug info for rows with orders or at spot price
    for i, row in enumerate(output_data):
        if row.get('decimal_price_val') is not None:
            if row.get('my_qty') and row.get('my_qty') != "":
                print(f"Row {i}: Price {row['price']}, Qty {row['my_qty']}, Side {row.get('working_qty_side')}, Position (after fill) {row.get('position_debug')}, PnL {row['projected_pnl']}, Risk {row['risk']}, Breakeven {row['breakeven']:.2f}")
            elif row.get('is_exact_spot') == 1:
                print(f"Row {i}: Price {row['price']} (SPOT PRICE), Position (after fill) {row.get('position_debug')}, PnL {row['projected_pnl']}, Risk {row['risk']}, Breakeven {row['breakeven']:.2f}")
    
    return output_data

# --- Execution ---
if __name__ == "__main__":
    print(f"Scenario Ladder App - Target TT Env: {ENVIRONMENT}")
    print("Starting Dash server for Scenario Ladder...")
    app.run(debug=True, port=8053) # Using a different port 