# uikitxv2/demo/simple_ladder_app.py

import dash
from dash import html, dcc # Import dcc for Store if needed later
import dash_bootstrap_components as dbc
import os
import sys
import pandas as pd
import requests # For API calls
import json     # For saving API response
from dash.dependencies import Input, Output, State # Import State

# --- Adjust Python path to find uikitxv2 and local modules ---
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.join(project_root, 'src')
ladderTest_dir = os.path.dirname(os.path.abspath(__file__))

if src_path not in sys.path:
    sys.path.insert(0, src_path)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if ladderTest_dir not in sys.path:
    sys.path.insert(0, ladderTest_dir)

# --- Import uikitxv2 components and local formatter ---
try:
    from src.components import DataTable, Button # Import Button
    from src.utils.colour_palette import default_theme
    from price_formatter import decimal_to_tt_bond_format
    # Import TT REST API tools
    from TTRestAPI.token_manager import TTTokenManager
    from TTRestAPI import tt_config
    print("Successfully imported uikitxv2 components, theme, price_formatter, and TT REST API tools")
except ImportError as e:
    print(f"Error importing components: {e}")
    print(f"sys.path: {sys.path}")
    sys.exit(1)
# --- End Imports ---

# --- Initialize Dash App ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Trading Ladder"

# --- Constants ---
# Assuming ZN for now, based on previous examples. This should ideally be dynamic.
TARGET_INSTRUMENT_ID = "8092262517946017060" # From your my_working_orders_response.json
TT_API_BASE_URL = "https://ttrestapi.trade.tt" # Defined in TTRestAPI examples, good to have here too

# --- Helper: Initial DataFrame Generation ---
def create_initial_ladder_df():
    mock_market_data_list = []
    max_price_decimal = 112.0 # Adjusted range for better visibility around common ZN prices
    min_price_decimal = 108.0
    price_increment = 1.0 / 64.0 
    current_price_decimal = max_price_decimal
    epsilon = price_increment / 2.0

    while current_price_decimal >= min_price_decimal - epsilon:
        formatted_price_str = decimal_to_tt_bond_format(current_price_decimal)
        mock_market_data_list.append({
            'price_decimal': current_price_decimal,
            'price': formatted_price_str,
            'work': "",
            'bid_qty': 0,
            'my_bid_qty': 0,
            'my_ask_qty': 0,
            'ask_qty': 0,
        })
        current_price_decimal -= price_increment
        current_price_decimal = round(current_price_decimal / price_increment) * price_increment
    
    mock_market_data_list.sort(key=lambda x: x['price_decimal'], reverse=True)
    return pd.DataFrame(mock_market_data_list)

# --- Define Market and Order Data ---
# Initial empty DataFrame structure
initial_df = create_initial_ladder_df()

# Define string representations for key prices (used for styling & initial mock work orders if any)
# These are less critical now as data will come from API, but kept for styling if needed.
P_110_025_S = decimal_to_tt_bond_format(110.078125) 
P_110_010_S = decimal_to_tt_bond_format(110.03125)
P_110_005_S = decimal_to_tt_bond_format(110.015625)
P_109_980_S = decimal_to_tt_bond_format(109.9375)
P_109_970_S = decimal_to_tt_bond_format(109.90625)


# --- Define Columns for DataTable ---
ladder_columns = [
    {"name": "Work", "id": "work", "type": "text"},
    {"name": "Bid Qty", "id": "bid_qty", "type": "numeric"},
    {"name": "Price", "id": "price", "type": "text"}, 
    {"name": "Ask Qty", "id": "ask_qty", "type": "numeric"},
]

# --- UI Component Instantiation ---
bid_color = "#1E88E5"
ask_color = "#E53935"
neutral_color = "#424242"
header_color = "#333333"
work_column_color = "#555555"

