#!/usr/bin/env python
"""
Dash app to track and display ZN Jun25 instrument data periodically.
"""

import dash
from dash import html, dcc
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc # Optional: for styling
import datetime
import os
import sys
import requests # For API calls
import json # For handling API response

# --- Adjust Python path to find uikitxv2 and TTRestAPI ---
# This mirrors the structure in ladderTest/laddertesting.py
# Assumes TTRestAPI is a sibling directory to uikitxv2, or uikitxv2 is the project root
# and TTRestAPI is directly inside it.

# Get the directory of the current script (zn_price_tracker_app.py)
# ladderTest_dir = os.path.dirname(os.path.abspath(__file__))

# Get the project root directory (uikitxv2)
# project_root = os.path.dirname(ladderTest_dir)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Corrected: two levels up for uikitxv2

# Path to the src directory within uikitxv2
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Path to TTRestAPI (assuming it's inside the project_root, e.g., uikitxv2/TTRestAPI)
# If TTRestAPI is a sibling to uikitxv2, this needs to be os.path.dirname(project_root)
# For now, let's assume it could be inside uikitxv2 for simpler relative pathing, matching how examples are structured.
# Or, if TTRestAPI is truly global/installed, this isn't strictly needed if it's in PYTHONPATH
ttrestapi_package_path = os.path.join(project_root, 'TTRestAPI')
if ttrestapi_package_path not in sys.path:
    sys.path.insert(0, ttrestapi_package_path) # To import TTRestAPI.token_manager

# Also add project_root itself if TTRestAPI is a top-level module *within* the uikitxv2 workspace
# This allows `from TTRestAPI import ...` if TTRestAPI is a folder in uikitxv2 root.
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- End Path Adjustment ---

# --- Import uikitxv2 components and TTRestAPI utilities ---
try:
    from src.components import DataTable # uikitxv2 DataTable
    from src.components.button import Button # uikitxv2 Button
    from src.utils.colour_palette import default_theme as uikit_default_theme # uikitxv2 theme
    from TTRestAPI.token_manager import TTTokenManager
    from TTRestAPI import tt_config
    print("Successfully imported uikitxv2 and TTRestAPI components")
except ImportError as e:
    print(f"Error importing uikitxv2/TTRestAPI components: {e}")
    # Attempt to provide more detailed path information if import fails
    print(f"Current sys.path: {sys.path}")
    print(f"Project root: {project_root}")
    print(f"Src path: {src_path}")
    print(f"TTRestAPI path (expected): {ttrestapi_package_path}")
    sys.exit(1)
# --- End Imports ---

# --- Constants ---
TT_API_BASE_URL = "https://ttrestapi.trade.tt"
ZN_JUN25_INSTRUMENT_ID = "4877721789746411490"
UPDATE_INTERVAL_MS = 5 * 1000  # 5 seconds
DATATABLE_MAX_ROWS = 100 # Limit the number of rows displayed to prevent excessive memory use

# --- Initialize Dash App ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY]) # Using a dark theme
app.title = "ZN Jun25 Tracker"

# --- Global TTTokenManager Instance ---
# Ensure tt_config has the necessary attributes (TT_API_KEY, TT_API_SECRET, etc.)
try:
    token_manager = TTTokenManager(
        api_key=tt_config.TT_API_KEY,
        api_secret=tt_config.TT_API_SECRET,
        app_name=getattr(tt_config, 'APP_NAME', "ZNTrackerApp"), # Use APP_NAME from config or default
        company_name=getattr(tt_config, 'COMPANY_NAME', "MyCompany"), # Use COMPANY_NAME or default
        environment=getattr(tt_config, 'ENVIRONMENT', 'UAT'),
        token_file=getattr(tt_config, 'TOKEN_FILE', 'tt_token.json')
    )
    print("TTTokenManager initialized successfully.")
except AttributeError as e:
    print(f"Error initializing TTTokenManager: A tt_config attribute is missing - {e}")
    print("Please ensure your TTRestAPI/tt_config.py is correctly set up.")
    sys.exit(1)
except Exception as e:
    print(f"An unexpected error occurred during TTTokenManager initialization: {e}")
    sys.exit(1)

# --- Global Data Store for DataTable ---
data_rows = [] # This will store our table data dictionaries

# --- App Layout ---
app.layout = dbc.Container([
    html.H2("ZN Jun25 Instrument Data Tracker", className="text-center text-light mb-4"),
    dcc.Interval(id='interval-component', interval=UPDATE_INTERVAL_MS, n_intervals=0, disabled=False), # Start enabled
    html.Div(id='live-update-status', className="text-light mb-2"), # To show status like 'Fetching...' or errors
    Button( # Using our wrapped Button component
        id='toggle-updates-button',
        label='Pause Updates',
        theme=uikit_default_theme,
        className="mb-3"
    ).render(), # Call render() for our Button component
    DataTable(
        id='price-history-table',
        columns=[
            {"name": "Timestamp", "id": "timestamp"},
            {"name": "ZN Jun25 Tick Value", "id": "zn_data"} # Initially tracking tickValue
        ],
        data=data_rows,
        theme=uikit_default_theme,
        style_table={'height': '400px', 'overflowY': 'auto'},
        style_cell={
            'textAlign': 'left',
            'padding': '5px',
            'minWidth': '150px', 'width': '150px', 'maxWidth': '150px'
        },
        page_size=15 # Show a reasonable number of rows per page if needed, or remove for all rows
    ).render() # Call render() for our DataTable component
], fluid=True, className="bg-dark vh-100")

# --- Callback to Update Data ---
@app.callback(
    [Output('price-history-table', 'data'),
     Output('live-update-status', 'children')],
    [Input('interval-component', 'n_intervals')]
)
def update_instrument_data(n):
    global data_rows
    status_message = f"Last updated: {datetime.datetime.now().strftime('%H:%M:%S')}"
    new_data_point = None

    try:
        # 1. Get Token
        token = token_manager.get_token()
        if not token:
            status_message = "Error: Failed to acquire API token."
            return list(data_rows), status_message # Return current data, and error status

        # 2. Prepare API Call for ZN Jun25 Instrument Details
        environment_path = 'ext_uat_cert' if tt_config.ENVIRONMENT == 'UAT' else 'ext_prod_live'
        service = "ttpds"
        endpoint = f"/instrument/{ZN_JUN25_INSTRUMENT_ID}"
        url = f"{TT_API_BASE_URL}/{service}/{environment_path}{endpoint}"
        req_id = token_manager.create_request_id()
        params = {"requestId": req_id}
        headers = {
            "x-api-key": tt_config.TT_API_KEY,
            "accept": "application/json",
            "Authorization": f"Bearer {token}"
        }

        # 3. Make API Call
        response = requests.get(url, headers=headers, params=params, timeout=10) # Added timeout
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        api_data = response.json()
        
        # 4. Extract Data (currently tickValue)
        fetched_value = "Error: Data format unexpected"
        instrument_list = api_data.get('instrument')
        if instrument_list and isinstance(instrument_list, list) and len(instrument_list) > 0:
            instrument_details = instrument_list[0] # Get the first instrument dict
            fetched_value = instrument_details.get('tickValue', "Error: tickValue not in instrument object")
        elif 'tickValue' in api_data: # Fallback if tickValue is somehow at the root (unlikely for this endpoint)
            fetched_value = api_data.get('tickValue')
        else:
            status_message = f"Error: 'instrument' list not found, empty, or tickValue missing in response at {datetime.datetime.now().strftime('%H:%M:%S')}."
            # Keep data_rows as is, just update status
            # Ensure fetched_value reflects the error if we proceed to create new_data_point
            fetched_value = "Error: struct/key" # A short error code for the table

        current_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_data_point = {"timestamp": current_timestamp, "zn_data": fetched_value}

    except requests.exceptions.HTTPError as http_err:
        status_message = f"HTTP error: {http_err} - Status: {getattr(http_err.response, 'status_code', 'N/A')} at {datetime.datetime.now().strftime('%H:%M:%S')}"
        # status_message += f" Response: {getattr(http_err.response, 'text', 'No response text')[:200]}" # Optional
        new_data_point = {"timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "zn_data": "HTTP Error"}

    except requests.exceptions.RequestException as req_err: # More general request exception
        status_message = f"Request error: {req_err} at {datetime.datetime.now().strftime('%H:%M:%S')}"
        new_data_point = {"timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "zn_data": "Request Error"}

    except Exception as e:
        status_message = f"An unexpected error occurred: {e} at {datetime.datetime.now().strftime('%H:%M:%S')}"
        new_data_point = {"timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "zn_data": "App Error"}

    # Always add a new_data_point, even if it's an error, to see the attempt in the table
    # if new_data_point: # This check is now redundant as new_data_point is always created in error cases too
    data_rows.insert(0, new_data_point) # Add new data to the beginning of the list
    data_rows = data_rows[:DATATABLE_MAX_ROWS] # Keep table size manageable
    
    return list(data_rows), status_message # Return a copy of the list

# --- Callback to Toggle Interval Updates ---
@app.callback(
    [Output('interval-component', 'disabled'),
     Output('toggle-updates-button', 'children')],
    [Input('toggle-updates-button', 'n_clicks')],
    [State('interval-component', 'disabled')] # Get current state of the interval
)
def toggle_interval_updates(n_clicks, current_disabled_state):
    if n_clicks is None or n_clicks == 0:
        # Initial load, or no clicks yet
        return False, "Pause Updates" # Interval enabled, button says Pause

    # Toggle the disabled state
    new_disabled_state = not current_disabled_state
    
    button_label = "Resume Updates" if new_disabled_state else "Pause Updates"
    
    return new_disabled_state, button_label

# --- Run the App ---
if __name__ == '__main__':
    print("Starting ZN Price Tracker Dash app...")
    # Correct path adjustments for running as a script
    # The path adjustments at the top of the file handle imports when run with `python -m ladderTest.zn_price_tracker_app`
    # If running `python zn_price_tracker_app.py` directly from `ladderTest` dir, path to `src` and `TTRestAPI` is different.
    # For simplicity, assume running with `python -m ...` or that PYTHONPATH is set.
    app.run(debug=True, port=8052) # Use a different port 