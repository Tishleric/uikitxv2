# uikitxv2/demo/simple_ladder_app.py

import dash
from dash import html
import dash_bootstrap_components as dbc
import os
import sys

# --- Adjust Python path to find uikitxv2 ---
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.join(project_root, 'src')
# Add src_path to Python path
if src_path not in sys.path:
    sys.path.insert(0, src_path)
# Add project_root to Python path (needed for 'src.' imports)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# --- End Path Adjustment ---

# --- Import uikitxv2 components ---
try:
    from src.components import DataTable
    from src.utils.colour_palette import default_theme
    print("Successfully imported uikitxv2 components and theme")
except ImportError as e:
    print(f"Error importing uikitxv2 components: {e}")
    sys.exit(1)
# --- End uikitxv2 Import ---

# --- Initialize Dash App ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Trading Ladder"

# --- Define Market and Order Data ---
# Generate only the exact price range visible in the screenshot (110.090 to 109.945)
mock_market_data = []

# Create a price range that matches exactly what's visible in the screenshot
current_price = 110.090  # Start from 110.090 instead of 110.100
while current_price >= 109.945:  # Cut off at 109.945 to match screenshot
    mock_market_data.append({
        'price': current_price,
        'work': "",  # Empty string instead of None
        'bid_qty': 0,  # 0 instead of None
        'my_bid_qty': 0,  # 0 instead of None
        'my_ask_qty': 0,  # 0 instead of None
        'ask_qty': 0,  # 0 instead of None
    })
    current_price = round(current_price - 0.005, 3)

# Populate bid and ask data with NO gap between bid and ask
for row in mock_market_data:
    # Ask side (red side - right) - Lowest ask is 110.010
    if 110.045 >= row['price'] >= 110.010:
        if row['price'] == 110.045:
            row['ask_qty'] = 4904
        elif row['price'] == 110.040:
            row['ask_qty'] = 5366
        elif row['price'] == 110.035:
            row['ask_qty'] = 5553
        elif row['price'] == 110.030:
            row['ask_qty'] = 6309
        elif row['price'] == 110.025:
            row['ask_qty'] = 6840
        elif row['price'] == 110.020:
            row['ask_qty'] = 5897
        elif row['price'] == 110.015:
            row['ask_qty'] = 6193
        elif row['price'] == 110.010:
            row['ask_qty'] = 5529
    
    # Bid side (blue side - left) - Highest bid now at 110.005
    elif 110.005 >= row['price'] >= 109.960:
        if row['price'] == 110.005:  # Highest bid moved up to 110.005 (immediately below lowest ask)
            row['bid_qty'] = 4132
        elif row['price'] == 110.000:
            row['bid_qty'] = 4040
        elif row['price'] == 109.995:
            row['bid_qty'] = 4363
        elif row['price'] == 109.990:
            row['bid_qty'] = 4547
        elif row['price'] == 109.985:
            row['bid_qty'] = 4547
        elif row['price'] == 109.980:
            row['bid_qty'] = 4547
        elif row['price'] == 109.975:
            row['bid_qty'] = 5825
        elif row['price'] == 109.970:
            row['bid_qty'] = 6031
        elif row['price'] == 109.965:
            row['bid_qty'] = 5835
        elif row['price'] == 109.960:
            row['bid_qty'] = 6651

# Add working orders and positions to the Work column
# Use special formatting to maintain height consistency
for row in mock_market_data:
    # Sell order at 110.025
    if row['price'] == 110.025:
        row['work'] = "S:0 | W:5"  # Use pipe symbol instead of newline
        row['my_ask_qty'] = 5
    
    # Sell order at 110.010
    elif row['price'] == 110.010:
        row['work'] = "S:0 | W:4"  # Use pipe symbol instead of newline
        row['my_ask_qty'] = 4

    # Buy order at 109.980 (new buy limit order)
    elif row['price'] == 109.980:
        row['work'] = "B:0 | W:15"  # Use pipe symbol instead of newline
        row['my_bid_qty'] = 15

    # Buy order at 109.970 (new buy limit order)
    elif row['price'] == 109.970:
        row['work'] = "B:0 | W:25"  # Use pipe symbol instead of newline
        row['my_bid_qty'] = 25

# Keep data sorted by price descending (highest at top) for ladder view
mock_market_data.sort(key=lambda x: x['price'], reverse=True)

# --- Define Columns for DataTable ---
ladder_columns = [
    {"name": "Work", "id": "work", "type": "text"},
    {"name": "Bid Qty", "id": "bid_qty", "type": "numeric"},
    {"name": "Price", "id": "price", "type": "numeric", 
     "format": dash.dash_table.Format.Format(precision=3, scheme=dash.dash_table.Format.Scheme.fixed)},
    {"name": "Ask Qty", "id": "ask_qty", "type": "numeric"},
]