trading_ladder_table = DataTable(
    id="trading-ladder",
    columns=ladder_columns,
    data=initial_df.to_dict('records'), # Initial data
    theme=default_theme,
    style_table={
        'width': '550px', 'tableLayout': 'fixed', 'height': '80vh',
        'overflowY': 'auto', 'overflowX': 'hidden',
    },
    style_cell={
        'backgroundColor': 'black', 'color': 'white', 'font-family': 'monospace',
        'fontSize': '12px', 'height': '22px', 'maxHeight': '22px', 'minHeight': '22px',
        'width': '120px', 'minWidth': '120px', 'maxWidth': '120px',
        'textAlign': 'center', 'padding': '0px', 'margin': '0px', 'border': '1px solid #444',
    },
    style_header={
        'backgroundColor': header_color, 'color': 'white', 'height': '28px',
        'padding': '0px', 'textAlign': 'center', 'fontWeight': 'bold', 'border': '1px solid #444',
    },
    style_data_conditional=[
        {'if': {'column_id': 'work'}, 'backgroundColor': work_column_color, 'textAlign': 'left', 'paddingLeft': '5px'},
        {'if': {'column_id': 'work', 'filter_query': '{work} contains "B:"'}, 'color': '#18F0C3'},
        {'if': {'column_id': 'work', 'filter_query': '{work} contains "S:"'}, 'color': '#FF5252'},
        {'if': {'column_id': 'price'}, 'backgroundColor': neutral_color},
        {'if': {'column_id': 'work', 'filter_query': '{work} = ""'}, 'color': 'black'},
        {'if': {'column_id': 'bid_qty', 'filter_query': '{bid_qty} = 0'}, 'color': 'black'},
        {'if': {'column_id': 'ask_qty', 'filter_query': '{ask_qty} = 0'}, 'color': 'black'},
        {'if': {'column_id': 'bid_qty', 'filter_query': '{bid_qty} > 0'}, 'backgroundColor': bid_color},
        {'if': {'column_id': 'bid_qty', 'filter_query': '{my_bid_qty} > 0'}, 'backgroundColor': '#0D47A1', 'fontWeight': 'bold'},
        {'if': {'column_id': 'ask_qty', 'filter_query': '{ask_qty} > 0'}, 'backgroundColor': ask_color},
        {'if': {'column_id': 'ask_qty', 'filter_query': '{my_ask_qty} > 0'}, 'backgroundColor': '#B71C1C', 'fontWeight': 'bold'},
        # { # Problematic filter commented out
        #     'if': {'filter_query': f"{{price}} = '{P_110_010_S}' || {{price}} = '{P_110_005_S}'"},
        #     'border': '1px solid #666',
        # },
    ],
    page_size=len(initial_df)
)

print("Instantiated trading ladder DataTable with initial DataFrame")

# --- App Layout ---
app.layout = dbc.Container([
    html.H2("Trading Ladder (TT Style)", style={"textAlign": "center", "color": "#18F0C3"}),
    dbc.Row([
        dbc.Col(Button(id="jump-to-current-price", label="Jump to Current Price", className="mb-2").render()),
        dbc.Col(Button(id="refresh-orders-button", label="Refresh Working Orders", className="mb-2").render()), # New Button
    ]),
    html.Div(id="target-row-index", style={"display": "none"}),
    html.Div(id="error-output-div", style={"color": "red"}), # For displaying errors
    html.Div(
        trading_ladder_table.render(),
        style={"display": "flex", "justifyContent": "center", "margin": "0 auto"}
    )
], fluid=True, style={"backgroundColor": "black", "padding": "10px", "height": "100vh"})

print("Dash layout defined")

