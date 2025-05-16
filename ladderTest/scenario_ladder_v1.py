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
from pywinauto.keyboard import send_keys
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

# --- Adjust Python path to find uikitxv2 and local modules ---
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.join(project_root, 'src')
ladderTest_dir = os.path.dirname(os.path.abspath(__file__))
TTRestAPI_path = os.path.join(project_root, 'TTRestAPI')


if src_path not in sys.path:
    sys.path.insert(0, src_path)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if ladderTest_dir not in sys.path:
    sys.path.insert(0, ladderTest_dir)
if TTRestAPI_path not in sys.path:
    sys.path.insert(0, TTRestAPI_path)

# --- Import uikitxv2 components and local formatter ---
try:
    from src.components import DataTable, Button # Include Button for the 'Get Spot Price' button
    from src.utils.colour_palette import default_theme # Using default_theme for now
    from price_formatter import decimal_to_tt_bond_format
    from TTRestAPI.token_manager import TTTokenManager
    from TTRestAPI import tt_config
    print("Successfully imported uikitxv2 components, theme, price_formatter, and TT REST API tools")
except ImportError as e:
    print(f"Error importing components: {e}")
    print(f"Relevant sys.path: {[p for p in sys.path if 'uikitxv2' in p]}")
    # More detailed error for TTRestAPI
    try:
        import TTRestAPI
        print(f"TTRestAPI found at: {TTRestAPI.__file__}")
        import TTRestAPI.token_manager
        print(f"TTRestAPI.token_manager found at: {TTRestAPI.token_manager.__file__}")
        import TTRestAPI.tt_config
        print(f"TTRestAPI.tt_config found at: {TTRestAPI.tt_config.__file__}")

    except ImportError as ie:
        print(f"Could not import TTRestAPI modules: {ie}")

    sys.exit(1)
# --- End Imports ---

# --- Initialize Dash App ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Scenario Ladder"

# --- Constants ---
TT_API_BASE_URL = "https://ttrestapi.trade.tt"
PRICE_INCREMENT_DECIMAL = 1.0 / 64.0  # For ZN-like instruments
DATATABLE_ID = 'scenario-ladder-table'
MESSAGE_DIV_ID = 'scenario-ladder-message'
STORE_ID = 'scenario-ladder-store' # For triggering load and potentially storing state
USE_MOCK_DATA = False # Flag to switch between mock and live data
MOCK_DATA_FILE = os.path.join(ladderTest_dir, "my_working_orders_response.json")

# Pricing Monkey constants
PM_URL = "https://pricingmonkey.com/b/e9172aaf-2cb4-4f2c-826d-92f57d3aea90"
PM_WAIT_FOR_BROWSER_OPEN = 3.0
PM_WAIT_BETWEEN_ACTIONS = 0.5
PM_WAIT_FOR_COPY = 1.0
PM_KEY_PRESS_PAUSE = 0.1

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
    
    # Pattern for "XXX-YY.ZZ" or "XXX-YY.ZZZ" (allowing for 2 or 3 decimal places)
    pattern = r"(\d+)-(\d{1,2})\.(\d{2,3})"
    match = re.match(pattern, price_str)
    
    if not match:
        print(f"Failed to parse price string: '{price_str}'")
        return None, None
        
    whole_points = int(match.group(1))
    thirty_seconds_part = int(match.group(2))
    fractional_part_str = match.group(3)
    
    # Convert fractional part to a value between 0 and 99
    fractional_thirty_seconds_part = int(fractional_part_str)
    
    # Convert to decimal price: whole_points + (thirty_seconds_part + fractional_thirty_seconds_part/100)/32
    decimal_price = whole_points + (thirty_seconds_part + fractional_thirty_seconds_part/100.0) / 32.0
    
    # Generate special string format
    # For exact 32nds (e.g. "110-09.00"), use format "110'090"
    # For fractional 32nds (e.g. "110-09.75"), use format "110'0975"
    if fractional_part_str == "00":
        special_string_price = f"{whole_points}'{thirty_seconds_part:02d}0"
    else:
        special_string_price = f"{whole_points}'{thirty_seconds_part:02d}{fractional_part_str}"
    
    print(f"Converted '{price_str}' to decimal: {decimal_price}, special format: '{special_string_price}'")
    return decimal_price, special_string_price