# --- UI Component Instantiation ---
# Bid side is blue, ask side is red (like in TT)
# Define colors similar to the TT ladder
bid_color = "#1E88E5"  # Blue for bids
ask_color = "#E53935"  # Red for asks
neutral_color = "#424242"  # Dark gray for price column
header_color = "#333333"  # Darker color for column headers
work_column_color = "#555555"  # Gray for work column

# Create DataTable with strictly limited styling options for consistency
trading_ladder_table = DataTable(
    id="trading-ladder",
    columns=ladder_columns,
    data=mock_market_data,
    theme=default_theme,
    
    # Strictly simple table styling
    style_table={
        'width': '550px',         # Set fixed width for the entire table
        'tableLayout': 'fixed',   # Use fixed layout algorithm
    },
    
    # Critical: Set exact height with no flexibility
    style_cell={
        'backgroundColor': 'black',
        'color': 'white',
        'font-family': 'monospace',
        'fontSize': '12px',
        'height': '22px',         # Strict exact height
        'maxHeight': '22px',
        'minHeight': '22px',
        'width': '120px',         # Set all columns to the same width
        'minWidth': '120px',      # Min width same as width
        'maxWidth': '120px',      # Max width same as width
        'textAlign': 'center',
        'padding': '0px', 
        'margin': '0px',
        'border': '1px solid #444',
    },
    
    # Header styling
    style_header={
        'backgroundColor': header_color,
        'color': 'white',
        'height': '28px',
        'padding': '0px',
        'textAlign': 'center',
        'fontWeight': 'bold',
        'border': '1px solid #444',
    },
    
    # Apply colors to different columns with minimal styling
    style_data_conditional=[
        # Work column styling - grayscale
        {
            'if': {'column_id': 'work'},
            'backgroundColor': work_column_color,
            'textAlign': 'left',
            'paddingLeft': '5px',
        },
        
        # Buy orders - blue text
        {
            'if': {'column_id': 'work', 'filter_query': '{work} contains "B:"'},
            'color': '#18F0C3',
        },
        
        # Sell orders - red text
        {
            'if': {'column_id': 'work', 'filter_query': '{work} contains "S:"'},
            'color': '#FF5252',
        },
        
        # Price column - gray background
        {
            'if': {'column_id': 'price'},
            'backgroundColor': neutral_color,
        },
        
        # Hide empty values
        {
            'if': {'column_id': 'work', 'filter_query': '{work} = ""'},
            'color': 'black',
        },
        {
            'if': {'column_id': 'bid_qty', 'filter_query': '{bid_qty} = 0'},
            'color': 'black',
        },
        {
            'if': {'column_id': 'ask_qty', 'filter_query': '{ask_qty} = 0'},
            'color': 'black',
        },
        
        # Bid column - blue background
        {
            'if': {'column_id': 'bid_qty', 'filter_query': '{bid_qty} > 0'},
            'backgroundColor': bid_color,
        },
        
        # My bids - darker blue
        {
            'if': {'column_id': 'bid_qty', 'filter_query': '{my_bid_qty} > 0'},
            'backgroundColor': '#0D47A1',
            'fontWeight': 'bold',
        },
        
        # Ask column - red background
        {
            'if': {'column_id': 'ask_qty', 'filter_query': '{ask_qty} > 0'},
            'backgroundColor': ask_color,
        },
        
        # My asks - darker red
        {
            'if': {'column_id': 'ask_qty', 'filter_query': '{my_ask_qty} > 0'},
            'backgroundColor': '#B71C1C',
            'fontWeight': 'bold',
        },
        
        # Special highlighting for the bid/ask boundary
        {
            'if': {'filter_query': '{price} = 110.010 || {price} = 110.005'},
            'border': '1px solid #666',
        },
    ],
    page_size=200,  # Large page size, no pagination
)

print("Instantiated trading ladder DataTable")

# Custom CSS to enforce consistent cell sizing
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

# --- App Layout ---
app.layout = dbc.Container([
    html.H2("Trading Ladder (TT Style)", style={"textAlign": "center", "color": "#18F0C3"}),
    html.Div(
        trading_ladder_table.render(),
        style={
            "display": "flex", 
            "justifyContent": "center",
            "margin": "0 auto",
        }
    )
], fluid=True, style={"backgroundColor": "black", "padding": "10px", "height": "100vh"})

print("Dash layout defined")

# --- Execution ---
if __name__ == "__main__":
    print("Starting Dash server for trading ladder...")
    app.run(debug=True, port=8051) # Use a different port if 8050 is in use