# --- Callback for Refreshing Working Orders ---
@app.callback(
    Output('trading-ladder', 'data'),
    Output('error-output-div', 'children'), # Output for errors
    Input('refresh-orders-button', 'n_clicks'),
    prevent_initial_call=True
)
def update_working_orders(n_clicks):
    if n_clicks is None:
        return dash.no_update, dash.no_update

    print("Refreshing working orders...")
    error_message = ""
    
    # Create a fresh DataFrame for updates to ensure a clean slate for work/my_qty columns
    # This df will have all price levels from min to max.
    updated_df = create_initial_ladder_df()

    try:
        token_manager = TTTokenManager(
            environment=tt_config.ENVIRONMENT,
            token_file_base=tt_config.TOKEN_FILE,
            config_module=tt_config
        )
        token = token_manager.get_token()
        if not token:
            error_message = "Failed to acquire token."
            print(error_message)
            return initial_df.to_dict('records'), error_message # Return initial if token fails

        service = "ttledger"
        endpoint = "/orders"
        url = f"{TT_API_BASE_URL}/{service}/{token_manager.env_path_segment}{endpoint}"
        
        request_id = token_manager.create_request_id()
        # Filter by our target instrument ID
        params = {"requestId": request_id, "instrumentId": TARGET_INSTRUMENT_ID}
        
        headers = {
            "x-api-key": token_manager.api_key,
            "accept": "application/json",
            "Authorization": f"Bearer {token}"
        }

        print(f"Making API request to {url} with params: {params}")
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        
        api_data = response.json()
        
        # Save to ladderTest directory
        orders_json_path = os.path.join(ladderTest_dir, "my_working_orders_response.json")
        with open(orders_json_path, 'w') as f:
            json.dump(api_data, f, indent=2)
        print(f"Working orders response saved to '{orders_json_path}'")

        orders = api_data.get('orders', [])
        if not orders and isinstance(api_data, list): orders = api_data

        if orders:
            print(f"Processing {len(orders)} orders for instrument {TARGET_INSTRUMENT_ID}...")
            for api_order in orders:
                # Only process orders for the target instrument (redundant if API filtered, good practice)
                if str(api_order.get("instrumentId")) != TARGET_INSTRUMENT_ID:
                    continue

                order_price_decimal = api_order.get('price')
                # Ensure price is a number before formatting
                if not isinstance(order_price_decimal, (int, float)):
                    print(f"Skipping order {api_order.get('orderId')} due to invalid price: {order_price_decimal}")
                    continue

                leaves_qty = int(api_order.get('leavesQuantity', 0))
                side = str(api_order.get('side', '')) # "1" for Buy, "2" for Sell
                
                if leaves_qty == 0: # Skip orders with no remaining quantity
                    continue

                formatted_price_str = decimal_to_tt_bond_format(order_price_decimal)
                
                # Find matching row index in DataFrame
                matching_rows = updated_df.index[updated_df['price'] == formatted_price_str].tolist()

                if matching_rows:
                    idx = matching_rows[0] # Should be unique if prices are unique
                    
                    # Placeholder for position, format like "S:pos | W:work_qty"
                    # Position data (S:X or B:X) needs a separate call to ttmonitor, TBD.
                    pos_str_part = "B:?" if side == "1" else "S:?"
                    
                    if side == "1": # Buy
                        updated_df.loc[idx, 'my_bid_qty'] += leaves_qty
                        current_work_qty = updated_df.loc[idx, 'my_bid_qty']
                        updated_df.loc[idx, 'work'] = f"{pos_str_part} | W:{current_work_qty}"
                    elif side == "2": # Sell
                        updated_df.loc[idx, 'my_ask_qty'] += leaves_qty
                        current_work_qty = updated_df.loc[idx, 'my_ask_qty']
                        updated_df.loc[idx, 'work'] = f"{pos_str_part} | W:{current_work_qty}"
                else:
                    print(f"Price {formatted_price_str} (from order {api_order.get('orderId')}) not found in ladder display range.")
            print("Finished processing orders.")
        else:
            print("No working orders returned from API or structure unexpected.")
            # Clear previous work if no orders
            updated_df['work'] = ""
            updated_df['my_bid_qty'] = 0
            updated_df['my_ask_qty'] = 0


    except requests.exceptions.HTTPError as http_err:
        error_message = f"HTTP error: {http_err} - {http_err.response.text if http_err.response else 'No response text'}"
        print(error_message)
    except Exception as e:
        error_message = f"An error occurred: {e}"
        print(error_message)
    
    return updated_df.to_dict('records'), error_message