# --- App Layout ---
app.layout = dbc.Container([
    dcc.Store(id=STORE_ID, data={'initial_load_trigger': True}), # Trigger initial load
    dcc.Store(id='spot-price-store', data={'decimal_price': None, 'special_string_price': None}), # Store for spot price
    html.H2("Scenario Ladder", style={"textAlign": "center", "color": "#18F0C3", "marginBottom": "20px"}),
    dbc.Row([
        dbc.Col(
            Button(id="get-spot-price-button", label="Get Spot Price", theme=default_theme).render(),
            width={"size": 4, "offset": 4},
            className="mb-3",
        ),
    ]),
    html.Div(id='spot-price-error-div', style={"textAlign": "center", "color": "red", "marginBottom": "10px"}),
    html.Div(id=MESSAGE_DIV_ID, children="Loading working orders...", style={"textAlign": "center", "color": "white", "marginBottom": "20px"}),
    html.Div(
        id=f"{DATATABLE_ID}-wrapper",
        children=[
            DataTable(
                id=DATATABLE_ID,
                columns=[
                    {'name': 'Working Qty', 'id': 'my_qty', "type": "numeric"},
                    {'name': 'Price', 'id': 'price', "type": "text"}
                ],
                data=[], # Start with no data
                theme=default_theme,
                style_table={'width': '350px', 'tableLayout': 'fixed', 'height': '70vh', 'overflowY': 'auto', 'margin': 'auto'},
                style_cell={
                    'backgroundColor': 'black', 'color': 'white', 'font-family': 'monospace',
                    'fontSize': '12px', 'height': '22px', 'maxHeight': '22px', 'minHeight': '22px',
                    'width': '50%', 'textAlign': 'center', 'padding': '0px', 'margin': '0px', 'border': '1px solid #444'
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
                    }
                ],
                page_size=100 # Adjust as needed, or make it dynamic
            ).render()
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
    Input(STORE_ID, 'data'),
    Input('spot-price-store', 'data'), # Add spot price store as input
    State(DATATABLE_ID, 'data')      # Add State for current table data
)
def load_and_display_orders(store_data, spot_price_data, current_table_data): # Added current_table_data
    print("Callback triggered: load_and_display_orders")
    triggered_input_info = dash.callback_context.triggered[0]
    context_id = triggered_input_info['prop_id']
    
    # If triggered by spot price update, get the current data of DataTable
    # and just update the spot price indicators
    if context_id == 'spot-price-store.data' and spot_price_data:
        # Use current_table_data from State
        if current_table_data and len(current_table_data) > 0:
            print(f"Spot price update. current_table_data has {len(current_table_data)} rows.")
            updated_data = update_data_with_spot_price(current_table_data, spot_price_data)
            return updated_data, dash.no_update, dash.no_update, dash.no_update
        else:
            # Table not populated yet, or empty. Let the full load logic run if initial_load_trigger is set.
            # Or, if initial_load_trigger is not the cause, prevent update.
            print("Spot price update, but current_table_data is empty. Preventing update or letting full load proceed.")
            if not (store_data and store_data.get('initial_load_trigger')):
                 raise PreventUpdate # Prevent if not an initial load scenario

    if not store_data or not store_data.get('initial_load_trigger'):
        print("Callback skipped: initial_load_trigger not True")
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update

    orders_data = []
    error_message_str = ""

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
                environment=tt_config.ENVIRONMENT,
                token_file_base=tt_config.TOKEN_FILE,
                config_module=tt_config
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

    if not processed_orders and not error_message_str:
        # No relevant orders found, but no API error either
        message_text = "No working orders found to display."
        print(message_text)
        message_style_visible = {'textAlign': 'center', 'color': 'white', 'marginBottom': '20px', 'display': 'block'}
        table_style_hidden = {'display': 'none'}
        return [], table_style_hidden, message_text, message_style_visible
    elif error_message_str and not processed_orders : # Prioritize API/load error message if it exists and no orders processed
        message_text = error_message_str
        print(f"Displaying error: {message_text}")
        message_style_visible = {'textAlign': 'center', 'color': 'red', 'marginBottom': '20px', 'display': 'block'} # Error in red
        table_style_hidden = {'display': 'none'}
        return [], table_style_hidden, message_text, message_style_visible
    elif not processed_orders and error_message_str: # Should be caught by above, but as a safeguard
        message_text = error_message_str
        print(f"Displaying error (safeguard): {message_text}")

    if processed_orders:
        min_order_price = min(o['price'] for o in processed_orders)
        max_order_price = max(o['price'] for o in processed_orders)

        # Round to nearest tick:
        # For min_price, round down. For max_price, round up.
        # math.floor(x / increment) * increment
        # math.ceil(x / increment) * increment
        ladder_min_price = math.floor(min_order_price / PRICE_INCREMENT_DECIMAL) * PRICE_INCREMENT_DECIMAL
        ladder_max_price = math.ceil(max_order_price / PRICE_INCREMENT_DECIMAL) * PRICE_INCREMENT_DECIMAL
        
        # Add some padding (e.g., 5 ticks above and below) if desired, or use a fixed range.
        # For now, just using the range of orders. Consider adding padding later.
        # ladder_min_price -= 5 * PRICE_INCREMENT_DECIMAL
        # ladder_max_price += 5 * PRICE_INCREMENT_DECIMAL

        num_levels = round((ladder_max_price - ladder_min_price) / PRICE_INCREMENT_DECIMAL) + 1
        print(f"Ladder Price Range: {decimal_to_tt_bond_format(ladder_min_price)} to {decimal_to_tt_bond_format(ladder_max_price)}, Levels: {num_levels}")

        current_price_level = ladder_max_price
        epsilon = PRICE_INCREMENT_DECIMAL / 100.0 # For float comparisons
        
        # Get spot price from store (if available)
        spot_decimal_price = None
        if spot_price_data and 'decimal_price' in spot_price_data:
            spot_decimal_price = spot_price_data.get('decimal_price')
            if spot_decimal_price is not None:
                print(f"Using spot price: {spot_decimal_price}")

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
                'is_above_spot': 0
            }
            
            # Removed initial spot price indicator logic here - will be handled by update_data_with_spot_price
            
            ladder_table_data.append(row_data)
            current_price_level -= PRICE_INCREMENT_DECIMAL
            # Correct for potential floating point drift by re-calculating based on fixed increment
            current_price_level = round(current_price_level / PRICE_INCREMENT_DECIMAL) * PRICE_INCREMENT_DECIMAL

        # REMOVE The block for spot price between price levels (approx lines 404-426)
        # This was: if spot_decimal_price is not None and ladder_table_data: ...
        # This logic is now fully in update_data_with_spot_price
        
        print(f"Generated {len(ladder_table_data)} rows for the ladder.")
        message_text = "" # Clear message if table has data
        message_style_hidden = {'display': 'none'}
        table_style_visible = {'display': 'block', 'width': '350px', 'margin': 'auto'} # Ensure table is centered
        return ladder_table_data, table_style_visible, message_text, message_style_hidden
    else: # Should only be hit if error_message_str exists AND processed_orders is empty
        message_text = error_message_str if error_message_str else "No working orders to display."
        print(f"Final fallback: {message_text}")
        message_style_visible = {'textAlign': 'center', 'color': 'red' if error_message_str else 'white', 'marginBottom': '20px', 'display': 'block'}
        table_style_hidden = {'display': 'none'}
        return [], table_style_hidden, message_text, message_style_visible



# --- Callback to Get Spot Price from Pricing Monkey ---
@app.callback(
    Output('spot-price-store', 'data'),
    Output('spot-price-error-div', 'children'),
    Input('get-spot-price-button', 'n_clicks'),
    prevent_initial_call=True
)
def fetch_spot_price_from_pm(n_clicks):
    """
    Fetch spot price from Pricing Monkey using UI automation.
    Opens the Pricing Monkey URL, navigates through the UI using keyboard shortcuts,
    copies the price from the clipboard, and then closes the browser tab.
    
    Args:
        n_clicks: Button click count
        
    Returns:
        dict: Spot price data with decimal and string representations
        str: Error message (if any)
    """
    if n_clicks is None or n_clicks == 0:
        raise PreventUpdate
    
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

def update_data_with_spot_price(existing_data, spot_price_data):
    """
    Update existing ladder data with spot price indicators based on decimal comparison.
    Handles exact matches and midpoints (marking the top border of the base tick).
    
    Args:
        existing_data (list): Current DataTable data (list of dictionaries, each with 'decimal_price_val')
        spot_price_data (dict): Spot price data from spot-price-store (contains 'decimal_price')
        
    Returns:
        list: Updated DataTable data with spot price indicators
    """
    if not existing_data or not spot_price_data:
        print("update_data_with_spot_price: No existing_data or spot_price_data, returning existing.")
        return existing_data
    
    spot_decimal_price = spot_price_data.get('decimal_price')
    if spot_decimal_price is None:
        print("update_data_with_spot_price: spot_decimal_price is None, returning existing.")
        return existing_data
        
    print(f"Updating existing data ({len(existing_data)} rows) with spot price: {spot_decimal_price}")
    
    updated_data = []
    epsilon = PRICE_INCREMENT_DECIMAL / 100.0 # For float comparisons

    # Determine the base tick for the spot price (floor to the nearest tick)
    # Ensure correct rounding for precise tick values to avoid floating point issues with comparison
    base_tick_for_spot_decimal = round((math.floor(spot_decimal_price / PRICE_INCREMENT_DECIMAL) * PRICE_INCREMENT_DECIMAL) / PRICE_INCREMENT_DECIMAL) * PRICE_INCREMENT_DECIMAL

    # Check if the spot price is an exact match to its base tick
    is_spot_exact_tick = abs(spot_decimal_price - base_tick_for_spot_decimal) < epsilon

    print(f"Spot Price: {spot_decimal_price}, Base Tick for Spot: {base_tick_for_spot_decimal}, Is Exact: {is_spot_exact_tick}")

    for row in existing_data:
        new_row = row.copy() # Work on a copy to avoid modifying the original list items directly
        # Reset indicators for each row
        new_row['is_exact_spot'] = 0
        new_row['is_below_spot'] = 0 # Not used by the new logic, but good to reset
        new_row['is_above_spot'] = 0
        
        row_decimal_val = new_row.get('decimal_price_val')
        if row_decimal_val is None:
            updated_data.append(new_row)
            continue
        
        # Round row_decimal_val to the same precision as base_tick_for_spot_decimal for comparison
        # This ensures that minor floating point discrepancies from initial generation don't affect comparison
        # row_decimal_val_rounded = round(row_decimal_val / PRICE_INCREMENT_DECIMAL) * PRICE_INCREMENT_DECIMAL

        # Case 1: Spot price is an exact match for this row's price
        if is_spot_exact_tick and abs(row_decimal_val - spot_decimal_price) < epsilon:
            new_row['is_exact_spot'] = 1
            print(f"  Exact spot match at row price {row_decimal_val} ('{new_row['price']}')")
        # Case 2: This row's price is the base tick for a midpoint spot price
        # (i.e., spot is not exact, and this row is the floor tick of the spot)
        elif not is_spot_exact_tick and abs(row_decimal_val - base_tick_for_spot_decimal) < epsilon:
            new_row['is_above_spot'] = 1 # Spot is above this base tick, mark this row's top border
            print(f"  Midpoint: Spot {spot_decimal_price} is above base tick {row_decimal_val} ('{new_row['price']}'). Marking top border.")
        
        updated_data.append(new_row)
        
    return updated_data

# --- Execution ---
if __name__ == "__main__":
    print(f"Scenario Ladder App - Target TT Env: {tt_config.ENVIRONMENT}")
    print("Starting Dash server for Scenario Ladder...")
    app.run(debug=True, port=8052) # Using a different port 