# --- Callback for Jump to Current Price ---
# (Existing jump_to_current_price callback - may need adjustment based on how DataFrame is handled)
# For now, it uses mock_market_data_list (which is the source for initial_df)
@app.callback(
    Output('target-row-index', 'children'),
    Input('jump-to-current-price', 'n_clicks'),
    State('trading-ladder', 'data'), # Get current data from table
    prevent_initial_call=True
)
def jump_to_current_price(n_clicks, current_table_data):
    if n_clicks is None or not current_table_data:
        return dash.no_update

    # The current_table_data is a list of dicts.
    # We need to find the appropriate row index based on bids/asks.
    
    target_idx_in_data = 0 
    highest_bid_with_data_idx = -1
    lowest_ask_price_row_idx = -1 # Index of the row with the lowest asking price

    # Iterate through the current table data (list of dicts)
    # Data is sorted by price descending in the DataFrame generation
    for idx, row_data in enumerate(current_table_data):
        if row_data.get('bid_qty', 0) > 0 or row_data.get('my_bid_qty', 0) > 0:
            if highest_bid_with_data_idx == -1: # First one we find (highest price)
                highest_bid_with_data_idx = idx
        
        # For asks, we want the one with the "lowest price" that has quantity,
        # which will be higher up in the list because the list is sorted descending by price.
        if row_data.get('ask_qty', 0) > 0 or row_data.get('my_ask_qty', 0) > 0:
            if lowest_ask_price_row_idx == -1: # The first one we encounter is the lowest asking price.
                 lowest_ask_price_row_idx = idx


    if highest_bid_with_data_idx != -1: # Prioritize scrolling to highest bid
        target_idx_in_data = highest_bid_with_data_idx
    elif lowest_ask_price_row_idx != -1: # Else, scroll to lowest ask
        target_idx_in_data = lowest_ask_price_row_idx
    # else: remain 0 (top)
        
    return str(target_idx_in_data)

# --- Clientside Callback for Scrolling ---
# (This should still work as it operates on row index)
app.clientside_callback(
    """
    function(targetIndex) {
        if (!targetIndex || targetIndex === '') {
            return;
        }
        const index = parseInt(targetIndex, 10) + 1; // Adjust for header row
        const rowSelector = `.dash-spreadsheet-container .dash-spreadsheet-inner tr:nth-child(${index})`;
        const rowElement = document.querySelector(rowSelector);
        if (rowElement) {
            rowElement.scrollIntoView({ block: 'center', behavior: 'smooth' });
        }
        return;
    }
    """,
    Output('target-row-index', 'data'), # Note: Changed from 'children' to 'data' as it's a common pattern
                                       # and 'children' was already an output for the jump_to_current_price callback.
                                       # This callback doesn't really need to output anything if it's just for side-effects.
                                       # However, keeping it as 'data' (a dummy output) is fine.
    Input('target-row-index', 'children'), # Triggered by the output of jump_to_current_price
    prevent_initial_call=True
)


# Custom CSS (app.index_string) remains the same as previous version
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            /* Force cell uniformity */
            .dash-cell, .dash-header {
                height: 22px !important;
                max-height: 22px !important;
                line-height: 22px !important;
                overflow: hidden !important;
                white-space: nowrap !important;
                text-overflow: ellipsis !important;
            }
            
            /* Enforce header height */
            .dash-header {
                height: 28px !important;
                max-height: 28px !important;
                line-height: 28px !important;
            }
            
            /* Ensure fixed width columns */
            .dash-spreadsheet-container .dash-spreadsheet-inner table {
                table-layout: fixed !important;
                width: 550px !important;
            }
            
            /* Set individual column widths */
            .dash-spreadsheet-container .dash-spreadsheet-inner th:nth-child(1),
            .dash-spreadsheet-container .dash-spreadsheet-inner td:nth-child(1) {
                width: 150px !important;
                min-width: 150px !important;
                max-width: 150px !important;
            }
            
            .dash-spreadsheet-container .dash-spreadsheet-inner th:nth-child(2),
            .dash-spreadsheet-container .dash-spreadsheet-inner td:nth-child(2),
            .dash-spreadsheet-container .dash-spreadsheet-inner th:nth-child(3),
            .dash-spreadsheet-container .dash-spreadsheet-inner td:nth-child(3),
            .dash-spreadsheet-container .dash-spreadsheet-inner th:nth-child(4),
            .dash-spreadsheet-container .dash-spreadsheet-inner td:nth-child(4) {
                width: 120px !important;
                min-width: 120px !important;
                max-width: 120px !important;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# --- Execution ---
if __name__ == "__main__":
    # Ensure tt_config.ENVIRONMENT is set correctly before running, e.g. "SIM"
    print(f"Ladder Test App - Target TT Env: {tt_config.ENVIRONMENT}")
    print(f"Ladder Test App - Target Instrument ID for Orders: {TARGET_INSTRUMENT_ID}")
    print("Starting Dash server for trading ladder...")
    app.run(debug=True, port=8051)