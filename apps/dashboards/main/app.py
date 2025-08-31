# uikitxv2/dashboard/dashboard.py

import dash
from dash import html, dcc, Input, Output, State, MATCH, ALL, callback_context # type: ignore # Added callback_context
from dash.exceptions import PreventUpdate # type: ignore
import dash_bootstrap_components as dbc # type: ignore
import os
import sys
import logging
import atexit
import pandas as pd
import traceback
import plotly.graph_objects as go 
import plotly.express as px
import json
from io import StringIO
import re
import time
import webbrowser
import pyperclip
from pywinauto.keyboard import send_keys
from typing import List, Dict
import numpy as np
from pywinauto.keyboard import send_keys
from typing import List, Dict
import math
import requests
import urllib.parse
import threading
import redis

# --- Adjust Python path ---
current_script_dir = os.path.dirname(os.path.abspath(__file__))
# Go up 3 levels to reach the project root (apps/dashboards/main -> project root)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_script_dir)))

if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"Added '{project_root}' to sys.path")

# Add lib directory to path for package imports
lib_path = os.path.join(project_root, 'lib')
if lib_path not in sys.path:
    sys.path.insert(0, lib_path)
    print(f"Added '{lib_path}' to sys.path")
# --- End Path ---

# --- Imports ---
try:
    from monitoring.logging import setup_logging, shutdown_logging
    from components.themes import default_theme
    from components import Tabs, Grid, Button, ComboBox, Container, DataTable, Graph, RadioButton, Mermaid, Loading, ListBox, RangeSlider, Checkbox, Tooltip
    print("Successfully imported logging, theme, and UI components.")
    from lib.trading.pricing_monkey import run_pm_automation, get_market_movement_data_df, SCENARIOS
    print("Successfully imported PM modules.")
    from lib.trading.bond_future_options import analyze_bond_future_option_greeks
    from lib.trading.bond_future_options.bachelier_greek import generate_greek_profiles_data, generate_taylor_error_data
    print("Successfully imported bond future options module.")
    from lib.trading.ladder import decimal_to_tt_bond_format, csv_to_sqlite_table, query_sqlite_table
    print("Successfully imported ladder utilities.")
    from lib.trading.tt_api import (
        TTTokenManager, 
        TT_API_KEY, TT_API_SECRET, TT_SIM_API_KEY, TT_SIM_API_SECRET,
        APP_NAME, COMPANY_NAME, ENVIRONMENT, TOKEN_FILE
    )
    print("Successfully imported TT REST API tools.")
    # Import decorator functions
    from lib.monitoring.decorators import monitor
    from lib.monitoring.decorators.monitor import start_observatory_writer
    print("Successfully imported tracing decorators.")
    # Import trading utilities
    from lib.trading.common import format_shock_value_for_display
    from lib.trading.common.price_parser import parse_treasury_price, decimal_to_tt_bond_format
    # Optional import: symbol-aware formatter (present in newer libs). Fall back gracefully if absent.
    try:
        from lib.trading.common.price_parser import decimal_to_tt_bond_format_by_symbol
    except Exception:
        decimal_to_tt_bond_format_by_symbol = None  # type: ignore
    from lib.trading.pnl_fifo_lifo.data_manager import get_trading_day
    # Import Actant modules from new location
    from lib.trading.actant.eod import ActantDataService, get_most_recent_json_file, get_json_file_metadata
except ImportError as e:
    print(f"Error importing from packages: {e}")
    traceback.print_exc()
    sys.exit(1)
except Exception as e_global:
    print(f"A non-ImportError occurred during the import phase: {e_global}")
    traceback.print_exc()
    sys.exit(1)
# --- End Imports ---

# --- Logging ---
logs_dir = os.path.join(project_root, 'logs')
LOG_DB_PATH = os.path.join(logs_dir, 'main_dashboard_logs.db')
os.makedirs(logs_dir, exist_ok=True)
logger_root = logging.getLogger()

# Call setup_logging directly - it already has @monitor applied
if not logger_root.handlers: 
    console_handler, db_handler = setup_logging(
        db_path=LOG_DB_PATH, 
        log_level_console=logging.DEBUG, 
        log_level_db=logging.INFO, 
        log_level_main=logging.DEBUG
    )
    atexit.register(shutdown_logging)
logger = logging.getLogger(__name__)

@monitor()
def verify_log_database():
    """Verify that the logging database tables exist and can be accessed."""
    try:
        import sqlite3
        conn = sqlite3.connect(LOG_DB_PATH)
        cursor = conn.cursor()
        
        # Check if the tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='flowTrace'")
        flow_trace_exists = cursor.fetchone() is not None
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='AveragePerformance'")
        avg_perf_exists = cursor.fetchone() is not None
        
        if flow_trace_exists and avg_perf_exists:
            logger.info("Log database verified: Both tables exist.")
        else:
            missing_tables = []
            if not flow_trace_exists:
                missing_tables.append("flowTrace")
            if not avg_perf_exists:
                missing_tables.append("AveragePerformance")
            logger.warning(f"Log database tables missing: {', '.join(missing_tables)}. They will be created on first log write.")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error verifying log database: {e}", exc_info=True)
        return False

# Verify the log database on startup
verify_log_database()
# --- End Logging ---

# --- Initialize Dash App ---
assets_folder_path_absolute = os.path.abspath(os.path.join(project_root, 'assets'))
# Decode URL-encoded path to handle Windows drive letters like z%3A -> z:
assets_folder_path_decoded = urllib.parse.unquote(assets_folder_path_absolute)
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP], 
    assets_folder=assets_folder_path_decoded,
    suppress_callback_exceptions=True 
)
app.title = "FRGM Trade Accelerator"

# --- Global In-Memory Signal for UI Updates ---
# This old pattern is being replaced by a direct Redis poll in the callback.
# UPDATE_SIGNAL = {'timestamp': None}

# @monitor()
# def redis_listener_thread():
#     """A background thread that listens to Redis for update signals."""
#     logger.info("Starting Redis listener thread for UI updates...")
#     r = redis.Redis(host='127.0.0.1', port=6379)
#     p = r.pubsub()
#     p.subscribe('positions:changed')
    
#     logger.info("Subscribed to 'positions:changed' channel.")
    
#     for message in p.listen():
#         if message['type'] == 'message':
#             try:
#                 # Just the act of receiving a message is the signal.
#                 # The content doesn't matter, only that something changed.
#                 UPDATE_SIGNAL['timestamp'] = time.time()
#                 logger.debug(f"Received update signal. New timestamp: {UPDATE_SIGNAL['timestamp']:.2f}")
#             except Exception as e:
#                 logger.error(f"Error processing message in redis_listener_thread: {e}", exc_info=True)

# # Start the listener thread in the background
# listener = threading.Thread(target=redis_listener_thread, daemon=True)
# listener.start()
# --- End Signal ---

# Add route to serve Doxygen documentation files
@app.server.route('/doxygen-docs/')
@app.server.route('/doxygen-docs/<path:filename>')
def serve_doxygen(filename='index.html'):
    """Serve Doxygen documentation files as static content"""
    import os
    from flask import send_from_directory, abort
    
    try:
        # Path to the Doxygen HTML directory
        doxygen_dir = os.path.join(project_root, 'html', 'html')
        
        # Security check - prevent directory traversal
        safe_path = os.path.join(doxygen_dir, filename)
        if not os.path.abspath(safe_path).startswith(os.path.abspath(doxygen_dir)):
            abort(403)
        
        # Check if file exists
        if not os.path.exists(safe_path):
            abort(404)
            
        # Serve the file
        return send_from_directory(doxygen_dir, filename)
        
    except Exception as e:
        logger.error(f"Error serving Doxygen file {filename}: {e}")
        abort(500)

# --- End App Init ---

# --- Start Observatory Writer ---
# Start the observatory writer for @monitor decorator
try:
    start_observatory_writer(db_path="logs/observatory.db")
    logger.info("Observatory writer started successfully")
except Exception as e:
    logger.error(f"Failed to start observatory writer: {e}")
# --- End Observatory Writer ---

# --- Register Actant PnL Callbacks Early ---
# Import and register Actant PnL callbacks at startup to avoid double-click issue
try:
    from apps.dashboards.actant_pnl import register_callbacks as register_actant_pnl_callbacks
    register_actant_pnl_callbacks(app)
    app._actant_pnl_callbacks_registered = True
    logger.info("Actant PnL callbacks registered at startup")
except Exception as e:
    logger.error(f"Failed to register Actant PnL callbacks at startup: {e}")
    app._actant_pnl_callbacks_registered = False
# --- End Actant PnL Registration ---

# --- Register Observatory Callbacks Early ---
# Import and register Observatory callbacks at startup
try:
    from apps.dashboards.observatory.callbacks import register_callbacks as register_observatory_callbacks
    
    # Register callbacks (they create their own data service)
    register_observatory_callbacks(app)
    app._observatory_callbacks_registered = True
    logger.info("Observatory callbacks registered at startup")
except Exception as e:
    logger.error(f"Failed to register Observatory callbacks at startup: {e}")
    app._observatory_callbacks_registered = False
# --- End Observatory Registration ---

# --- Register Spot Risk Callbacks Early ---
# Import and register Spot Risk callbacks at startup
try:
    from apps.dashboards.spot_risk import register_callbacks as register_spot_risk_callbacks
    
    # Register callbacks
    register_spot_risk_callbacks(app)
    app._spot_risk_callbacks_registered = True
    logger.info("Spot Risk callbacks registered at startup")
except Exception as e:
    logger.error(f"Failed to register Spot Risk callbacks at startup: {e}")
    app._spot_risk_callbacks_registered = False
# --- End Spot Risk Registration ---

# --- Register P&L Tracking Callbacks Early ---
# Import and register P&L Tracking callbacks at startup
# PnL tracking removed - Phase 3 clean slate
# Previous PnL tracking callbacks were here
app._pnl_tracking_callbacks_registered = False
# --- End P&L Tracking Registration ---

# --- Register P&L Tracking V2 Callbacks ---
# CTO_INTEGRATION: P&L v2 registration commented out pending integration
# try:
#     from apps.dashboards.pnl_v2.callbacks import register_pnl_v2_callbacks
#     register_pnl_v2_callbacks()
#     app._pnl_tracking_v2_callbacks_registered = True
#     logger.info("P&L Tracking V2 callbacks registered at startup")
# except Exception as e:
#     logger.error(f"Failed to register P&L Tracking V2 callbacks at startup: {e}")
#     app._pnl_tracking_v2_callbacks_registered = False
# --- End P&L Tracking V2 Registration ---

# --- UI Constants & Helpers ---
text_style = {"color": default_theme.text_light, "marginBottom": "5px", "marginTop": "15px"}
input_style_dcc = {
    'width': '100%', 'fontSize': '1rem', 'color': default_theme.text_light,
    'backgroundColor': default_theme.panel_bg, 'border': f'1px solid {default_theme.secondary}',
    'borderRadius': '4px', 'boxSizing': 'border-box', 'minHeight': '38px',
}
desc_prefix_options = ["1st", "2nd", "3rd", "4th", "5th", "6th", "7th"]
desc_strike_options = ["0", "25", "50", "75", "100"] 
desc_type_options = ["call", "put"]
phase_options = ["1", "2", "3", "4", "5"]

# Color scheme for different expiries
EXPIRY_COLORS = {
    "1st": "#00CC96",  # Teal/green
    "2nd": "#636EFA",  # Blue
    "3rd": "#EF553B",  # Red
    "4th": "#AB63FA",  # Purple
    "5th": "#FFA15A",  # Orange
    "6th": "#19D3F3",  # Light blue
    "7th": "#FF6692",  # Pink
    # Fallbacks for any other categories
    "other": "#FECB52"  # Yellow
}

# RESULT_TABLE_COLUMNS is taken directly from your provided file and is NOT changed.
RESULT_TABLE_COLUMNS = [
    {'name': 'Underlying', 'id': 'Underlying'},
    {'name': 'DV01 Gamma', 'id': 'DV01 Gamma'}, 
    {'name': 'Theta', 'id': 'Theta'},
    {'name': 'Vega', 'id': 'Vega'},
]

# Columns expected from pMoneyAuto for the graph
STRIKE_COLUMN_NAME = "Strike" 
# Default Y-axis for the graph (ensure this column exists in pMoneyAuto output)
DEFAULT_Y_AXIS_COL = "Implied Vol (Daily BP)" 

# Options for the Y-Axis ComboBox
# 'value' must match the exact column name in the DataFrame from pMoneyAuto
# 'label' is for display in the dropdown
Y_AXIS_CHOICES = [
    {"label": "Implied Vol", "value": "Implied Vol (Daily BP)"}, 
    {"label": "Delta (%)", "value": "% Delta"}, # Label updated
    {"label": "Vega", "value": "Vega"},
    {"label": "Gamma", "value": "DV01 Gamma"}, 
    {"label": "Theta", "value": "Theta"},
]
# Columns that need scaling by trade_amount for the graph.
GRAPH_SCALABLE_GREEKS = ['DV01 Gamma', 'Theta', 'Vega']

def create_option_input_block(option_index: int) -> Container:
    # This function remains the same as in your provided file
    desc_prefix_id = f"option-{option_index}-desc-prefix"
    desc_strike_id = f"option-{option_index}-desc-strike"
    desc_type_id = f"option-{option_index}-desc-type"
    qty_id = f"option-{option_index}-qty"
    phase_id = f"option-{option_index}-phase"

    prefix_combo = ComboBox(id=desc_prefix_id, options=[{"label": opt, "value": opt} for opt in desc_prefix_options], placeholder="Prefix", theme=default_theme)
    strike_combo = ComboBox(id=desc_strike_id, options=[{"label": opt, "value": opt} for opt in desc_strike_options], placeholder="Strike", theme=default_theme)
    type_combo = ComboBox(id=desc_type_id, options=[{"label": opt, "value": opt} for opt in desc_type_options], placeholder="Type", theme=default_theme)
    phase_combo_instance = ComboBox(id=phase_id, options=[{"label": opt, "value": opt} for opt in phase_options], placeholder="Select phase", theme=default_theme)

    description_layout = html.Div(
        style={'display': 'flex', 'alignItems': 'center', 'gap': '5px', 'width': '100%'},
        children=[
            html.Div(prefix_combo.render(), style={'flex': '3'}),
            html.Span("10y note", style={'color': default_theme.text_light, 'flex': '0 0 auto', 'padding': '0 5px'}),
            html.Div(strike_combo.render(), style={'flex': '2'}),
            html.Span("out", style={'color': default_theme.text_light, 'flex': '0 0 auto', 'padding': '0 5px'}),
            html.Div(type_combo.render(), style={'flex': '2'})
        ]
    )
    option_container_content_instance = Container(
        id=f"option-{option_index}-container",
        children=[
            html.H5(f"Option {option_index + 1} Details", style={'color': default_theme.primary, 'marginTop': '20px', 'paddingTop': '15px'}),
            html.P("Trade description:", style=text_style), description_layout,
            html.P("Trade quantity:", style=text_style), dcc.Input(id=qty_id, type="number", placeholder="Enter quantity", style=input_style_dcc, min=0),
            html.P("Phase of entry:", style=text_style), phase_combo_instance.render(), 
        ],
        style={'padding': '15px', 'border': f'1px solid {default_theme.secondary}', 'borderRadius': '5px', 'marginBottom': '15px', 'backgroundColor': default_theme.panel_bg}
    )
    return option_container_content_instance 
# --- End UI Helpers ---

# --- UI Layout Definition ---
logger.info("Defining UI layout...")
num_options_question_text = html.P("How many options are you looking to have (1-3)?", style=text_style)
num_options_selector_rendered = ComboBox(
    id="num-options-selector",
    options=[{"label": "1 Option", "value": "1"}, {"label": "2 Options", "value": "2"}, {"label": "3 Options", "value": "3"}],
    value="1",
    theme=default_theme, clearable=False, style={'marginBottom': '20px'}
).render()

dynamic_options_area = html.Div(id="dynamic-options-area") 

update_sheet_button_rendered = Button(
    label="Run Pricing Monkey Automation", id="update-sheet-button", theme=default_theme, n_clicks=0
).render()
update_sheet_button_wrapper = html.Div(update_sheet_button_rendered, style={'marginTop': '25px', 'textAlign': 'center'})

results_display_area_content = html.Div(id="results-display-area-content", children=[
    html.P("Results will appear here.", style={'textAlign': 'center', 'color': default_theme.text_light, 'marginTop': '20px'})
])

results_grid_rendered = Grid( 
    id="results-grid-area", 
    children=[results_display_area_content], 
    style={'marginTop': '30px', 'width': '100%', 'backgroundColor': default_theme.panel_bg, 'padding': '15px', 'borderRadius': '5px'}
).render()

pricing_monkey_tab_main_container_rendered = Container(
    id="pm-tab-main-container",
    children=[
        num_options_question_text,
        num_options_selector_rendered,
        dynamic_options_area, 
        update_sheet_button_wrapper,
        results_grid_rendered 
    ]
).render()

# Create the Analysis tab content
analysis_tab_content = Container(
    id="analysis-tab-container",
    children=[
        # Store component to hold market movement data
        dcc.Store(id="market-movement-data-store"),
        
        html.H4("Analysis Configuration", style={"color": default_theme.primary, "marginBottom": "20px", "textAlign": "center"}),
        
        # Center the Refresh Data button
        html.Div([
            Button(
                label="Refresh Data",
                id="analysis-refresh-button",
                theme=default_theme,
                n_clicks=0
            ).render()
        ], style={'display': 'flex', 'justifyContent': 'center', 'marginBottom': '20px'}),
        
        # Bottom row - Y-axis on left, Underlying on right
        html.Div([
            # Y-axis selection (left)
            html.Div([
                html.P("Y-axis:", style=text_style),
                ComboBox(
                    id="analysis-y-axis-selector",
                    options=[
                        {"label": "Implied Vol", "value": "Implied Vol (Daily BP)"},
                        {"label": "Delta (%)", "value": "%Delta"},
                        {"label": "Vega", "value": "Vega"},
                        {"label": "Gamma", "value": "DV01 Gamma"},
                        {"label": "Theta", "value": "Theta"},
                    ],
                    value="Implied Vol (Daily BP)",
                    theme=default_theme,
                    style={'width': '100%'}
                ).render()
            ], style={'flex': '1', 'marginRight': '15px'}),
            
            # Underlying selection (right)
            html.Div([
                html.P("Underlying:", style=text_style),
                ComboBox(
                    id="analysis-underlying-selector",
                    options=[],  # Will be populated by callback
                    placeholder="Select underlying",
                    theme=default_theme,
                    style={'width': '100%'}
                ).render()
            ], style={'flex': '1'})
        ], style={'display': 'flex', 'marginBottom': '20px', 'alignItems': 'flex-end'}),
        
        # View Toggle Buttons
        html.Div([
            html.P("View Mode:", style={"color": default_theme.text_light, "marginRight": "10px", "marginBottom": "0"}),
            html.Div([
                Button(
                    label="Graph",
                    id="view-toggle-graph",
                    theme=default_theme,
                    n_clicks=1,  # Default selected
                    style={
                        'borderTopRightRadius': '0',
                        'borderBottomRightRadius': '0',
                        'borderRight': 'none',
                        'backgroundColor': default_theme.primary  # Start with this selected
                    }
                ).render(),
                Button(
                    label="Table",
                    id="view-toggle-table",
                    theme=default_theme,
                    n_clicks=0,
                    style={
                        'borderTopLeftRadius': '0', 
                        'borderBottomLeftRadius': '0',
                        'backgroundColor': default_theme.panel_bg  # Start with this unselected
                    }
                ).render()
            ], style={"display": "flex"})
        ], style={"display": "flex", "alignItems": "center", "justifyContent": "center", "marginBottom": "20px"}),
        
        # Graph container
        html.Div(
            id="graph-view-container",
            children=[
                Grid(
                    id="analysis-graph-container",
                    children=[
                        Graph(
                            id="analysis-graph",
                            figure={
                                'data': [],
                                'layout': go.Layout(
                                    xaxis_title="Strike",
                                    yaxis_title="Selected Metric",
                                    plot_bgcolor=default_theme.base_bg,
                                    paper_bgcolor=default_theme.panel_bg,
                                    font_color=default_theme.text_light,
                                    xaxis=dict(showgrid=True, gridcolor=default_theme.secondary),
                                    yaxis=dict(showgrid=True, gridcolor=default_theme.secondary),
                                    margin=dict(l=60, r=20, t=40, b=50)
                                )
                            },
                            theme=default_theme,
                            style={'height': '400px', 'width': '100%'}
                        ).render()
                    ],
                    style={'backgroundColor': default_theme.panel_bg, 'padding': '15px', 'borderRadius': '5px'}
                ).render()
            ],
            style={'display': 'block'}  # Initially visible
        ),
        
        # Table container
        html.Div(
            id="table-view-container",
            children=[
                Grid(
                    id="analysis-table-container",
                    children=[
                        DataTable(
                            id="analysis-data-table",
                            data=[],  # Will be populated by callback
                            columns=[{"name": "Strike", "id": "Strike"}],  # Will be populated by callback
                            theme=default_theme,
                            style_table={'overflowX': 'auto', 'width': '100%'},
                            style_header={
                                'backgroundColor': default_theme.primary,
                                'color': default_theme.text_light,
                                'fontWeight': 'bold',
                                'textAlign': 'center',
                                'padding': '8px'
                            },
                            style_cell={
                                'backgroundColor': default_theme.base_bg,
                                'color': default_theme.text_light,
                                'textAlign': 'center',
                                'padding': '8px',
                                'fontFamily': 'Inter, sans-serif',
                                'fontSize': '0.8rem'
                            },
                            style_data_conditional=[
                                {
                                    'if': {'column_id': 'Strike'},
                                    'fontWeight': 'bold',
                                    'backgroundColor': default_theme.panel_bg,
                                }
                            ]
                        ).render()
                    ],
                    style={'backgroundColor': default_theme.panel_bg, 'padding': '15px', 'borderRadius': '5px'}
                ).render()
            ],
            style={'display': 'none'}  # Initially hidden
        )
    ],
    style={'padding': '15px'}
).render()

# --- Logs Database Utilities ---
@monitor()
def query_flow_trace_logs(limit=100):
    """
    Query the flowTrace table from the SQLite log database.
    
    Args:
        limit: Maximum number of rows to return, defaults to 100
        
    Returns:
        List of dictionaries suitable for DataTable
    """
    try:
        import sqlite3
        conn = sqlite3.connect(LOG_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Query for the most recent logs, ordered by timestamp (newest first)
        query = """
        SELECT id, timestamp, machine, user, level, function, message 
        FROM flowTrace 
        ORDER BY id DESC 
        LIMIT ?
        """
        cursor.execute(query, (limit,))
        
        # Convert to list of dictionaries
        results = []
        for row in cursor.fetchall():
            results.append(dict(row))
        
        cursor.close()
        conn.close()
        return results
    except Exception as e:
        logger.error(f"Error querying flow trace logs: {e}", exc_info=True)
        return []

@monitor()
def query_performance_metrics():
    """
    Query the AveragePerformance table from the SQLite log database.
    
    Returns:
        List of dictionaries suitable for DataTable
    """
    try:
        import sqlite3
        conn = sqlite3.connect(LOG_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Query all performance metrics, ordered by function name
        query = """
        SELECT function_name, call_count, error_count, 
               avg_duration_s, avg_cpu_delta, avg_memory_delta_mb, 
               last_updated
        FROM AveragePerformance 
        ORDER BY call_count DESC
        """
        cursor.execute(query)
        
        # Convert to list of dictionaries
        results = []
        for row in cursor.fetchall():
            # Format numeric values for display
            row_dict = dict(row)
            if row_dict.get('avg_duration_s') is not None:
                row_dict['avg_duration_s'] = f"{row_dict['avg_duration_s']:.3f}"
            if row_dict.get('avg_cpu_delta') is not None:
                row_dict['avg_cpu_delta'] = f"{row_dict['avg_cpu_delta']:.2f}"
            if row_dict.get('avg_memory_delta_mb') is not None:
                row_dict['avg_memory_delta_mb'] = f"{row_dict['avg_memory_delta_mb']:.2f}"
            results.append(row_dict)
        
        cursor.close()
        conn.close()
        return results
    except Exception as e:
        logger.error(f"Error querying performance metrics: {e}", exc_info=True)
        return []

# Define function to create the logs tab content
def create_logs_tab():
    """Creates the Logs tab with flow trace and performance data tables."""
    
    # Define empty table configurations
    flow_trace_columns = [
        {"name": "Timestamp", "id": "timestamp"},
        {"name": "Function", "id": "function"},
        {"name": "Level", "id": "level"},
        {"name": "Message", "id": "message"},
        {"name": "Machine", "id": "machine"},
        {"name": "User", "id": "user"}
    ]
    
    performance_columns = [
        {"name": "Function", "id": "function_name"},
        {"name": "Call Count", "id": "call_count"},
        {"name": "Error Count", "id": "error_count"},
        {"name": "Avg Duration (s)", "id": "avg_duration_s"},
        {"name": "Avg CPU Delta (%)", "id": "avg_cpu_delta"},
        {"name": "Avg Memory Delta (MB)", "id": "avg_memory_delta_mb"},
        {"name": "Last Updated", "id": "last_updated"}
    ]
    
    # Create the refresh button
    refresh_button = Button(
        id="logs-refresh-button",
        label="Refresh Logs",
        theme=default_theme,
        n_clicks=0
    )
    
    # Create the empty table button with danger styling
    empty_table_button = Button(
        id="logs-empty-button",
        label="Empty Table",
        theme=default_theme,
        style={"backgroundColor": default_theme.danger, "borderColor": default_theme.danger},
        n_clicks=0
    )
    
    # Create empty DataTable components
    flow_trace_table = DataTable(
        id="flow-trace-table",
        columns=flow_trace_columns,
        data=[],  # Empty data
        theme=default_theme,
        style_data_conditional=[
            {
                'if': {'filter_query': '{level} = "ERROR"'},
                'backgroundColor': default_theme.danger,
                'color': default_theme.text_light
            }
        ]
    )
    
    performance_table = DataTable(
        id="performance-metrics-table",
        columns=performance_columns,
        data=[],  # Empty data
        theme=default_theme
    )
    
    # Create Grid layout for the controls (toggle buttons and refresh button)
    controls_grid = Grid(
        id="logs-controls-grid",
        children=[
            html.Div([
                # View Toggle Buttons similar to Analysis tab
                html.Div([
                    html.P("View Mode:", style={"color": default_theme.text_light, "marginRight": "10px", "marginBottom": "0"}),
                    html.Div([
                        Button(
                            label="Flow Trace",
                            id="logs-toggle-flow",
                            theme=default_theme,
                            n_clicks=1,  # Default selected
                            style={
                                'borderTopRightRadius': '0',
                                'borderBottomRightRadius': '0',
                                'borderRight': 'none',
                                'backgroundColor': default_theme.primary  # Start with this selected
                            }
                        ).render(),
                        Button(
                            label="Performance",
                            id="logs-toggle-performance",
                            theme=default_theme,
                            n_clicks=0,
                            style={
                                'borderTopLeftRadius': '0', 
                                'borderBottomLeftRadius': '0',
                                'backgroundColor': default_theme.panel_bg  # Start with this unselected
                            }
                        ).render()
                    ], style={"display": "flex"})
                ], style={"display": "flex", "alignItems": "center", "flex": "1"}),
                
                # Refresh and Empty buttons on the right
                html.Div(style={"textAlign": "right", "marginLeft": "20px"}, children=[
                    html.Div(style={"display": "flex", "gap": "10px"}, children=[
                        refresh_button.render(),
                        empty_table_button.render()
                    ])
                ])
            ], style={"display": "flex", "width": "100%", "justifyContent": "space-between", "alignItems": "center"})
        ],
        style={"marginBottom": "15px", "backgroundColor": default_theme.panel_bg, "padding": "15px", "borderRadius": "5px"}
    )
    
    # Create the Grid layouts for the tables
    flow_trace_grid = Grid(
        id="flow-trace-grid",
        children=[flow_trace_table.render()],
        style={"backgroundColor": default_theme.panel_bg, "padding": "15px", "borderRadius": "5px", "display": "block"}
    )
    
    performance_grid = Grid(
        id="performance-metrics-grid",
        children=[performance_table.render()],
        style={"backgroundColor": default_theme.panel_bg, "padding": "15px", "borderRadius": "5px", "display": "none"}
    )
    
    # Wrap it all in a Container
    logs_container = Container(
        id="logs-tab-container",
        children=[
            html.H4("Application Logs", style={"color": default_theme.primary, "marginBottom": "20px", "textAlign": "center"}),
            controls_grid.render(),
            flow_trace_grid.render(),
            performance_grid.render()
        ],
        style={"padding": "15px"}
    )
    
    return logs_container.render()
def create_mermaid_tab():
    """Creates the Mermaid tab with a diagram visualization."""
    
    # Define a dummy flowchart for the mermaid diagram
    dummy_flowchart = """
    flowchart LR
        %% ============ Execution layer ============
        subgraph ExecutionLayer["Execution Layer"]
            tt["TT (futures algo)"]
            cmeDirect["CME Direct (options)"]
            cme["CME Exchange"]

            tt -->|futures orders| cme
            
        end

        %% ============ Data & analytics stack ============
        md["Market Data feed"]
        pricing["Pricing Monkey"]
        actant["ACTANT"]
        greeks["Greeks"]
        position["Position"]
        optimizer["Optimizer"]
        dashboard["Dashboard"]

        %% ----- Market-data distribution -----
        md --> tt
        md --> | options orders |cmeDirect
        md --> actant
        md --> pricing

        %% ----- Exchange & options → risk engine -----
        cme -->|positions| actant
        cmeDirect -->|positions| actant

        %% ----- Risk & valuation flow -----
        actant -->|analytics| greeks
        actant -->|positions| position
        pricing --> greeks
        pricing --> dashboard

        %% ----- Optimisation loop -----
        greeks --> optimizer
        position --> optimizer
        optimizer --> dashboard
    """
    
    # Create the Mermaid component with the dummy diagram
    mermaid_diagram = Mermaid(theme=default_theme).render(
        id="mermaid-diagram",
        graph_definition=dummy_flowchart,
        title="Project Architecture",
        description="System architecture diagram showing data flow and component relationships"
    )
    
    # Create Grid layout to contain the Mermaid diagram
    mermaid_grid = Grid(
        id="mermaid-grid",
        children=[mermaid_diagram],
        style={"backgroundColor": default_theme.panel_bg, "padding": "15px", "borderRadius": "5px"}
    )
    
    # Define new flowchart for TT REST API diagram
    tt_rest_api_flowchart = """
    flowchart LR
      %% Execution Layer
      subgraph TTExecution["Execution Layer"]
        A[TT ADL Algorithm Lab] -->|Executes trades| B[CME Exchange]
      end

      %% Data & Analytics Stack
      subgraph DataStack["Data & Analytics Stack"]
        B -->|Market & Position Data| C["Actant  (Position, Risk, Market Data)"]
        D[Pricing Monkey] -->|Spot Price| E["Backend"]
        C -->|Processed Position via SFTP| E
      end

      %% REST API feed
      A -->|Working Orders via TT REST API| E

      %% In-app calculations
      E -->|"Calculates PnL, Risk, Breakeven, and (later) Gamma"|E

      %% UI Layer
      F["UI (Simulated Ladder)"]
      E --> F
    """
    
    # Create the second Mermaid component 
    tt_rest_api_diagram = Mermaid(theme=default_theme).render(
        id="tt-rest-api-diagram",
        graph_definition=tt_rest_api_flowchart,
        title="Scenario Ladder Architecture",
        description="Architecture diagram showing the flow of data into our simulated ladder"
    )
    
    # Create second Grid layout for the TT REST API diagram
    tt_rest_api_grid = Grid(
        id="tt-rest-api-grid",
        children=[tt_rest_api_diagram],
        style={"backgroundColor": default_theme.panel_bg, "padding": "15px", "borderRadius": "5px", "marginTop": "20px"}
    )
    
    # Wrap it all in a Container with both grids
    mermaid_container = Container(
        id="mermaid-tab-container",
        children=[
            mermaid_grid.render(),
            tt_rest_api_grid.render()
        ],
        style={"padding": "15px"}
    )
    
    return mermaid_container.render()

# --- Greek Analysis Helper Functions ---
def acp_create_greek_graph(df, greek_col, title, strike_price, current_f=None):
    """Create a Plotly figure for a specific Greek"""
    fig = go.Figure()
    
    # Add the Greek profile line
    fig.add_trace(go.Scatter(
        x=df['F'],
        y=df[greek_col],
        mode='lines',
        line=dict(color=default_theme.primary, width=2),
        name=greek_col
    ))
    
    # Add vertical line at strike
    fig.add_vline(
        x=strike_price,
        line_dash="dash",
        line_color=default_theme.danger,
        annotation_text="Strike",
        annotation_position="top"
    )
    
    # Add vertical line at current future price if provided
    if current_f is not None:
        fig.add_vline(
            x=current_f,
            line_dash="dot",
            line_color=default_theme.accent
        )
    
    # Add horizontal line at zero
    fig.add_hline(
        y=0,
        line_dash="dot",
        line_color=default_theme.secondary,
        line_width=1
    )
    
    # Update layout with theme colors
    fig.update_layout(
        title=title,
        xaxis_title="Future Price",
        yaxis_title=greek_col,
        plot_bgcolor=default_theme.base_bg,
        paper_bgcolor=default_theme.panel_bg,
        font_color=default_theme.text_light,
        xaxis=dict(
            showgrid=True,
            gridcolor=default_theme.secondary,
            zeroline=False
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=default_theme.secondary,
            zeroline=True,
            zerolinecolor=default_theme.secondary
        ),
        margin=dict(l=60, r=20, t=40, b=50),
        height=350
    )
    
    return fig

def acp_create_parameter_inputs():
    """Create the parameter input section"""
    input_style = {
        'width': '100%',
        'backgroundColor': default_theme.panel_bg,
        'color': default_theme.text_light,
        'border': f'1px solid {default_theme.secondary}',
        'borderRadius': '4px',
        'padding': '5px'
    }
    
    label_style = {
        'color': default_theme.text_light,
        'marginBottom': '5px',
        'fontSize': '14px'
    }
    
    return Grid(
        id="acp-parameter-inputs-grid",
        children=[
            # Row 1: Strike, Future Price, Days to Expiry
            (html.Div([
                html.Label("Strike Price", style=label_style),
                dcc.Input(id="acp-strike-input", type="number", value=110.75, step=0.01, style=input_style)
            ]), {"width": 4}),
            (html.Div([
                html.Label("Future Price", style=label_style),
                dcc.Input(id="acp-future-price-input", type="number", value=110.789062, step=0.0000001, style=input_style)
            ]), {"width": 4}),
            (html.Div([
                html.Label("Time to Expiry (Years)", style=label_style),
                dcc.Input(id="acp-days-to-expiry-input", type="number", value=0.0186508, step=0.0000001, style=input_style)
            ]), {"width": 4}),
            
            # Row 2: Market Price, DV01, Convexity
            (html.Div([
                html.Label("Market Price (Decimal)", style=label_style),
                dcc.Input(id="acp-market-price-input", type="number", value=0.359375, step=0.00001, style=input_style)
            ]), {"width": 4}),
            (html.Div([
                html.Label("Future DV01", style=label_style),
                dcc.Input(id="acp-dv01-input", type="number", value=0.063, step=0.001, style=input_style)
            ]), {"width": 4}),
            (html.Div([
                html.Label("Future Convexity", style=label_style),
                dcc.Input(id="acp-convexity-input", type="number", value=0.002404, step=0.000001, style=input_style)
            ]), {"width": 4}),
            
            # Row 3: Option Type and Calculate Button
            (html.Div([
                html.Label("Option Type", style=label_style),
                ComboBox(
                    id="acp-option-type-selector",
                    options=[
                        {"label": "Put", "value": "put"},
                        {"label": "Call", "value": "call"}
                    ],
                    value="put",
                    theme=default_theme,
                    clearable=False
                ).render()
            ]), {"width": 4}),
            (html.Div([
                html.Label("Implied Volatility", style=label_style),
                html.Div(
                    id="acp-implied-vol-display",
                    style={
                        **input_style,
                        'padding': '7px',
                        'backgroundColor': default_theme.base_bg,
                        'fontWeight': 'bold',
                        'color': default_theme.primary
                    }
                )
            ]), {"width": 4}),
            (html.Div([
                html.Br(),  # Spacer to align button
                Button(
                    label="Recalculate",
                    id="acp-recalculate-button",
                    theme=default_theme,
                    n_clicks=0,
                    style={'width': '100%'}
                ).render()
            ]), {"width": 4})
    ], 
    theme=default_theme
    )

def acp_create_greek_table(df, greek_col, title, current_f, strike):
    """Create a DataTable for a specific Greek showing profile values"""
    # Filter to show reasonable range around current price
    display_df = df[(df['F'] >= current_f - 5) & (df['F'] <= current_f + 5)].copy()
    
    # Format the values for display
    display_df['F'] = display_df['F'].round(2)
    display_df[greek_col] = display_df[greek_col].round(4)
    
    # Rename columns for display
    display_df = display_df[['F', greek_col]].rename(columns={
        'F': 'Future Price',
        greek_col: title.split('(')[0].strip()  # Extract just the Greek name
    })
    
    # Add row highlighting for current price and strike
    style_data_conditional = []
    
    # Highlight row closest to current price
    current_idx = (display_df['Future Price'] - current_f).abs().idxmin()
    if current_idx in display_df.index:
        current_row = display_df.index.get_loc(current_idx)
        style_data_conditional.append({
            'if': {'row_index': current_row},
            'backgroundColor': default_theme.accent,
            'color': 'white'
        })
    
    # Highlight row closest to strike
    strike_idx = (display_df['Future Price'] - strike).abs().idxmin()
    if strike_idx in display_df.index:
        strike_row = display_df.index.get_loc(strike_idx)
        style_data_conditional.append({
            'if': {'row_index': strike_row},
            'backgroundColor': default_theme.danger,
            'color': 'white'
        })
    
    return DataTable(
        id=f"acp-{greek_col}-table",
        data=display_df.to_dict('records'),
        columns=[{"name": col, "id": col} for col in display_df.columns],
        theme=default_theme,
        style_cell={
            'backgroundColor': default_theme.base_bg,
            'color': default_theme.text_light,
            'textAlign': 'center',
            'padding': '8px',
            'border': f'1px solid {default_theme.secondary}'
        },
        style_header={
            'backgroundColor': default_theme.panel_bg,
            'fontWeight': 'bold',
            'color': default_theme.primary
        },
        style_data_conditional=style_data_conditional,
        page_size=20,  # Large enough to show all rows in the ±5 range
        style_table={'height': '300px', 'overflowY': 'auto'}
).render()

def create_greek_analysis_content():
    """Create the Greek Analysis page content"""
    return Container(
        id="acp-main-container",
    children=[
            # Store for Greek profiles data
            dcc.Store(id="acp-greek-profiles-store"),
            
            # Parameters Section
            html.Div([
                html.H4("Option Parameters", style={"color": default_theme.primary, "marginBottom": "20px"}),
                acp_create_parameter_inputs().render()
            ], style={"marginBottom": "30px"}),
            
            # Greek Summary Panel
            html.Div(id="acp-greek-summary-container"),
            

            
            # Toggle Buttons (Graph/Table view)
            html.Div([
                html.Div([
                    Button(
                        label="Graph View",
                        id="acp-view-mode-graph-btn",
                        theme=default_theme,
                        n_clicks=1,
                        style={
                            'borderTopRightRadius': '0',
                            'borderBottomRightRadius': '0',
                            'borderRight': 'none',
                            'backgroundColor': default_theme.primary
                        }
                    ).render(),
                    Button(
                        label="Table View",
                        id="acp-view-mode-table-btn",
                        theme=default_theme,
                        n_clicks=0,
                        style={
                            'borderTopLeftRadius': '0',
                            'borderBottomLeftRadius': '0',
                            'backgroundColor': default_theme.panel_bg
                        }
                    ).render()
                ], style={"display": "flex", "justifyContent": "center", "marginBottom": "20px"})
            ]),
            
            # Graph View Container - Individual Greek graphs removed (replaced by Greek Profile Analysis below)
            html.Div(
                id="acp-graph-view-container",
                children=[
                    # Empty container - content moved to Greek Profile Analysis section
                ],
                style={"display": "none"}  # Hidden by default since original graphs removed
            ),
            
            # Table View Container
            html.Div(
                id="acp-table-view-container",
                children=[
                    Loading(
                        id="acp-table-loading",
                        children=[
                            html.Div(id="acp-greek-table-container")
                        ],
                        type="circle",
                        theme=default_theme
                    ).render()
                ],
                style={"display": "none"}
            ),
            
            # Greek Profile Graphs Container - will be hidden when table view is active
            html.Div(
                id="acp-greek-profile-graphs-container",
                children=[
                    # Greek Profile Analysis Section
                    html.Hr(style={"borderColor": default_theme.secondary, "margin": "30px 0"}),
                    html.H4("Greek Profile Analysis: Analytical vs Numerical", style={"color": default_theme.primary, "marginBottom": "20px", "textAlign": "center"}),
                    
                    # Greek Profile Graphs Grid
                    Loading(
                        id="acp-profile-loading",
                        children=[
                            Grid(
                                id="acp-greek-profile-grid",
                                children=[
                                    # Row 1: delta_y, gamma_y, vega_y
                                    (html.Div(id="acp-profile-delta-container"), {"width": 4}),
                                    (html.Div(id="acp-profile-gamma-container"), {"width": 4}),
                                    (html.Div(id="acp-profile-vega-container"), {"width": 4}),
                                    # Row 2: theta_F, volga_price, vanna_F_price
                                    (html.Div(id="acp-profile-theta-container"), {"width": 4}),
                                    (html.Div(id="acp-profile-volga-container"), {"width": 4}),
                                    (html.Div(id="acp-profile-vanna-container"), {"width": 4}),
                                    # Row 3: charm_F, speed_F, color_F
                                    (html.Div(id="acp-profile-charm-container"), {"width": 4}),
                                    (html.Div(id="acp-profile-speed-container"), {"width": 4}),
                                    (html.Div(id="acp-profile-color-container"), {"width": 4}),
                                    # Row 4: ultima, zomma, empty
                                    (html.Div(id="acp-profile-ultima-container"), {"width": 4}),
                                    (html.Div(id="acp-profile-zomma-container"), {"width": 4}),
                                    (html.Div(), {"width": 4})  # Empty placeholder
                                ],
                                theme=default_theme
                            ).render()
                        ],
                        type="circle",
                        theme=default_theme
                    ).render(),
                    
                    # Taylor Approximation Accuracy Section
                    html.Hr(style={"borderColor": default_theme.secondary, "margin": "30px 0"}),
                    html.H4("Taylor Approximation Accuracy", style={"color": default_theme.primary, "marginBottom": "20px", "textAlign": "center"}),
                    html.P("Shows how accurately the Greeks predict option price changes for various market movements", 
                           style={"color": default_theme.text_subtle, "textAlign": "center", "marginBottom": "20px"}),
                    
                    # Taylor Error Graph (full width)
                    Loading(
                        id="acp-taylor-loading",
                        children=[
                            html.Div(id="acp-taylor-error-container")
                        ],
                        type="circle",
                        theme=default_theme
                    ).render()
                ],
                style={"display": "block"}  # Initially visible
            )
        ],
        theme=default_theme,
        style={'padding': '15px'}
    ).render()

# --- End Greek Analysis Functions ---

# --- Project Documentation Helper Functions ---
def pdoc_create_overview_section():
    """Create the project overview section"""
    
    # Migration status table data
    migration_data = [
        {"Metric": "Components Migrated", "Status": "95+ ✓", "Notes": "All UI components, trading modules, and utilities"},
        {"Metric": "Import System", "Status": "Fixed ✓", "Notes": "lib/__init__.py now properly exposes submodules"},
        {"Metric": "Dashboards Functional", "Status": "100% ✓", "Notes": "All entry points work correctly"},
        {"Metric": "Data Loss", "Status": "0 ✓", "Notes": "Complete backups maintained"}
    ]
    
    migration_table = DataTable(
        id="pdoc-migration-table",
        data=migration_data,
        columns=[
            {"name": "Metric", "id": "Metric"},
            {"name": "Status", "id": "Status"},
            {"name": "Notes", "id": "Notes"}
        ],
        theme=default_theme,
        style_cell={
            'backgroundColor': default_theme.base_bg,
            'color': default_theme.text_light,
            'textAlign': 'left',
            'padding': '12px',
            'border': f'1px solid {default_theme.secondary}'
        },
        style_header={
            'backgroundColor': default_theme.secondary,
            'color': default_theme.primary,
            'fontWeight': '500'
        },
        style_data_conditional=[
            {
                'if': {'column_id': 'Status'},
                'color': default_theme.primary,
                'fontWeight': 'bold'
            }
        ]
    ).render()
    
    return Container(
        id="pdoc-overview-section",
        children=[
            html.H2("Project Overview", style={"color": default_theme.primary, "marginTop": "0", "fontSize": "1.8em"}),
            html.P("UIKitXv2 is a comprehensive trading dashboard framework with clean Python package architecture. The recent migration achieved a 9.5/10 quality score, with all functionality preserved and imports fixed."),
            
            html.H3("Migration Status", style={"color": default_theme.accent, "marginTop": "25px", "fontSize": "1.3em"}),
            migration_table,
            
            html.H3("Why 9.5/10 Instead of 10/10?", style={"color": default_theme.accent, "marginTop": "25px", "fontSize": "1.3em"}),
            html.Ul([
                html.Li("Integration Testing Gap: While unit tests exist, there's no automated integration test suite that runs all entry points"),
                html.Li("Documentation Lag: Some inline documentation and README need updates to reflect new structure"),
                html.Li("CI/CD Pipeline: No automated checks to catch import issues before they reach production"),
                html.Li("Minor Technical Debt: Some modules still use older patterns that could be modernized")
            ])
        ],
        theme=default_theme,
        style={'backgroundColor': default_theme.panel_bg, 'padding': '30px', 'marginBottom': '30px', 'borderRadius': '8px', 'border': f'1px solid {default_theme.secondary}'}
    )

def pdoc_parse_code_index():
    """Parse code-index.md and return a dictionary of file/folder descriptions"""
    descriptions = {}
    
    # Read code-index.md
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        code_index_path = os.path.join(project_root, "memory-bank", "code-index.md")
        
        with open(code_index_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the file for descriptions
        lines = content.split('\n')
        current_section = ""
        
        for i, line in enumerate(lines):
            # Update current section based on headers
            if line.startswith('### ') or line.startswith('#### '):
                current_section = line.strip('# ').strip()
            
            # Look for file descriptions in the format: - **filename** - description
            if line.strip().startswith('- **'):
                match = re.match(r'- \*\*([^*]+)\*\* - (.+)', line.strip())
                if match:
                    filename = match.group(1).strip()
                    description = match.group(2).strip()
                    descriptions[filename] = description
            
            # Also look for directory descriptions in headers
            if ' (`' in line and '`)' in line:
                # Extract directory path from headers like "### Components (`lib/components/`)"
                match = re.match(r'.*\(`([^`]+)`\)', line)
                if match:
                    dir_path = match.group(1).strip()
                    # Get the description from the header
                    desc_match = re.match(r'^#+\s*([^(]+)', line)
                    if desc_match:
                        desc = desc_match.group(1).strip()
                        descriptions[dir_path] = desc
    
    except Exception as e:
        logger.error(f"Error parsing code-index.md: {e}")
    
    # Add some directory descriptions that might be missing
    descriptions.update({
        'lib/': 'Main package directory - Core UIKitXv2 library',
        'lib/components/': 'UI components library with basic and advanced components',
        'lib/components/basic/': 'Basic UI components - buttons, checkboxes, dropdowns, etc.',
        'lib/components/advanced/': 'Advanced UI components - data tables, graphs, grids',
        'lib/components/core/': 'Core component infrastructure and protocols',
        'lib/components/themes/': 'Theme system and styling configuration',
                    'lib/monitoring/': 'Monitoring and observatory tools',
        'lib/monitoring/decorators/': 'Performance and trace monitoring decorators',
        'lib/monitoring/logging/': 'Logging configuration and handlers',
        'lib/trading/': 'Trading domain functionality',
        'lib/trading/common/': 'Common trading utilities and parsers',
        'lib/trading/actant/': 'Actant integration modules',
        'lib/trading/pricing_monkey/': 'Pricing Monkey integration and automation',
        'lib/trading/tt_api/': 'TT REST API integration',
        'apps/': 'Application entry points and dashboards',
        'apps/dashboards/': 'Dashboard applications',
        'data/': 'Data storage structure',
        'scripts/': 'Utility and processing scripts',
        'tests/': 'Test suite for all modules',
        'SumoMachine/': 'Standalone Pricing Monkey automation tools'
    })
    
    # Add specific file descriptions from code-index.md
    descriptions.update({
        # Monitoring decorators
        'context_vars.py': 'Shared context variables for tracing and logging decorators',
        'trace_time.py': 'Decorator for logging function execution time and storing in context',
        'trace_closer.py': 'Decorator for managing resource tracing and flow trace logs',
        'trace_cpu.py': 'Decorator for measuring CPU usage delta during execution',
        'trace_memory.py': 'Decorator for measuring RSS memory usage delta',
        
        # Logging
        'config.py': 'Logging configuration with console and SQLite handlers setup',
        'handlers.py': 'SQLiteHandler processing FLOW_TRACE logs into database tables',
        
        # Trading common
        'price_parser.py': 'Price parsing/formatting utilities for treasury/bond trading',
        'date_utils.py': 'Trading calendar and date utilities for expiry calculations',
        
        # Actant EOD
        'data_service.py': 'ActantDataService - loads/processes JSON data into SQLite',
        'file_manager.py': 'File management utilities for JSON discovery and metadata',
        
        # Actant SOD  
        'actant.py': 'Core SOD processing logic for parsing trades and generating Actant format',
        'pricing_monkey_adapter.py': 'Adapter for converting Pricing Monkey to Actant formats',
        'browser_automation.py': 'Browser automation for retrieving data from Pricing Monkey',
        'futures_utils.py': 'Utilities for futures contract date calculations',
        
        # Pricing Monkey
        'pm_auto.py': 'Multi-option workflow automation using openpyxl and browser',
        'retrieval.py': 'Extended browser automation for ActantEOD data retrieval',
        'simple_retrieval.py': 'Simple data retrieval with SOD formatting',
        'processor.py': 'PM data processing utilities and validation',
        'movement.py': 'Market movement data collection and analysis',
        
        # Ladder
        'price_formatter.py': 'Treasury bond price formatting between decimal and TT formats',
        'csv_to_sqlite.py': 'Convert CSV files to SQLite tables for efficient querying',
        
        # TT API
        'token_manager.py': 'TTTokenManager for authentication and token management',
        'utils.py': 'TT API utility functions for GUIDs and request formatting',
        
        # Bond Future Options
        'pricing_engine.py': 'Core bond future option pricing engine (CTO-validated)',
        'analysis.py': 'Refactored analysis utilities for Greeks calculation',
        'demo_profiles.py': 'Demonstration code for Greek profile visualization',
        
        # Apps
        'app.py': 'Main dashboard application file',
        'scenario_ladder.py': 'Scenario ladder dashboard for price visualization',
        'zn_price_tracker.py': 'ZN price tracking application',
        
        # Scripts
        'process_actant_json.py': 'Processes Actant JSON into flattened CSV/SQLite format',
        'data_integrity_check.py': 'Comprehensive data integrity verification',
        'verify_th_pnl.py': 'Verification script for Th PnL data integrity',
        'pricing_monkey_to_actant.py': 'Integration script for PM data to Actant processing',
        
        # Config files
        'pyproject.toml': 'Package configuration with dependencies and build settings',
        'README.md': 'Project documentation and setup instructions',
        '.gitignore': 'Git ignore patterns for Python projects',
        'conftest.py': 'Shared pytest fixtures and test configuration',
        'code-index.md': 'Comprehensive file documentation and code structure reference',
        
        # Entry points
        'run_actant_eod.py': 'Entry point for ActantEOD dashboard (port 8050)',
        'run_actant_sod.py': 'Entry point for ActantSOD processing',
        'run_scenario_ladder.py': 'Entry point for Scenario Ladder dashboard (port 8051)',
        
        # Data directories
        'data/input/': 'Input data storage for all modules',
        'data/output/': 'Output data and generated files',
        'data/input/eod/': 'ActantEOD input JSON files',
        'data/input/sod/': 'ActantSOD input CSV files',
        'data/input/ladder/': 'Ladder input and mock data files',
        'data/output/eod/': 'EOD processing outputs and databases',
        'data/output/sod/': 'SOD generated CSV files',
        'data/output/ladder/': 'Ladder SQLite databases',
        
        # Test directories
        'tests/components/': 'Component unit tests',
        'tests/monitoring/': 'Decorator and logging tests',
        'tests/trading/': 'Trading utility tests',
        'tests/integration/': 'Dashboard integration tests',
        
        # Memory bank
        'memory-bank/': 'Project memory and documentation',
        'memory-bank/PRDeez/': 'Product requirements and specifications',
        
        # Assets
        'assets/': 'Static assets for dashboards',
        
        # SumoMachine
        'PmToExcel.py': 'Standalone PM to Excel automation with keyboard navigation'
    })
    
    return descriptions
def pdoc_create_file_tree_section():
    """Create the file tree section with hover tooltips"""
    
    # Parse code-index for descriptions
    descriptions = pdoc_parse_code_index()
    
    # Counter for unique tooltip IDs
    tooltip_counter = 0
    
    def create_file_element(filename, description=None, is_dir=False):
        """Create a file/directory element with optional tooltip"""
        nonlocal tooltip_counter
        
        if description:
            tooltip_counter += 1
            element_id = f"pdoc-file-{tooltip_counter}"
            
            # Create the filename span with ID for tooltip targeting
            element = html.Span(
                html.Strong(filename) if is_dir else filename,
                id=element_id,
                style={'cursor': 'help', 'textDecoration': 'underline dotted'}
            )
            
            # Create the tooltip
            tooltip = Tooltip(
                id=f"{element_id}-tooltip",
                target=element_id,
                children=description,
                theme=default_theme,
                placement="right"
            ).render()
            
            return [element, tooltip]
        else:
            # No tooltip needed
            return html.Strong(filename) if is_dir else filename
    
    # Build the file tree with tooltips
    tree_elements = []
    
    # Helper to add tree line with optional description
    def add_tree_line(prefix, filename, path=None, is_dir=False, comment=None):
        """Add a line to the tree with optional tooltip"""
        line_elements = [prefix]
        
        # Try to find description for this file/folder
        desc = None
        if path:
            desc = descriptions.get(path)
        if not desc and filename:
            desc = descriptions.get(filename)
        
        file_elem = create_file_element(filename, desc, is_dir)
        if isinstance(file_elem, list):
            line_elements.extend([file_elem[0], " "])
            if comment:
                line_elements.extend([html.Em(comment), " "])
            line_elements.append(file_elem[1])  # Tooltip
        else:
            line_elements.extend([file_elem, " "])
            if comment:
                line_elements.append(html.Em(comment))
        
        line_elements.append(html.Br())
        return line_elements
    
    # Build the tree structure
    tree_elements.extend(add_tree_line("", "uikitxv2/", "uikitxv2/", True))
    tree_elements.extend(add_tree_line("├── ", "lib/", "lib/", True, "# Main package (pip install -e .)"))
    tree_elements.extend(add_tree_line("│   ├── ", "__init__.py", "lib/__init__.py", False, "# Critical module exposer"))
    tree_elements.extend(add_tree_line("│   ├── ", "components/", "lib/components/", True, "# UI components library"))
    tree_elements.extend(add_tree_line("│   │   ├── ", "__init__.py", None, False))
    tree_elements.extend(add_tree_line("│   │   ├── ", "basic/", "lib/components/basic/", True, "# Simple UI components"))
    tree_elements.extend(add_tree_line("│   │   │   ├── ", "button.py", "button.py", False))
    tree_elements.extend(add_tree_line("│   │   │   ├── ", "checkbox.py", "checkbox.py", False))
    tree_elements.extend(add_tree_line("│   │   │   ├── ", "combobox.py", "combobox.py", False))
    tree_elements.extend(add_tree_line("│   │   │   ├── ", "container.py", "container.py", False))
    tree_elements.extend(add_tree_line("│   │   │   ├── ", "listbox.py", "listbox.py", False))
    tree_elements.extend(add_tree_line("│   │   │   ├── ", "radiobutton.py", "radiobutton.py", False))
    tree_elements.extend(add_tree_line("│   │   │   ├── ", "rangeslider.py", "rangeslider.py", False))
    tree_elements.extend(add_tree_line("│   │   │   ├── ", "tabs.py", "tabs.py", False))
    tree_elements.extend(add_tree_line("│   │   │   ├── ", "toggle.py", "toggle.py", False))
    tree_elements.extend(add_tree_line("│   │   │   └── ", "tooltip.py", "tooltip.py", False))
    tree_elements.extend(add_tree_line("│   │   ├── ", "advanced/", "lib/components/advanced/", True, "# Complex UI components"))
    tree_elements.extend(add_tree_line("│   │   │   ├── ", "datatable.py", "datatable.py", False))
    tree_elements.extend(add_tree_line("│   │   │   ├── ", "graph.py", "graph.py", False))
    tree_elements.extend(add_tree_line("│   │   │   ├── ", "grid.py", "grid.py", False))
    tree_elements.extend(add_tree_line("│   │   │   └── ", "mermaid.py", "mermaid.py", False))
    tree_elements.extend(add_tree_line("│   │   ├── ", "core/", "lib/components/core/", True, "# Component foundations"))
    tree_elements.extend(add_tree_line("│   │   │   ├── ", "base_component.py", "base_component.py", False))
    tree_elements.extend(add_tree_line("│   │   │   └── ", "protocols.py", "protocols.py", False))
    tree_elements.extend(add_tree_line("│   │   └── ", "themes/", "lib/components/themes/", True, "# UI theming"))
    tree_elements.extend(add_tree_line("│   │       └── ", "colour_palette.py", "colour_palette.py", False))
    tree_elements.extend(add_tree_line("│   ├── ", "monitoring/", "lib/monitoring/", True, "# Logging & performance"))
    tree_elements.extend(add_tree_line("│   │   ├── ", "__init__.py", "lib/monitoring/__init__.py", False))
    tree_elements.extend(add_tree_line("│   │   ├── ", "decorators/", "lib/monitoring/decorators/", True))
    tree_elements.extend(add_tree_line("│   │   │   ├── ", "__init__.py", None, False))
    tree_elements.extend(add_tree_line("│   │   │   ├── ", "context_vars.py", "context_vars.py", False))
    tree_elements.extend(add_tree_line("│   │   │   ├── ", "trace_time.py", "trace_time.py", False))
    tree_elements.extend(add_tree_line("│   │   │   ├── ", "trace_closer.py", "trace_closer.py", False))
    tree_elements.extend(add_tree_line("│   │   │   ├── ", "trace_cpu.py", "trace_cpu.py", False))
    tree_elements.extend(add_tree_line("│   │   │   └── ", "trace_memory.py", "trace_memory.py", False))
    tree_elements.extend(add_tree_line("│   │   └── ", "logging/", "lib/monitoring/logging/", True))
    tree_elements.extend(add_tree_line("│   │       ├── ", "__init__.py", None, False))
    tree_elements.extend(add_tree_line("│   │       ├── ", "config.py", "config.py", False))
    tree_elements.extend(add_tree_line("│   │       └── ", "handlers.py", "handlers.py", False))
    tree_elements.extend(add_tree_line("│   ├── ", "trading/", "lib/trading/", True, "# Trading business logic"))
    tree_elements.extend(add_tree_line("│   │   ├── ", "__init__.py", "lib/trading/__init__.py", False))
    tree_elements.extend(add_tree_line("│   │   ├── ", "common/", "lib/trading/common/", True))
    tree_elements.extend(add_tree_line("│   │   │   ├── ", "__init__.py", None, False))
    tree_elements.extend(add_tree_line("│   │   │   ├── ", "price_parser.py", "price_parser.py", False))
    tree_elements.extend(add_tree_line("│   │   │   └── ", "date_utils.py", "date_utils.py", False))
    tree_elements.extend(add_tree_line("│   │   ├── ", "actant/", "lib/trading/actant/", True))
    tree_elements.extend(add_tree_line("│   │   │   ├── ", "__init__.py", None, False))
    tree_elements.extend(add_tree_line("│   │   │   ├── ", "eod/", "lib/trading/actant/eod/", True))
    tree_elements.extend(add_tree_line("│   │   │   │   ├── ", "__init__.py", None, False))
    tree_elements.extend(add_tree_line("│   │   │   │   ├── ", "data_service.py", "data_service.py", False))
    tree_elements.extend(add_tree_line("│   │   │   │   └── ", "file_manager.py", "file_manager.py", False))
    tree_elements.extend(add_tree_line("│   │   │   └── ", "sod/", "lib/trading/actant/sod/", True))
    tree_elements.extend(add_tree_line("│   │   │       ├── ", "__init__.py", None, False))
    tree_elements.extend(add_tree_line("│   │   │       ├── ", "actant.py", "actant.py", False))
    tree_elements.extend(add_tree_line("│   │   │       ├── ", "pricing_monkey_adapter.py", "pricing_monkey_adapter.py", False))
    tree_elements.extend(add_tree_line("│   │   │       ├── ", "browser_automation.py", "browser_automation.py", False))
    tree_elements.extend(add_tree_line("│   │   │       └── ", "futures_utils.py", "futures_utils.py", False))
    tree_elements.extend(add_tree_line("│   │   ├── ", "pricing_monkey/", "lib/trading/pricing_monkey/", True))
    tree_elements.extend(add_tree_line("│   │   │   ├── ", "__init__.py", None, False))
    tree_elements.extend(add_tree_line("│   │   │   ├── ", "automation/", "lib/trading/pricing_monkey/automation/", True))
    tree_elements.extend(add_tree_line("│   │   │   │   ├── ", "__init__.py", None, False))
    tree_elements.extend(add_tree_line("│   │   │   │   └── ", "pm_auto.py", "pm_auto.py", False))
    tree_elements.extend(add_tree_line("│   │   │   ├── ", "retrieval/", "lib/trading/pricing_monkey/retrieval/", True))
    tree_elements.extend(add_tree_line("│   │   │   │   ├── ", "__init__.py", None, False))
    tree_elements.extend(add_tree_line("│   │   │   │   ├── ", "retrieval.py", "retrieval.py", False))
    tree_elements.extend(add_tree_line("│   │   │   │   └── ", "simple_retrieval.py", "simple_retrieval.py", False))
    tree_elements.extend(add_tree_line("│   │   │   └── ", "processors/", "lib/trading/pricing_monkey/processors/", True))
    tree_elements.extend(add_tree_line("│   │   │       ├── ", "__init__.py", None, False))
    tree_elements.extend(add_tree_line("│   │   │       ├── ", "processor.py", "processor.py", False))
    tree_elements.extend(add_tree_line("│   │   │       └── ", "movement.py", "movement.py", False))
    tree_elements.extend(add_tree_line("│   │   ├── ", "ladder/", "lib/trading/ladder/", True))
    tree_elements.extend(add_tree_line("│   │   │   ├── ", "__init__.py", None, False))
    tree_elements.extend(add_tree_line("│   │   │   ├── ", "price_formatter.py", "price_formatter.py", False))
    tree_elements.extend(add_tree_line("│   │   │   └── ", "csv_to_sqlite.py", "csv_to_sqlite.py", False))
    tree_elements.extend(add_tree_line("│   │   ├── ", "tt_api/", "lib/trading/tt_api/", True))
    tree_elements.extend(add_tree_line("│   │   │   ├── ", "__init__.py", None, False))
    tree_elements.extend(add_tree_line("│   │   │   ├── ", "config.py", "config.py", False))
    tree_elements.extend(add_tree_line("│   │   │   ├── ", "token_manager.py", "token_manager.py", False))
    tree_elements.extend(add_tree_line("│   │   │   └── ", "utils.py", "utils.py", False))
    tree_elements.extend(add_tree_line("│   │   └── ", "bond_future_options/", "lib/trading/bond_future_options/", True))
    tree_elements.extend(add_tree_line("│   │       ├── ", "__init__.py", None, False))
    tree_elements.extend(add_tree_line("│   │       ├── ", "pricing_engine.py", "pricing_engine.py", False))
    tree_elements.extend(add_tree_line("│   │       ├── ", "analysis.py", "analysis.py", False))
    tree_elements.extend(add_tree_line("│   │       └── ", "demo_profiles.py", "demo_profiles.py", False))
    tree_elements.extend(add_tree_line("│   └── ", "__init__.py", "lib/__init__.py", False, "# Critical module exposer"))
    tree_elements.extend(add_tree_line("├── ", "apps/", "apps/", True, "# Application layer"))
    tree_elements.extend(add_tree_line("│   ├── ", "dashboards/", "apps/dashboards/", True))
    tree_elements.extend(add_tree_line("│   │   ├── ", "actant_eod/", "apps/dashboards/actant_eod/", True, "# EOD Dashboard"))
    tree_elements.extend(add_tree_line("│   │   │   ├── ", "__init__.py", None, False))
    tree_elements.extend(add_tree_line("│   │   │   └── ", "app.py", "app.py", False))
    tree_elements.extend(add_tree_line("│   │   ├── ", "actant_preprocessing/", "apps/dashboards/actant_preprocessing/", True))
    tree_elements.extend(add_tree_line("│   │   │   └── ", "app.py", "app.py", False))
    tree_elements.extend(add_tree_line("│   │   ├── ", "ladder/", "apps/dashboards/ladder/", True))
    tree_elements.extend(add_tree_line("│   │   │   └── ", "scenario_ladder.py", "scenario_ladder.py", False))
    tree_elements.extend(add_tree_line("│   │   └── ", "main/", "apps/dashboards/main/", True))
    tree_elements.extend(add_tree_line("│   │       └── ", "app.py", "app.py", False))
    tree_elements.extend(add_tree_line("│   ├── ", "demos/", "apps/demos/", True))
    tree_elements.extend(add_tree_line("│   │   └── ", "zn_price_tracker.py", "zn_price_tracker.py", False))
    tree_elements.extend(add_tree_line("│   └── ", "unified_dashboard/", "apps/unified_dashboard/", True))
    tree_elements.extend(add_tree_line("│       ├── ", "components/", None, True))
    tree_elements.extend(add_tree_line("│       ├── ", "pages/", None, True))
    tree_elements.extend(add_tree_line("│       └── ", "state/", None, True))
    tree_elements.extend(add_tree_line("│       └── ", "state/", None, True))
    tree_elements.extend(add_tree_line("├── ", "scripts/", "scripts/", True, "# Utility scripts"))
    tree_elements.extend(add_tree_line("│   ├── ", "actant_eod/", "scripts/actant_eod/", True))
    tree_elements.extend(add_tree_line("│   │   ├── ", "process_actant_json.py", "process_actant_json.py", False))
    tree_elements.extend(add_tree_line("│   │   ├── ", "data_integrity_check.py", "data_integrity_check.py", False))
    tree_elements.extend(add_tree_line("│   │   └── ", "verify_th_pnl.py", "verify_th_pnl.py", False))
    tree_elements.extend(add_tree_line("│   ├── ", "actant_sod/", "scripts/actant_sod/", True))
    tree_elements.extend(add_tree_line("│   │   └── ", "pricing_monkey_to_actant.py", "pricing_monkey_to_actant.py", False))
    tree_elements.extend(add_tree_line("│   └── ", "migration/", "scripts/migration/", True))
    tree_elements.extend(add_tree_line("├── ", "data/", "data/", True, "# Data organization"))
    tree_elements.extend(add_tree_line("│   ├── ", "cache/", "data/cache/", True))
    tree_elements.extend(add_tree_line("│   ├── ", "input/", "data/input/", True))
    tree_elements.extend(add_tree_line("│   │   ├── ", "eod/", "data/input/eod/", True))
    tree_elements.extend(add_tree_line("│   │   ├── ", "ladder/", "data/input/ladder/", True))
    tree_elements.extend(add_tree_line("│   │   │   └── ", "Specifications/", None, True))
    tree_elements.extend(add_tree_line("│   │   ├── ", "reference/", "data/input/reference/", True))
    tree_elements.extend(add_tree_line("│   │   └── ", "sod/", "data/input/sod/", True))
    tree_elements.extend(add_tree_line("│   └── ", "output/", "data/output/", True))
    tree_elements.extend(add_tree_line("│       ├── ", "eod/", "data/output/eod/", True))
    tree_elements.extend(add_tree_line("│       ├── ", "ladder/", "data/output/ladder/", True))
    tree_elements.extend(add_tree_line("│       ├── ", "reports/", "data/output/reports/", True))
    tree_elements.extend(add_tree_line("│       └── ", "sod/", "data/output/sod/", True))
    tree_elements.extend(add_tree_line("├── ", "tests/", "tests/", True, "# Test suite for all modules"))
    tree_elements.extend(add_tree_line("│   ├── ", "components/", "tests/components/", True))
    tree_elements.extend(add_tree_line("│   ├── ", "core/", "tests/core/", True))
    tree_elements.extend(add_tree_line("│   ├── ", "dashboard/", "tests/dashboard/", True))
    tree_elements.extend(add_tree_line("│   ├── ", "decorators/", "tests/decorators/", True))
    tree_elements.extend(add_tree_line("│   ├── ", "integration/", "tests/integration/", True))
    tree_elements.extend(add_tree_line("│   ├── ", "ladderTest/", "tests/ladderTest/", True))
    tree_elements.extend(add_tree_line("│   ├── ", "lumberjack/", "tests/lumberjack/", True))
    tree_elements.extend(add_tree_line("│   ├── ", "ttapi/", "tests/ttapi/", True))
    tree_elements.extend(add_tree_line("│   └── ", "utils/", "tests/utils/", True))
    tree_elements.extend(add_tree_line("├── ", "assets/", "assets/", True, "# Static assets for dashboards"))
    tree_elements.extend(add_tree_line("├── ", "memory-bank/", "memory-bank/", True, "# Project memory and documentation"))
    tree_elements.extend(add_tree_line("│   └── ", "PRDeez/", "memory-bank/PRDeez/", True, "# Product requirements and specifications"))
    tree_elements.extend(add_tree_line("├── ", "SumoMachine/", "SumoMachine/", True, "# Standalone Pricing Monkey automation"))
    tree_elements.extend(add_tree_line("│   └── ", "PmToExcel.py", "PmToExcel.py", False))
    tree_elements.extend(add_tree_line("├── ", "logs/", "logs/", True, "# Application logs"))
    tree_elements.extend(add_tree_line("├── ", "TTRestAPI/", "TTRestAPI/", True))
    tree_elements.extend(add_tree_line("│   └── ", "examples/", None, True))
    tree_elements.extend(add_tree_line("├── ", "pyproject.toml", "pyproject.toml", False, "# Package configuration"))
    tree_elements.extend(add_tree_line("├── ", "README.md", "README.md", False, "# Project documentation"))
    tree_elements.extend(add_tree_line("├── ", ".gitignore", ".gitignore", False, "# Git ignore patterns"))
    tree_elements.extend(add_tree_line("├── ", "conftest.py", "conftest.py", False, "# Pytest configuration"))
    tree_elements.extend(add_tree_line("├── ", "run_actant_eod.py", "run_actant_eod.py", False, "# EOD dashboard entry"))
    tree_elements.extend(add_tree_line("├── ", "run_actant_preprocessing.py", "run_actant_preprocessing.py", False))
    tree_elements.extend(add_tree_line("├── ", "run_actant_sod.py", "run_actant_sod.py", False, "# SOD processing entry"))
    tree_elements.extend(add_tree_line("└── ", "run_scenario_ladder.py", "run_scenario_ladder.py", False, "# Ladder dashboard entry"))
    
    # Wrap in a pre element for proper formatting
    file_tree_content = html.Pre(
        tree_elements,
        style={
        'fontFamily': '"Consolas", "Monaco", "Courier New", monospace',
        'backgroundColor': '#050505',
        'color': default_theme.text_light,
        'padding': '20px',
        'borderRadius': '5px',
        'border': f'1px solid {default_theme.secondary}',
        'overflowX': 'auto',
        'margin': '0'
        }
    )
    
    return Container(
        id="pdoc-file-tree-section",
        children=[
            html.H2("Interactive Project File Tree", style={"color": default_theme.primary, "marginTop": "0", "fontSize": "1.8em"}),
            html.P("Hover over files and directories to see their descriptions. All components have been successfully migrated to the new package architecture."),
            
            html.Div(
                file_tree_content,
                style={
                    'backgroundColor': '#050505',
                    'padding': '20px',
                    'borderRadius': '5px',
                    'border': f'1px solid {default_theme.secondary}',
                    'overflowX': 'auto'
                }
            )
        ],
        theme=default_theme,
        style={'backgroundColor': default_theme.panel_bg, 'padding': '30px', 'marginBottom': '30px', 'borderRadius': '8px', 'border': f'1px solid {default_theme.secondary}'}
    )

def pdoc_create_architecture_section():
    """Create the architecture section with Mermaid diagrams"""
    
    # Package structure diagram
    package_diagram = """
graph TB
    subgraph "Clean Package Architecture"
        A[lib/] -->|pip install -e .| B[Installed Package]
        B --> C[Clean Imports]
        C --> D["from components import Button"]
        C --> E["from trading.actant.eod import ActantDataService"]
        C --> F["from monitoring.decorators import trace_time"]
    end
    
    subgraph "Old Structure (Eliminated)"
        G[sys.path manipulation] -->|❌| H[Fragile imports]
        I[sys.modules hacks] -->|❌| J[Import errors]
    end
    
    style A fill:#00FF88,stroke:#00CC66,color:#000
    style B fill:#00CC66,stroke:#00FF88,color:#000
    style C fill:#00CC66,stroke:#00FF88,color:#000
    style G fill:#FF4444,stroke:#CC0000,color:#FFF
    style I fill:#FF4444,stroke:#CC0000,color:#FFF
"""
    
    # Data flow diagram
    data_flow_diagram = """
graph LR
    subgraph "Data Sources"
        PM[Pricing Monkey]
        TT[TT REST API]
        JSON[Actant JSON]
    end
    
    subgraph "Processing Layer"
        EOD[EOD Processing]
        SOD[SOD Processing]
        LADDER[Ladder Logic]
    end
    
    subgraph "Storage"
        INPUT[data/input/]
        OUTPUT[data/output/]
        DB[(SQLite DBs)]
    end
    
    subgraph "Presentation"
        DASH1[EOD Dashboard]
        DASH2[Ladder Dashboard]
        DASH3[Main Dashboard]
    end
    
    PM --> SOD
    JSON --> EOD
    TT --> LADDER
    
    EOD --> DB
    SOD --> OUTPUT
    LADDER --> DB
    
    DB --> DASH1
    DB --> DASH2
    OUTPUT --> DASH3
    
    style PM fill:#4A9EFF,stroke:#3388DD,color:#FFF
    style TT fill:#4A9EFF,stroke:#3388DD,color:#FFF
    style JSON fill:#4A9EFF,stroke:#3388DD,color:#FFF
    style EOD fill:#00FF88,stroke:#00CC66,color:#000
    style SOD fill:#00FF88,stroke:#00CC66,color:#000
    style LADDER fill:#00FF88,stroke:#00CC66,color:#000
"""
    
    # Component architecture diagram
    component_diagram = """
classDiagram
    BaseComponent <|-- Button
    BaseComponent <|-- Checkbox
    BaseComponent <|-- ComboBox
    BaseComponent <|-- Container
    BaseComponent <|-- DataTable
    BaseComponent <|-- Graph
    BaseComponent <|-- Grid
    BaseComponent <|-- ListBox
    BaseComponent <|-- Mermaid
    BaseComponent <|-- RadioButton
    BaseComponent <|-- RangeSlider
    BaseComponent <|-- Tabs
    BaseComponent <|-- Toggle
    
    class BaseComponent {
        +id: str
        +theme: Theme
        +render() dict
        #_ensure_id() None
        #_apply_theme_to_component() dict
    }
    
    class Theme {
        +primary: str
        +secondary: str
        +success: str
        +info: str
        +warning: str
        +danger: str
        +base_bg: str
        +panel_bg: str
        +text_light: str
        +text_dark: str
    }
    
    BaseComponent ..> Theme : uses
"""
    
    return Container(
        id="pdoc-architecture-section",
        children=[
            html.H2("Architecture Overview", style={"color": default_theme.primary, "marginTop": "0", "fontSize": "1.8em"}),
            
            html.H3("Package Structure Benefits", style={"color": default_theme.accent, "marginTop": "25px", "fontSize": "1.3em"}),
            Grid(
                id="pdoc-package-diagram-grid",
                children=[
                    Mermaid(theme=default_theme).render(
                        id="pdoc-package-diagram",
                        graph_definition=package_diagram,
                        title="Package Structure Benefits",
                        description="Clean package architecture eliminates import issues"
                    )
                ],
                style={'backgroundColor': '#050505', 'padding': '20px', 'borderRadius': '5px', 'border': f'1px solid {default_theme.secondary}'}
            ).render(),
            
            html.H3("Data Flow Architecture", style={"color": default_theme.accent, "marginTop": "25px", "fontSize": "1.3em"}),
            Grid(
                id="pdoc-data-flow-diagram-grid",
                children=[
                    Mermaid(theme=default_theme).render(
                        id="pdoc-data-flow-diagram",
                        graph_definition=data_flow_diagram,
                        title="Data Flow Architecture",
                        description="Data sources, processing layers, and presentation components"
                    )
                ],
                style={'backgroundColor': '#050505', 'padding': '20px', 'borderRadius': '5px', 'border': f'1px solid {default_theme.secondary}'}
            ).render(),
            
            html.H3("Component Architecture", style={"color": default_theme.accent, "marginTop": "25px", "fontSize": "1.3em"}),
            Grid(
                id="pdoc-component-diagram-grid",
                children=[
                    Mermaid(theme=default_theme).render(
                        id="pdoc-component-diagram",
                        graph_definition=component_diagram,
                        title="Component Architecture",
                        description="UI component inheritance and theme integration"
                    )
                ],
                style={'backgroundColor': '#050505', 'padding': '20px', 'borderRadius': '5px', 'border': f'1px solid {default_theme.secondary}'}
            ).render()
        ],
        theme=default_theme,
        style={'backgroundColor': default_theme.panel_bg, 'padding': '30px', 'marginBottom': '30px', 'borderRadius': '8px', 'border': f'1px solid {default_theme.secondary}'}
    )

def pdoc_create_eod_sod_section():
    """Create the EOD/SOD clarity section with tables"""
    
    # EOD directories table data
    eod_data = [
        {
            "Directory": "lib/trading/actant/eod/",
            "Purpose": "Core EOD business logic and data processing",
            "Key Files": "• data_service.py - Main data processing engine\n• file_manager.py - JSON file discovery and loading"
        },
        {
            "Directory": "apps/dashboards/actant_eod/",
            "Purpose": "EOD Dashboard UI application",
            "Key Files": "• app.py - Dash application with visualizations\n• Uses data_service from lib/trading/actant/eod/"
        },
        {
            "Directory": "scripts/actant_eod/",
            "Purpose": "EOD utility scripts for data processing",
            "Key Files": "• process_actant_json.py - Convert JSON to CSV/SQLite\n• data_integrity_check.py - Verify data pipeline\n• verify_th_pnl.py - Check Th PnL calculations"
        },
        {
            "Directory": "data/input/eod/",
            "Purpose": "Input data storage for EOD",
            "Key Files": "JSON files from Actant (e.g., GE_XCME.ZN_*.json)"
        },
        {
            "Directory": "data/output/eod/",
            "Purpose": "EOD processing outputs",
            "Key Files": "SQLite databases with processed metrics"
        }
    ]
    
    # SOD directories table data
    sod_data = [
        {
            "Directory": "lib/trading/actant/sod/",
            "Purpose": "Core SOD business logic and data transformation",
            "Key Files": "• actant.py - Trade parsing and CSV generation\n• browser_automation.py - Pricing Monkey data retrieval\n• pricing_monkey_adapter.py - Data format conversion\n• futures_utils.py - Contract date calculations"
        },
        {
            "Directory": "apps/dashboards/actant_sod/",
            "Purpose": "SOD Dashboard (placeholder for future development)",
            "Key Files": "Currently empty - reserved for SOD dashboard"
        },
        {
            "Directory": "scripts/actant_sod/",
            "Purpose": "SOD integration scripts",
            "Key Files": "• pricing_monkey_to_actant.py - Production SOD pipeline\n  (Retrieves real PM data → processes → saves CSV)"
        },
        {
            "Directory": "data/input/sod/",
            "Purpose": "Input data storage for SOD",
            "Key Files": "Reference files like SampleZNSOD.csv"
        },
        {
            "Directory": "data/output/sod/",
            "Purpose": "SOD processing outputs",
            "Key Files": "Generated CSV files ready for Actant upload"
        }
    ]
    
    eod_table = DataTable(
        id="pdoc-eod-table",
        data=eod_data,
        columns=[
            {"name": "Directory", "id": "Directory"},
            {"name": "Purpose", "id": "Purpose"},
            {"name": "Key Files", "id": "Key Files"}
        ],
        theme=default_theme,
        style_cell={
            'backgroundColor': default_theme.base_bg,
            'color': default_theme.text_light,
            'textAlign': 'left',
            'padding': '12px',
            'border': f'1px solid {default_theme.secondary}',
            'whiteSpace': 'pre-line'
        },
        style_header={
            'backgroundColor': default_theme.secondary,
            'color': default_theme.primary,
            'fontWeight': '500'
        },
        style_data_conditional=[
            {
                'if': {'column_id': 'Directory'},
                'fontWeight': 'bold'
            }
        ]
    ).render()
    
    sod_table = DataTable(
        id="pdoc-sod-table",
        data=sod_data,
        columns=[
            {"name": "Directory", "id": "Directory"},
            {"name": "Purpose", "id": "Purpose"},
            {"name": "Key Files", "id": "Key Files"}
        ],
        theme=default_theme,
        style_cell={
            'backgroundColor': default_theme.base_bg,
            'color': default_theme.text_light,
            'textAlign': 'left',
            'padding': '12px',
            'border': f'1px solid {default_theme.secondary}',
            'whiteSpace': 'pre-line'
        },
        style_header={
            'backgroundColor': default_theme.secondary,
            'color': default_theme.primary,
            'fontWeight': '500'
        },
        style_data_conditional=[
            {
                'if': {'column_id': 'Directory'},
                'fontWeight': 'bold'
            }
        ]
    ).render()
    
    return Container(
        id="pdoc-eod-sod-section",
        children=[
            html.H2("EOD/SOD Directory Clarity", style={"color": default_theme.primary, "marginTop": "0", "fontSize": "1.8em"}),
            html.P("The project has several directories with EOD/SOD in the name. Here's what each does:"),
            
            html.H3("EOD (End of Day) Directories", style={"color": default_theme.accent, "marginTop": "25px", "fontSize": "1.3em"}),
            eod_table,
            
            html.H3("SOD (Start of Day) Directories", style={"color": default_theme.accent, "marginTop": "25px", "fontSize": "1.3em"}),
            sod_table,
            
            html.H3("Key Distinction", style={"color": default_theme.accent, "marginTop": "25px", "fontSize": "1.3em"}),
            html.Div([
                html.P([html.Strong("EOD (End of Day):")]),
                html.Ul([
                    html.Li("Focuses on analyzing trading day results"),
                    html.Li("Processes complex JSON with shock scenarios and risk metrics"),
                    html.Li("Powers interactive dashboard for P&L and risk visualization"),
                    html.Li("Handles metrics like Delta, Gamma, Vega, Theta across price shocks")
                ]),
                
                html.P([html.Strong("SOD (Start of Day):")]),
                html.Ul([
                    html.Li("Prepares position data for the trading day"),
                    html.Li("Retrieves data from Pricing Monkey via browser automation"),
                    html.Li("Generates CSV files in Actant format for position upload"),
                    html.Li("Simpler data structure focused on trades and positions")
                ])
            ], style={
                'backgroundColor': '#050505',
                'padding': '20px',
                'borderRadius': '5px',
                'marginTop': '20px'
            })
        ],
        theme=default_theme,
        style={'backgroundColor': default_theme.panel_bg, 'padding': '30px', 'marginBottom': '30px', 'borderRadius': '8px', 'border': f'1px solid {default_theme.secondary}'}
    )

def pdoc_create_entry_points_section():
    """Create the entry points summary section"""
    
    entry_points_data = [
        {
            "Script": "run_actant_eod.py",
            "Purpose": "Launch EOD Dashboard",
            "Real/Demo Data": "Real (from JSON files)",
            "Notes": "Interactive dashboard on port 8050"
        },
        {
            "Script": "run_actant_sod.py",
            "Purpose": "Run SOD Processing",
            "Real/Demo Data": "Demo Only",
            "Notes": "Runs actant_main() with test data"
        },
        {
            "Script": "scripts/actant_sod/pricing_monkey_to_actant.py",
            "Purpose": "Real SOD Processing",
            "Real/Demo Data": "Real Data",
            "Notes": "Production script with PM integration"
        },
        {
            "Script": "run_scenario_ladder.py",
            "Purpose": "Launch Ladder Dashboard",
            "Real/Demo Data": "Real (TT API)",
            "Notes": "Price ladder on port 8051"
        }
    ]
    
    entry_points_table = DataTable(
        id="pdoc-entry-points-table",
        data=entry_points_data,
        columns=[
            {"name": "Script", "id": "Script"},
            {"name": "Purpose", "id": "Purpose"},
            {"name": "Real/Demo Data", "id": "Real/Demo Data"},
            {"name": "Notes", "id": "Notes"}
        ],
        theme=default_theme,
        style_cell={
            'backgroundColor': default_theme.base_bg,
            'color': default_theme.text_light,
            'textAlign': 'left',
            'padding': '12px',
            'border': f'1px solid {default_theme.secondary}'
        },
        style_header={
            'backgroundColor': default_theme.secondary,
            'color': default_theme.primary,
            'fontWeight': '500'
        },
        style_data_conditional=[
            {
                'if': {'filter_query': '{Real/Demo Data} = "Demo Only"', 'column_id': 'Real/Demo Data'},
                'color': '#FF9900'
            },
            {
                'if': {'filter_query': '{Real/Demo Data} = "Real Data"', 'column_id': 'Real/Demo Data'},
                'color': default_theme.primary
            },
            {
                'if': {'column_id': 'Script'},
                'fontFamily': '"Consolas", "Monaco", "Courier New", monospace'
            }
        ]
    ).render()
    
    return Container(
        id="pdoc-entry-points-section",
        children=[
            html.H2("Entry Points Summary", style={"color": default_theme.primary, "marginTop": "0", "fontSize": "1.8em"}),
            entry_points_table
        ],
        theme=default_theme,
        style={'backgroundColor': default_theme.panel_bg, 'padding': '30px', 'marginBottom': '30px', 'borderRadius': '8px', 'border': f'1px solid {default_theme.secondary}'}
    )
def create_project_documentation_content():
    """Create the complete Project Documentation page content"""
    
    # Get Mermaid diagrams from create_mermaid_tab function
    # First flowchart - Project Architecture
    project_flowchart = """
    flowchart LR
        %% ============ Execution layer ============
        subgraph ExecutionLayer["Execution Layer"]
            tt["TT (futures algo)"]
            cmeDirect["CME Direct (options)"]
            cme["CME Exchange"]

            tt -->|futures orders| cme
            
        end

        %% ============ Data & analytics stack ============
        md["Market Data feed"]
        pricing["Pricing Monkey"]
        actant["ACTANT"]
        greeks["Greeks"]
        position["Position"]
        optimizer["Optimizer"]
        dashboard["Dashboard"]

        %% ----- Market-data distribution -----
        md --> tt
        md --> | options orders |cmeDirect
        md --> actant
        md --> pricing

        %% ----- Exchange & options → risk engine -----
        cme -->|positions| actant
        cmeDirect -->|positions| actant

        %% ----- Risk & valuation flow -----
        actant -->|analytics| greeks
        actant -->|positions| position
        pricing --> greeks
        pricing --> dashboard

        %% ----- Optimisation loop -----
        greeks --> optimizer
        position --> optimizer
        optimizer --> dashboard
    """
    
    # Second flowchart - Scenario Ladder Architecture
    scenario_ladder_flowchart = """
    flowchart LR
      %% Execution Layer
      subgraph TTExecution["Execution Layer"]
        A[TT ADL Algorithm Lab] -->|Executes trades| B[CME Exchange]
      end

      %% Data & Analytics Stack
      subgraph DataStack["Data & Analytics Stack"]
        B -->|Market & Position Data| C["Actant  (Position, Risk, Market Data)"]
        D[Pricing Monkey] -->|Spot Price| E["Backend"]
        C -->|Processed Position via SFTP| E
      end

      %% REST API feed
      A -->|Working Orders via TT REST API| E

      %% In-app calculations
      E -->|"Calculates PnL, Risk, Breakeven, and (later) Gamma"|E

      %% UI Layer
      F["UI (Simulated Ladder)"]
      E --> F
    """
    
    # Create Doxygen button - using a simple HTML anchor styled as a button
    doxygen_button = html.A(
        "📖 View API Documentation",
        href="/doxygen-docs",
        target="_blank",
        style={
            'display': 'inline-block',
            'backgroundColor': default_theme.accent,
            'color': 'white',
            'fontSize': '16px',
            'padding': '10px 20px',
            'marginBottom': '20px',
            'textDecoration': 'none',
            'borderRadius': '4px',
            'cursor': 'pointer',
            'border': 'none'
        }
    )
    
    return Container(
        id="pdoc-main-container",
        children=[
            # Header
            html.Div([
                html.H1("UIKitXv2 Project Documentation", style={
                    "color": default_theme.primary,
                    "fontSize": "2.5em",
                    "margin": "0",
                    "fontWeight": "600",
                    "textAlign": "center"
                }),
                html.Div("Architecture Diagrams & Interactive File Tree", style={
                    "color": default_theme.text_light,
                    "marginTop": "10px",
                    "fontSize": "1.2em",
                    "textAlign": "center",
                    "opacity": "0.8"
                })
            ], style={
                "textAlign": "center",
                "padding": "40px 0",
                "borderBottom": f"1px solid {default_theme.secondary}",
                "marginBottom": "40px"
            }),
            
            # Doxygen Documentation Button
            html.Div([
                doxygen_button
            ], style={'textAlign': 'center', 'marginBottom': '30px'}),
            
            # Mermaid Diagrams Section
            html.Div([
                html.H2("System Architecture Diagrams", style={"color": default_theme.primary, "marginBottom": "30px", "fontSize": "1.8em"}),
                
                # First diagram
                Grid(
                    id="pdoc-project-architecture-grid",
                    children=[
                        Mermaid(theme=default_theme).render(
                            id="pdoc-project-architecture-diagram",
                            graph_definition=project_flowchart,
                            title="Project Architecture",
                            description="System architecture diagram showing data flow and component relationships"
                        )
                    ],
                    style={'backgroundColor': default_theme.panel_bg, 'padding': '15px', 'borderRadius': '5px'}
                ).render(),
                
                # Second diagram
                Grid(
                    id="pdoc-scenario-ladder-grid",
                    children=[
                        Mermaid(theme=default_theme).render(
                            id="pdoc-scenario-ladder-diagram",
                            graph_definition=scenario_ladder_flowchart,
                            title="Scenario Ladder Architecture",
                            description="Architecture diagram showing the flow of data into our simulated ladder"
                        )
                    ],
                    style={'backgroundColor': default_theme.panel_bg, 'padding': '15px', 'borderRadius': '5px', 'marginTop': '20px'}
                ).render()
            ], style={'marginBottom': '40px'}),
            
            # File tree and other architecture sections
            pdoc_create_file_tree_section().render(),
            pdoc_create_architecture_section().render()
        ],
        theme=default_theme,
        style={'padding': '15px'}
    ).render()

# --- End Project Documentation Functions ---

# --- Scenario Ladder Helper Functions ---
def scl_parse_and_convert_pm_price(price_str):
    """
    Parse a price string from Pricing Monkey format and convert it to both decimal and special string format.
    
    Handles formats like:
    - "110-08.5" (with decimal)
    - "110-17" (without decimal)
    """
    # Use the robust parse_treasury_price function from price_parser module
    decimal_price = parse_treasury_price(price_str)
    
    if decimal_price is None:
        logger.error(f"Failed to parse price string: '{price_str}'")
        return None, None
        
    # Convert to special string format using the standard function
    special_string_price = decimal_to_tt_bond_format(decimal_price)
    
    logger.info(f"Converted '{price_str}' to decimal: {decimal_price}, special format: '{special_string_price}'")
    return decimal_price, special_string_price

def scl_convert_tt_special_format_to_decimal(price_str):
    """
    Convert a TT special string format price (e.g. "110'065") to decimal.
    """
    # Clean the string (trim whitespace, handle potential CR/LF)
    price_str = price_str.strip() if price_str else ""
    
    # Pattern for "XXX'YYZZ" format where YY is 32nds and ZZ is optional fractional part
    pattern = r"(\d+)'(\d{2,4})"
    match = re.match(pattern, price_str)
    
    if not match:
        logger.error(f"Failed to parse TT special format price: '{price_str}'")
        return None
        
    whole_points = int(match.group(1))
    fractional_str = match.group(2)
    
    if len(fractional_str) == 2:  # Just 32nds, no fraction
        thirty_seconds_part = int(fractional_str)
        fraction_part = 0
    elif len(fractional_str) == 3:  # 32nds with single-digit fraction
        thirty_seconds_part = int(fractional_str[0:2])
        fraction_part = int(fractional_str[2]) / 10.0
    elif len(fractional_str) == 4:  # 32nds with two-digit fraction
        thirty_seconds_part = int(fractional_str[0:2])
        fraction_part = int(fractional_str[2:4]) / 100.0
    else:
        logger.error(f"Unexpected fractional format: '{fractional_str}'")
        return None

    # Calculate decimal: whole_points + (thirty_seconds_part + fraction_part) / 32.0
    decimal_price = whole_points + (thirty_seconds_part + fraction_part) / 32.0
    
    logger.info(f"Converted '{price_str}' to decimal: {decimal_price}")
    return decimal_price

def scl_load_actant_zn_fills(csv_filepath):
    """
    Load ZN futures fill data from Actant CSV file.
    """
    import pandas as pd
    
    logger.info(f"Loading Actant ZN fills from: {csv_filepath}")
    try:
        fills_df = pd.read_csv(csv_filepath)
        
        # Filter for ZN futures only
        zn_future_fills = fills_df[(fills_df['ASSET'] == 'ZN') & 
                                   (fills_df['PRODUCT_CODE'] == 'FUTURE')]
        
        if zn_future_fills.empty:
            logger.warning("No ZN futures found in Actant data")
            return []
            
        logger.info(f"Found {len(zn_future_fills)} ZN future fills in Actant data")
        
        # Process each fill
        processed_fills = []
        for _, row in zn_future_fills.iterrows():
            # Convert price from TT special format to decimal
            price_str = row.get('PRICE_TODAY')
            price = scl_convert_tt_special_format_to_decimal(price_str)
            
            if price is None:
                logger.warning(f"Skipping fill with invalid price: {price_str}")
                continue
                
            # Get quantity and adjust sign based on long/short
            quantity = float(row.get('QUANTITY', 0))
            if pd.isna(quantity) or quantity == 0:
                logger.warning(f"Skipping fill with invalid quantity: {quantity}")
                continue
                
            side = row.get('LONG_SHORT', '')
            if side == 'S':  # Short position
                quantity = -quantity
            
            processed_fills.append({
                'price': price,
                'qty': int(quantity)  # Ensure quantity is an integer
            })
            
        logger.info(f"Processed {len(processed_fills)} valid ZN future fills")
        return processed_fills
        
    except Exception as e:
        logger.error(f"Error loading Actant ZN fills: {e}")
        return []

def scl_calculate_baseline_from_actant_fills(actant_fills, spot_decimal_price):
    """
    Calculate baseline position and P&L at spot price based on Actant fill data.
    """
    if not actant_fills or spot_decimal_price is None:
        logger.info("No fills or invalid spot price - using zero baseline")
        return {'base_pos': 0, 'base_pnl': 0.0}

    # Constants for P&L calculation
    BP_DECIMAL_PRICE_CHANGE = 0.0625  # 2 * (1/32) = 1/16 = 0.0625
    DOLLARS_PER_BP = 62.5  # $62.5 per basis point

    # Sort fills by price (ascending) to process them in sequence
    sorted_fills = sorted(actant_fills, key=lambda x: x['price'])
    
    current_position = 0
    realized_pnl = 0.0
    
    # Initialize evaluation price with the first fill price
    if sorted_fills:
        current_eval_price = sorted_fills[0]['price']
    else:
        return {'base_pos': 0, 'base_pnl': 0.0}
    
    logger.info(f"Starting baseline P&L calculation from Actant fills")
    logger.info(f"Starting price (first fill): {current_eval_price}")
    logger.info(f"Target spot price: {spot_decimal_price}")
    
    for fill in sorted_fills:
        fill_price = fill['price']
        fill_qty = fill['qty']
        
        # P&L from price movement with current position
        price_movement = fill_price - current_eval_price
        if abs(price_movement) > 0.000001:  # Avoid floating point comparison issues
            bp_movement = price_movement / BP_DECIMAL_PRICE_CHANGE
            pnl_increment = bp_movement * DOLLARS_PER_BP * current_position
            realized_pnl += pnl_increment
            
            logger.debug(f"Position before fill: {current_position}")
            logger.debug(f"Price movement: {current_eval_price} to {fill_price} = {price_movement:.7f}")
            logger.debug(f"P&L increment: {bp_movement:.3f} BPs * ${DOLLARS_PER_BP}/BP * {current_position} = ${pnl_increment:.2f}")
        
        # Update position with current fill
        current_position += fill_qty
        logger.debug(f"Fill executed: {'BUY' if fill_qty > 0 else 'SELL'} {abs(fill_qty)} @ {fill_price}")
        logger.debug(f"New position after fill: {current_position}")
        
        # Update evaluation price for next iteration
        current_eval_price = fill_price
    
    # Calculate P&L adjustment from last fill to spot price
    price_movement_to_spot = spot_decimal_price - current_eval_price
    if abs(price_movement_to_spot) > 0.000001:
        bp_movement_to_spot = price_movement_to_spot / BP_DECIMAL_PRICE_CHANGE
        pnl_increment_to_spot = bp_movement_to_spot * DOLLARS_PER_BP * current_position
        realized_pnl += pnl_increment_to_spot
        
        logger.debug(f"Final price movement to spot: {current_eval_price} to {spot_decimal_price} = {price_movement_to_spot:.7f}")
        logger.debug(f"Final P&L increment to spot: ${pnl_increment_to_spot:.2f}")
    
    result = {
        'base_pos': current_position,
        'base_pnl': round(realized_pnl, 2)
    }
    logger.info(f"Baseline Result: Position = {result['base_pos']}, P&L at spot = ${result['base_pnl']:.2f}")
    return result

def scl_create_scenario_ladder_content():
    """Create the Scenario Ladder page content"""
    # Constants for data paths - using project structure
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    MOCK_DATA_FILE = os.path.join(project_root, "data", "input", "ladder", "my_working_orders_response.json")
    ACTANT_CSV_FILE = os.path.join(project_root, "data", "input", "sod", "SampleSOD.csv")
    ACTANT_DB_FILEPATH = os.path.join(project_root, "data", "output", "ladder", "actant_data.db")
    
    # Mock spot price setup
    MOCK_SPOT_PRICE_STR = "110-08.5"
    MOCK_SPOT_DECIMAL_PRICE, MOCK_SPOT_SPECIAL_STRING_PRICE = scl_parse_and_convert_pm_price(MOCK_SPOT_PRICE_STR)
    
    return Container(
        id="scl-main-container",
        children=[
            # Stores for state management
            dcc.Store(id='scl-scenario-ladder-store', data={'initial_load_trigger': True}),
            dcc.Store(id='scl-spot-price-store', data={
                'decimal_price': MOCK_SPOT_DECIMAL_PRICE if MOCK_SPOT_DECIMAL_PRICE is not None else None,
                'special_string_price': MOCK_SPOT_SPECIAL_STRING_PRICE if MOCK_SPOT_SPECIAL_STRING_PRICE is not None else None
            }),
            dcc.Store(id='scl-baseline-store', data={'base_pos': 0, 'base_pnl': 0.0}),
            dcc.Store(id='scl-demo-mode-store', data={'demo_mode': True}),  # Add demo mode store, default to demo
            
            # Header
            html.H2("Scenario Ladder", style={"textAlign": "center", "color": default_theme.primary, "marginBottom": "20px"}),
            
            # Demo Mode Toggle
            html.Div([
                html.Div([
                    html.P("Data Source:", style={
                        "color": default_theme.text_light, 
                        "marginRight": "10px", 
                        "marginBottom": "0",
                        "display": "inline-block"
                    }),
                    html.Div([
                        Button(
                            id="scl-demo-mode-btn",
                            label="Demo Mode",
                            theme=default_theme,
                            n_clicks=0,
                            style={
                                'borderTopRightRadius': '0',
                                'borderBottomRightRadius': '0',
                                'borderRight': 'none',
                                'backgroundColor': default_theme.primary  # Start with demo selected
                            }
                        ).render(),
                        Button(
                            id="scl-live-mode-btn",
                            label="Live Data",
                            theme=default_theme,
                            n_clicks=0,
                            style={
                                'borderTopLeftRadius': '0',
                                'borderBottomLeftRadius': '0',
                                'backgroundColor': default_theme.panel_bg
                            }
                        ).render()
                    ], style={"display": "flex", "marginRight": "20px"})
                ], style={"display": "flex", "alignItems": "center"})
            ], style={'display': 'flex', 'justifyContent': 'center', 'marginBottom': '20px'}),
            
            # Refresh button
            html.Div([
                Button(id="scl-refresh-data-button", label="Refresh Data", theme=default_theme).render()
            ], style={'display': 'flex', 'justifyContent': 'center', 'marginBottom': '20px'}),
            
            # Baseline display
            html.Div(id='scl-baseline-display', style={"textAlign": "center", "color": default_theme.primary, "marginBottom": "10px"}),
            
            # Error displays
            html.Div(id='scl-spot-price-error-div', style={"textAlign": "center", "color": default_theme.danger, "marginBottom": "10px"}),
            html.Div(id='scl-scenario-ladder-message', children="Loading working orders...", 
                    style={"textAlign": "center", "color": default_theme.text_light, "marginBottom": "20px"}),
            
            # Table container
            html.Div(
                id="scl-scenario-ladder-table-wrapper",
                children=[
                    Grid(
                        id="scl-scenario-ladder-grid",
                        children=[
                            DataTable(
                                id='scl-scenario-ladder-table',
                                columns=[
                                    {'name': 'Working Qty', 'id': 'my_qty', "type": "numeric"},
                                    {'name': 'Price', 'id': 'price', "type": "text"},
                                    {'name': 'Projected PnL', 'id': 'projected_pnl', "type": "numeric", "format": {"specifier": "$,.2f"}},
                                    {'name': 'Pos', 'id': 'position_debug', "type": "numeric"},
                                    {'name': 'Risk', 'id': 'risk', "type": "numeric"},
                                    {'name': 'Breakeven', 'id': 'breakeven', "type": "numeric", "format": {"specifier": ".2f"}}
                                ],
                                data=[],  # Start with no data
                                theme=default_theme,
                                style_cell={
                                    'backgroundColor': default_theme.base_bg, 
                                    'color': default_theme.text_light, 
                                    'font-family': 'monospace',
                                    'fontSize': '12px', 
                                    'height': '22px', 
                                    'textAlign': 'center', 
                                    'padding': '2px', 
                                    'border': f'1px solid {default_theme.secondary}'
                                },
                                style_header={
                                    'backgroundColor': default_theme.panel_bg, 
                                    'color': default_theme.primary, 
                                    'height': '28px',
                                    'padding': '4px', 
                                    'textAlign': 'center', 
                                    'fontWeight': 'bold', 
                                    'border': f'1px solid {default_theme.secondary}'
                                },
                                style_data_conditional=[
                                    # Buy side orders (blue)
                                    {
                                        'if': {'filter_query': '{working_qty_side} = "1"', 'column_id': 'my_qty'},
                                        'color': default_theme.secondary
                                    },
                                    # Sell side orders (red)
                                    {
                                        'if': {'filter_query': '{working_qty_side} = "2"', 'column_id': 'my_qty'},
                                        'color': default_theme.danger
                                    },
                                    # Exact spot price (green background)
                                    {
                                        'if': {'filter_query': '{is_exact_spot} = 1', 'column_id': 'price'},
                                        'backgroundColor': default_theme.success,
                                        'color': 'white'
                                    },
                                    # Positive PnL (green)
                                    {
                                        'if': {'filter_query': '{projected_pnl} > 0', 'column_id': 'projected_pnl'},
                                        'color': default_theme.success
                                    },
                                    # Negative PnL (red)
                                    {
                                        'if': {'filter_query': '{projected_pnl} < 0', 'column_id': 'projected_pnl'},
                                        'color': default_theme.danger
                                    },
                                    # Long position (blue)
                                    {
                                        'if': {'filter_query': '{position_debug} > 0', 'column_id': 'position_debug'},
                                        'color': default_theme.secondary
                                    },
                                    # Short position (red)
                                    {
                                        'if': {'filter_query': '{position_debug} < 0', 'column_id': 'position_debug'},
                                        'color': default_theme.danger
                                    },
                                    # Long risk (blue)
                                    {
                                        'if': {'filter_query': '{risk} > 0', 'column_id': 'risk'},
                                        'color': default_theme.secondary
                                    },
                                    # Short risk (red)
                                    {
                                        'if': {'filter_query': '{risk} < 0', 'column_id': 'risk'},
                                        'color': default_theme.danger
                                    },
                                    # Positive breakeven (green)
                                    {
                                        'if': {'filter_query': '{breakeven} > 0', 'column_id': 'breakeven'},
                                        'color': default_theme.success
                                    },
                                    # Negative breakeven (red)
                                    {
                                        'if': {'filter_query': '{breakeven} < 0', 'column_id': 'breakeven'},
                                        'color': default_theme.danger
                                    }
                                ],
                                page_size=100
                            ).render()
                        ],
                        theme=default_theme
                    ).render()
                ],
                style={'display': 'none'}  # Initially hidden until data loads
            )
        ],
        theme=default_theme,
        style={'padding': '15px', 'backgroundColor': default_theme.base_bg, 'minHeight': '80vh'}
    ).render()

def scl_update_data_with_spot_price(existing_data, spot_price_data, base_position=0, base_pnl=0.0):
    """Update existing ladder data with spot price indicators and P&L calculations"""
    if not existing_data or not spot_price_data:
        return existing_data
    
    spot_decimal = spot_price_data.get('decimal_price')
    if spot_decimal is None:
        return existing_data
    
    # Constants for calculations
    PRICE_INCREMENT_DECIMAL = 1.0 / 64.0
    BP_DECIMAL_PRICE_CHANGE = 0.0625  # 2 * (1/32) = 1/16 = 0.0625  
    DOLLARS_PER_BP = 62.5  # $62.5 per basis point
    
    epsilon = PRICE_INCREMENT_DECIMAL / 100.0
    
    # Process data in two passes: above spot and below spot
    # Sort by decimal_price_val in descending order (highest prices first)
    sorted_data = sorted(existing_data, key=lambda x: x.get('decimal_price_val', 0), reverse=True)
    
    # Initialize position tracking
    current_position = base_position
    
    # First pass: Process levels from highest price down to spot (above spot)
    spot_found = False
    for row in sorted_data:
        row_price = row.get('decimal_price_val', 0)
        
        # Check if this is the exact spot price
        if abs(row_price - spot_decimal) < epsilon:
            row['is_exact_spot'] = 1
            row['is_below_spot'] = 0
            row['is_above_spot'] = 0
            spot_found = True
        elif row_price > spot_decimal:
            # Above spot price
            row['is_exact_spot'] = 0
            row['is_below_spot'] = 0
            row['is_above_spot'] = 1
        else:
            # Below spot price  
            row['is_exact_spot'] = 0
            row['is_below_spot'] = 1
            row['is_above_spot'] = 0
        
        # Update position based on working orders at this level
        my_qty = row.get('my_qty', '')
        working_qty_side = row.get('working_qty_side', '')
        
        if isinstance(my_qty, (int, float)) and my_qty > 0 and working_qty_side:
            if working_qty_side == '1':  # Buy orders
                current_position += my_qty
            elif working_qty_side == '2':  # Sell orders  
                current_position -= my_qty
        
        # Calculate projected P&L at this price level
        price_diff = row_price - spot_decimal
        bp_movement = price_diff / BP_DECIMAL_PRICE_CHANGE
        projected_pnl = base_pnl + (bp_movement * DOLLARS_PER_BP * base_position)
        
        # Calculate position AFTER orders at this level are executed
        row['position_debug'] = int(current_position)
        row['projected_pnl'] = round(projected_pnl, 2)
        
        # Calculate risk (DV01 risk = position * 15.625)
        row['risk'] = round(current_position * 15.625, 1)
        
        # Calculate breakeven (simplified - could be enhanced)
        if base_position != 0:
            row['breakeven'] = round(projected_pnl / abs(base_position), 2)
        else:
            row['breakeven'] = 0
    
    return sorted_data

def scl_fetch_spot_price_from_pm():
    """
    Fetch spot price from Pricing Monkey using UI automation.
    Returns mock data when USE_MOCK_DATA is True.
    """
    import time
    import webbrowser
    import pyperclip
    from pywinauto.keyboard import send_keys
    
    # Constants
    PM_URL = "https://pricingmonkey.com/b/e9172aaf-2cb4-4f2c-826d-92f57d3aea90"
    PM_WAIT_FOR_BROWSER_OPEN = 3.0
    PM_WAIT_BETWEEN_ACTIONS = 0.5
    PM_WAIT_FOR_COPY = 1.0
    PM_KEY_PRESS_PAUSE = 0.1
    USE_MOCK_DATA = False  # Can be toggled for testing
    
    # Mock data fallback
    MOCK_SPOT_PRICE_STR = "110-08.5"
    MOCK_SPOT_DECIMAL_PRICE, MOCK_SPOT_SPECIAL_STRING_PRICE = scl_parse_and_convert_pm_price(MOCK_SPOT_PRICE_STR)
    
    if USE_MOCK_DATA:
        logger.info("Using mock spot price for refresh")
        if MOCK_SPOT_DECIMAL_PRICE is not None:
            return {
                'decimal_price': MOCK_SPOT_DECIMAL_PRICE,
                'special_string_price': MOCK_SPOT_SPECIAL_STRING_PRICE
            }, ""  # Empty error message
        else:
            return {
                'decimal_price': None,
                'special_string_price': None
            }, "Error: Mock spot price not initialized."
    
    logger.info("Fetching spot price from Pricing Monkey")
    
    try:
        # Open the Pricing Monkey URL
        logger.info(f"Opening URL: {PM_URL}")
        webbrowser.open(PM_URL, new=2)
        time.sleep(PM_WAIT_FOR_BROWSER_OPEN)
        
        # Navigate to the target element using keyboard shortcuts
        logger.info("Pressing TAB 10 times to navigate")
        send_keys('{TAB 10}', pause=PM_KEY_PRESS_PAUSE, with_spaces=True)
        time.sleep(PM_WAIT_BETWEEN_ACTIONS)
        
        logger.info("Pressing DOWN to select price")
        send_keys('{DOWN}', pause=PM_KEY_PRESS_PAUSE)
        time.sleep(PM_WAIT_BETWEEN_ACTIONS)
        
        # Copy the value to clipboard
        logger.info("Copying to clipboard")
        send_keys('^c', pause=PM_KEY_PRESS_PAUSE)
        time.sleep(PM_WAIT_FOR_COPY)
        
        # Get the clipboard content
        clipboard_content = pyperclip.paste()
        logger.info(f"Clipboard content: '{clipboard_content}'")
        
        # Close the browser tab
        logger.info("Closing browser tab")
        send_keys('^w', pause=PM_KEY_PRESS_PAUSE)
        time.sleep(PM_WAIT_BETWEEN_ACTIONS)
        
        # Process the clipboard content
        decimal_price, special_string_price = scl_parse_and_convert_pm_price(clipboard_content)
        
        if decimal_price is None:
            error_msg = f"Failed to parse price from clipboard: '{clipboard_content}'"
            logger.error(error_msg)
            return {'decimal_price': None, 'special_string_price': None}, error_msg
        
        # Return the parsed data
        return {
            'decimal_price': decimal_price,
            'special_string_price': special_string_price
        }, ""
        
    except Exception as e:
        error_msg = f"Error fetching spot price: {str(e)}"
        logger.error(error_msg)
        return {'decimal_price': None, 'special_string_price': None}, error_msg

# --- End Scenario Ladder Helper Functions ---

# --- FRGMonitor Helper Functions ---
def format_number_strip_zeros(value):
    """Format a number by stripping trailing zeros after decimal point.
    
    Args:
        value: Numeric value or None
        
    Returns:
        String representation without trailing zeros, or empty string if None
    """
    if value is None or pd.isna(value):
        return ""
    
    # Convert to string with enough decimal places
    formatted = f"{value:.6f}"
    
    # Strip trailing zeros and decimal point if no fractional part
    if '.' in formatted:
        formatted = formatted.rstrip('0').rstrip('.')
    
    return formatted

# --- FRGMonitor Tab ---
def create_frg_monitor_content():
    """Create FRGMonitor with positions and daily_positions tables from trades.db"""
    
    # Header
    header = html.H4(
        "FRGMonitor", 
        style={
            "color": default_theme.primary, 
            "marginBottom": "20px", 
            "textAlign": "center"
        }
    )
    
    # --- Simple auto-refresh components ---
    # Poll FRG data at 300 ms for lower-latency UI updates
    refresh_interval = dcc.Interval(id='frg-refresh-interval', interval=300, n_intervals=0)
    
    # This store holds the previous data hash to detect changes
    data_hash_store = dcc.Store(id='frg-data-hash-store', data={'hash': None})
    # --- End New Components ---

    # Create tab contents
    positions_content = create_positions_tab_content()
    daily_positions_content = create_daily_positions_tab_content()
    
    # Use wrapped Tabs component
    tabs = Tabs(
        id="frg-monitor-tabs",
        tabs=[
            ("Live Positions", positions_content),
            ("Daily Positions", daily_positions_content)
        ],
        active_tab="tab-0",
        theme=default_theme
    )
    
    # Main container
    container = Container(
        id="frg-monitor-container",
        children=[
            header,
            tabs.render(),
            # Add the auto-refresh components to the layout
            refresh_interval,
            data_hash_store
        ],
        style={"padding": "10px"},  # Reduced padding for more width
        fluid=True  # Make the main container full-width
    )
    
    return container.render()
def create_positions_tab_content():
    """Create positions table with real-time updates"""
    
    # Status and update info
    info_row = html.Div([
        html.Span("Status: ", style={"fontWeight": "bold"}),
        html.Span("Initializing...", id="positions-status-text"),
        html.Span(" | Last Update: ", style={"fontWeight": "bold", "marginLeft": "20px"}),
        html.Span("--", id="positions-last-update-text"),
        html.Span(" (Chicago time)", style={"fontSize": "0.8rem", "fontStyle": "italic", "marginLeft": "10px"})
    ], style={"marginBottom": "15px", "fontSize": "0.9rem"})
    
    # DataTable
    positions_table = DataTable(
        id="positions-table",
        columns=[],
        data=[],
        theme=default_theme,
        page_size=20,
        style_table={'overflowX': 'visible', 'width': '100%'},
        style_cell={'textAlign': 'center', 'padding': '5px', 'fontSize': '0.85rem'},
        style_data_conditional=[
            # Aggregate rows styling
            {
                'if': {'filter_query': '{instrument_type} = "AGGREGATE"'},
                'backgroundColor': 'rgba(0, 0, 0, 0.05)',
                'fontWeight': 'bold',
                'borderTop': '2px solid #333',
                'borderBottom': '2px solid #333'
            },
            # Positive P&L green
            {
                'if': {'filter_query': '{pnl_live} > 0', 'column_id': 'pnl_live'},
                'color': default_theme.success
            },
            {
                'if': {'filter_query': '{non_gamma_lifo} > 0', 'column_id': 'non_gamma_lifo'},
                'color': default_theme.success
            },
            {
                'if': {'filter_query': '{gamma_lifo} > 0', 'column_id': 'gamma_lifo'},
                'color': default_theme.success
            },
            {
                'if': {'filter_query': '{pnl_close} > 0', 'column_id': 'pnl_close'},
                'color': default_theme.success
            },
            # Negative P&L red
            {
                'if': {'filter_query': '{pnl_live} < 0', 'column_id': 'pnl_live'},
                'color': default_theme.danger
            },
            {
                'if': {'filter_query': '{non_gamma_lifo} < 0', 'column_id': 'non_gamma_lifo'},
                'color': default_theme.danger
            },
            {
                'if': {'filter_query': '{gamma_lifo} < 0', 'column_id': 'gamma_lifo'},
                'color': default_theme.danger
            },
            {
                'if': {'filter_query': '{pnl_close} < 0', 'column_id': 'pnl_close'},
                'color': default_theme.danger
            }
        ]
    )
    
    # Container
    container = Container(
        id="positions-tab-container",
        children=[
            info_row,
            positions_table.render()
        ],
        theme=default_theme,
        style={"padding": "10px", "width": "100%", "maxWidth": "100%"},  # Use full width and override any max-width
        fluid=True
    )
    
    return container.render()

def create_daily_positions_tab_content():
    """Create daily positions table with real-time updates"""
    
    # Status and update info
    info_row = html.Div([
        html.Span("Status: ", style={"fontWeight": "bold"}),
        html.Span("Initializing...", id="daily-positions-status-text"),
        html.Span(" | Last Update: ", style={"fontWeight": "bold", "marginLeft": "20px"}),
        html.Span("--", id="daily-positions-last-update-text"),
        html.Span(" (Chicago time)", style={"fontSize": "0.8rem", "fontStyle": "italic", "marginLeft": "10px"}),
        html.Span(" | Inception to Date P&L: ", style={"fontWeight": "bold", "marginLeft": "20px"}),
        html.Span("--", id="daily-positions-inception-pnl")
    ], style={"marginBottom": "15px", "fontSize": "0.9rem"})
    
    # DataTable
    daily_table = DataTable(
        id="daily-positions-table",
        columns=[],
        data=[],
        theme=default_theme,
        page_size=20,
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'center', 'padding': '8px'},
        style_data_conditional=[
            # Positive P&L green
            {
                'if': {'filter_query': '{realized_pnl} > 0', 'column_id': 'realized_pnl'},
                'color': default_theme.success
            },
            {
                'if': {'filter_query': '{unrealized_pnl} > 0', 'column_id': 'unrealized_pnl'},
                'color': default_theme.success
            },
            # Negative P&L red
            {
                'if': {'filter_query': '{realized_pnl} < 0', 'column_id': 'realized_pnl'},
                'color': default_theme.danger
            },
            {
                'if': {'filter_query': '{unrealized_pnl} < 0', 'column_id': 'unrealized_pnl'},
                'color': default_theme.danger
            }
        ]
    )
    
    # Container
    container = Container(
        id="daily-positions-tab-container",
        children=[
            info_row,
            daily_table.render()
        ],
        theme=default_theme
    )
    
    return container.render()

# --- End FRGMonitor Tab ---

# --- Actant EOD Helper Functions (Placeholder) ---
def aeod_create_dashboard_layout():
    """Create the main dashboard layout with new design."""
    return Container(
        id="aeod-main-layout",
        children=[
            html.H2("Actant EOD Dashboard", style={"textAlign": "center", "color": default_theme.primary, "marginBottom": "20px"}),
            html.P("Advanced trading analytics dashboard successfully integrated", 
                  style={"textAlign": "center", "color": default_theme.text_light, "marginBottom": "20px"}),
            html.P("Full implementation in progress - placeholder for complex dashboard layout", 
                  style={"textAlign": "center", "color": default_theme.secondary})
        ],
        theme=default_theme,
        style={'padding': '50px', 'textAlign': 'center'}
    ).render()

def aeod_create_actant_eod_content():
    """Create the Actant EOD page content"""
    return aeod_create_dashboard_layout()

# --- End Actant EOD Helper Functions ---

# --- Sidebar Navigation System ---
def create_sidebar():
    """Create the unified sidebar navigation"""
    sidebar_items = [
        {"id": "nav-frg-monitor", "label": "FRGMonitor", "icon": "📊"},  # Moved to top
        {"id": "nav-pricing-monkey", "label": "Option Hedging", "icon": "💰"},
        {"id": "nav-analysis", "label": "Option Comparison", "icon": "📊"},
        {"id": "nav-greek-analysis", "label": "Greek Analysis", "icon": "📈"},
        {"id": "nav-scenario-ladder", "label": "Scenario Ladder", "icon": "📊"},
        {"id": "nav-actant-eod", "label": "Actant EOD", "icon": "📈"},
            {"id": "nav-actant-pnl", "label": "Actant PnL", "icon": "📉"},
    # PnL tracking removed - Phase 3 clean slate
        {"id": "nav-spot-risk", "label": "Spot Risk", "icon": "🎯"},
        {"id": "nav-observatory", "label": "Observatory", "icon": "👀"},
        {"id": "nav-project-docs", "label": "Project Documentation", "icon": "📚"},
        {"id": "nav-logs", "label": "Logs (Legacy)", "icon": "📋"}  # Mark as legacy
    ]
    
    sidebar_style = {
        'position': 'fixed',
        'top': 0,
        'left': 0,
        'bottom': 0,
        'width': '240px',
        'padding': '20px 0',
        'backgroundColor': default_theme.panel_bg,
        'borderRight': f'2px solid {default_theme.secondary}',
        'overflowY': 'auto',
        'zIndex': 1000
    }
    
    # Header in sidebar
    header_style = {
        'color': default_theme.primary,
        'fontSize': '1.2rem',
        'fontWeight': '600',
        'textAlign': 'center',
        'padding': '0 20px 20px 20px',
        'borderBottom': f'1px solid {default_theme.secondary}',
        'marginBottom': '20px'
    }
    
    # Navigation button base style
    nav_button_base_style = {
        'width': '100%',
        'textAlign': 'left',
        'border': 'none',
        'borderRadius': '0',
        'marginBottom': '2px',
        'padding': '12px 20px',
        'fontSize': '0.9rem',
        'display': 'flex',
        'alignItems': 'center',
        'gap': '10px',
        'transition': 'all 0.2s ease',
        'cursor': 'pointer'
    }
    
    # Create navigation buttons
    nav_buttons = []
    for item in sidebar_items:
        button_style = {
            **nav_button_base_style,
            'backgroundColor': default_theme.panel_bg,
            'color': default_theme.text_light,
            'borderLeft': f'3px solid transparent'
        }
        
        button = html.Button([
            html.Span(item["icon"], style={'fontSize': '1.1rem'}),
            html.Span(item["label"])
        ], 
        id=item["id"], 
        style=button_style,
        n_clicks=0)
        
        nav_buttons.append(button)
    
    sidebar_content = html.Div([
        html.H2("FRGM Trade Accelerator", style=header_style),
        html.Div(nav_buttons, style={'padding': '0'})
    ], style=sidebar_style)
    
    return sidebar_content

def get_page_content(page_name):
    """Get content for the specified page"""
    page_content_mapping = {
        "pricing-monkey": pricing_monkey_tab_main_container_rendered,
        "analysis": analysis_tab_content,
        "greek-analysis": create_greek_analysis_content(),
        "project-docs": create_project_documentation_content(),
        "scenario-ladder": scl_create_scenario_ladder_content(),
        "actant-eod": aeod_create_actant_eod_content(),
        "actant-pnl": None,  # Will be populated below
        "observatory": None,  # Will be populated below
        "logs": create_logs_tab()
    }
    
    # Load Actant PnL dashboard dynamically
    if page_name == "actant-pnl":
        try:
            from apps.dashboards.actant_pnl import create_dashboard_content
            # Callbacks were already registered at app startup
            return create_dashboard_content()
        except Exception as e:
            logger.error(f"Error loading Actant PnL dashboard: {e}")
            return html.Div(
                f"Error loading Actant PnL dashboard: {str(e)}", 
                style={"color": "red", "padding": "20px"}
            )
    
    # Load Observatory dashboard dynamically
    if page_name == "observatory":
        try:
            from apps.dashboards.observatory.views import create_observatory_content
            # Callbacks were already registered at app startup
            return create_observatory_content()
        except Exception as e:
            logger.error(f"Error loading Observatory dashboard: {e}")
            return html.Div(
                f"Error loading Observatory dashboard: {str(e)}", 
                style={"color": "red", "padding": "20px"}
            )
    
    # PnL tracking removed - Phase 3 clean slate
    
    # CTO_INTEGRATION: P&L v2 loading removed
    # # Load P&L Tracking V2 dashboard
    # if page_name == "pnl-tracking-v2":
    #     try:
    #         from apps.dashboards.pnl_v2 import create_pnl_v2_layout
    #         # Return the new V2 layout
    #         return create_pnl_v2_layout()
    #     except Exception as e:
    #         logger.error(f"Error loading P&L Tracking V2 dashboard: {e}")
    #         return html.Div(
    #             f"Error loading P&L Tracking V2 dashboard: {str(e)}", 
    #             style={"color": "red", "padding": "20px"}
    #         )
    
    # Load Spot Risk dashboard dynamically
    if page_name == "spot-risk":
        try:
            from apps.dashboards.spot_risk.views import create_spot_risk_content
            from apps.dashboards.spot_risk.controller import SpotRiskController
            # Create controller and load data
            controller = SpotRiskController()
            controller.load_csv_data()
            # Callbacks were already registered at app startup
            return create_spot_risk_content(controller=controller)
        except Exception as e:
            logger.error(f"Error loading Spot Risk dashboard: {e}")
            return html.Div(
                f"Error loading Spot Risk dashboard: {str(e)}", 
                style={"color": "red", "padding": "20px"}
            )
    
    # Load FRGMonitor dashboard
    if page_name == "frg-monitor":
        try:
            return create_frg_monitor_content()
        except Exception as e:
            logger.error(f"Error loading FRGMonitor dashboard: {e}")
            return html.Div(
                f"Error loading FRGMonitor dashboard: {str(e)}", 
                style={"color": "red", "padding": "20px"}
            )
    
    return page_content_mapping.get(page_name, pricing_monkey_tab_main_container_rendered)

# --- End Sidebar System ---

# --- Layout Definition ---
# Store for tracking active page
active_page_store = dcc.Store(id="active-page-store", data="frg-monitor")

# Create sidebar
sidebar = create_sidebar()

# Content area style
content_style = {
    'marginLeft': '240px',
    'padding': '20px 10px',  # Reduced horizontal padding for more width
    'backgroundColor': default_theme.base_bg,
    'minHeight': '100vh'
}

# Create main layout with sidebar
app.layout = html.Div([
    active_page_store,
    sidebar,
    html.Div(
        id="main-content-area",
        children=[get_page_content("frg-monitor")],  # Default content
        style=content_style
    )
], style={
    "backgroundColor": default_theme.base_bg, 
    "fontFamily": "Inter, sans-serif",
    "margin": "0",
    "padding": "0"
})

# --- Navigation Callback ---
@app.callback(
    [Output("main-content-area", "children"),
     Output("active-page-store", "data"),
     Output("nav-pricing-monkey", "style"),
     Output("nav-analysis", "style"),
     Output("nav-greek-analysis", "style"),
     Output("nav-logs", "style"),
     Output("nav-project-docs", "style"),
     Output("nav-scenario-ladder", "style"),
     Output("nav-actant-eod", "style"),
         Output("nav-actant-pnl", "style"),
    # PnL tracking outputs removed - Phase 3 clean slate
     Output("nav-spot-risk", "style"),
     Output("nav-frg-monitor", "style"),
     Output("nav-observatory", "style")],
    [Input("nav-pricing-monkey", "n_clicks"),
     Input("nav-analysis", "n_clicks"),
     Input("nav-greek-analysis", "n_clicks"),
     Input("nav-logs", "n_clicks"),
     Input("nav-project-docs", "n_clicks"),
     Input("nav-scenario-ladder", "n_clicks"),
     Input("nav-actant-eod", "n_clicks"),
     Input("nav-actant-pnl", "n_clicks"),

     # Input("nav-pnl-tracking-v2", "n_clicks"),  # CTO_INTEGRATION: v2 removed
     Input("nav-spot-risk", "n_clicks"),
     Input("nav-frg-monitor", "n_clicks"),
     Input("nav-observatory", "n_clicks")],
    [State("active-page-store", "data")],
    prevent_initial_call=False
)
@monitor()
def handle_navigation(pm_clicks, analysis_clicks, greek_clicks, logs_clicks, project_docs_clicks, scenario_ladder_clicks, actant_eod_clicks, actant_pnl_clicks, spot_risk_clicks, frg_monitor_clicks, observatory_clicks, current_page):
    """Handle sidebar navigation with proper state management"""
    
    # Determine which button was clicked
    ctx = dash.callback_context
    if not ctx.triggered:
        # Initial load - show FRGMonitor page as default
        active_page = "frg-monitor"
    else:
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        page_mapping = {
            "nav-pricing-monkey": "pricing-monkey",
            "nav-analysis": "analysis",
            "nav-greek-analysis": "greek-analysis", 
            "nav-logs": "logs",
            "nav-project-docs": "project-docs",
            "nav-scenario-ladder": "scenario-ladder",
            "nav-actant-eod": "actant-eod",
            "nav-actant-pnl": "actant-pnl",
            "nav-pnl-tracking": "pnl-tracking",
            # "nav-pnl-tracking-v2": "pnl-tracking-v2",  # CTO_INTEGRATION: v2 removed
            "nav-spot-risk": "spot-risk",
            "nav-frg-monitor": "frg-monitor",
            "nav-observatory": "observatory"
        }
        active_page = page_mapping.get(trigger_id, current_page or "frg-monitor")
    
    # Get content for active page
    content = get_page_content(active_page)
    
    # Define button styles
    nav_button_base_style = {
        'width': '100%',
        'textAlign': 'left',
        'border': 'none',
        'borderRadius': '0',
        'marginBottom': '2px',
        'padding': '12px 20px',
        'fontSize': '0.9rem',
        'display': 'flex',
        'alignItems': 'center',
        'gap': '10px',
        'transition': 'all 0.2s ease',
        'cursor': 'pointer'
    }
    
    # Active button style
    active_style = {
        **nav_button_base_style,
        'backgroundColor': default_theme.accent,
        'color': default_theme.base_bg,
        'borderLeft': f'3px solid {default_theme.primary}',
        'fontWeight': '500'
    }
    
    # Inactive button style
    inactive_style = {
        **nav_button_base_style,
        'backgroundColor': default_theme.panel_bg,
        'color': default_theme.text_light,
        'borderLeft': f'3px solid transparent'
    }
    
    # Apply styles based on active page
    styles = {
        "pricing-monkey": active_style if active_page == "pricing-monkey" else inactive_style,
        "analysis": active_style if active_page == "analysis" else inactive_style,
        "greek-analysis": active_style if active_page == "greek-analysis" else inactive_style,
        "logs": active_style if active_page == "logs" else inactive_style,
        "project-docs": active_style if active_page == "project-docs" else inactive_style,
        "scenario-ladder": active_style if active_page == "scenario-ladder" else inactive_style,
        "actant-eod": active_style if active_page == "actant-eod" else inactive_style,
        "actant-pnl": active_style if active_page == "actant-pnl" else inactive_style,
        # "pnl-tracking-v2": active_style if active_page == "pnl-tracking-v2" else inactive_style,  # CTO_INTEGRATION: v2 removed
        "spot-risk": active_style if active_page == "spot-risk" else inactive_style,
        "frg-monitor": active_style if active_page == "frg-monitor" else inactive_style,
        "observatory": active_style if active_page == "observatory" else inactive_style
    }
    
    logger.info(f"Navigation: switched to page '{active_page}'")
    
    return [content], active_page, styles["pricing-monkey"], styles["analysis"], styles["greek-analysis"], styles["logs"], styles["project-docs"], styles["scenario-ladder"], styles["actant-eod"], styles["actant-pnl"], styles["spot-risk"], styles["frg-monitor"], styles["observatory"]

# Remove old tabs-based layout
# main_tabs_rendered = Tabs(
#     id="main-dashboard-tabs",
#     tabs=[
#         ("Pricing Monkey Setup", pricing_monkey_tab_main_container_rendered),
#         ("Analysis", analysis_tab_content),
#         ("Logs", create_logs_tab()),
#         ("Mermaid", create_mermaid_tab())
#     ], 
#     theme=default_theme
# ).render()

# app.layout = html.Div(
#     children=[
#         html.H1("FRGM Trade Accelerator", style={"textAlign": "center", "color": default_theme.primary, "padding": "20px 0"}), 
#         main_tabs_rendered
#     ],
#     style={"backgroundColor": default_theme.base_bg, "padding": "20px", "minHeight": "100vh", "fontFamily": "Inter, sans-serif"} 
# )

logger.info("UI layout defined with sidebar navigation.")
# --- End Layout ---

# --- FRGMonitor Callbacks ---
@app.callback(
    [Output("positions-table", "columns"),
     Output("positions-table", "data"),
     Output("positions-status-text", "children"),
     Output("positions-last-update-text", "children"),
     Output("frg-data-hash-store", "data")],
    Input("frg-refresh-interval", "n_intervals"),
    State("frg-data-hash-store", "data"),
    prevent_initial_call=False
)
@monitor(sample_rate=0.5)
def update_positions_table(n_intervals, hash_store):
    """Update positions table from trades.db only when triggered by a new signal."""
    import sqlite3
    import pandas as pd
    from datetime import datetime
    import pytz

    import hashlib
    # Localized import to minimize global surface
    from decimal import Decimal, ROUND_HALF_UP
    
    try:
        # Database path (root folder)
        db_path = os.path.join(project_root, "trades.db")
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        
        # Get current Chicago time for display
        chicago_tz = pytz.timezone('America/Chicago')
        now_cdt = datetime.now(chicago_tz)
        today_str = now_cdt.strftime('%Y-%m-%d')
        
        # Get trading day (respects 5pm cutoff) using Chicago-local time to avoid host tz drift
        trading_day = get_trading_day(now_cdt).strftime('%Y-%m-%d')

        # Dynamically determine UTC offset for SQLite
        utc_offset = now_cdt.utcoffset()
        if utc_offset:
            offset_hours = int(utc_offset.total_seconds() / 3600)
            date_modifier = f"'{offset_hours} hours'"
        else:
            date_modifier = "'0 hours'"  # Fallback

        # Fetch positions data
        query = f"""
        SELECT 
            p.symbol,
            p.instrument_type,
            p.open_position,
            p.closed_position,
            p.delta_y,
            p.gamma_y,
            p.speed_y,
            p.theta,
            (p.theta / 252.0) as theta_decay_pnl,
            p.vega,
            p.fifo_realized_pnl,
            p.fifo_unrealized_pnl,
            (p.fifo_realized_pnl + p.fifo_unrealized_pnl) as pnl_live,
            p.lifo_realized_pnl,
            p.lifo_unrealized_pnl,
            CASE WHEN p.instrument_type = 'FUTURE' THEN (p.lifo_realized_pnl + p.lifo_unrealized_pnl) ELSE NULL END AS non_gamma_lifo,
            CASE WHEN p.instrument_type = 'OPTION' THEN (p.lifo_realized_pnl + p.lifo_unrealized_pnl) ELSE NULL END AS gamma_lifo,
            p.last_updated,
            pr_now.price as live_px,
            -- Close price: show only if from today
            CASE 
                WHEN pr_close.timestamp LIKE '{trading_day}' || '%' 
                THEN pr_close.price
                ELSE 0 
            END as close_px,
            -- Close PnL: show only if close price is from today
            CASE 
                WHEN pr_close.timestamp LIKE '{trading_day}' || '%' 
                THEN (p.fifo_realized_pnl + p.fifo_unrealized_pnl_close)
                ELSE 0 
            END as pnl_close
        FROM positions p
        LEFT JOIN pricing pr_now ON p.symbol = pr_now.symbol AND pr_now.price_type = 'now'
        LEFT JOIN pricing pr_close ON p.symbol = pr_close.symbol AND pr_close.price_type = 'close'
        WHERE 
            p.open_position != 0
            OR (
                p.closed_position != 0 AND (
                    EXISTS (
                        SELECT 1 FROM realized_fifo rf
                        WHERE rf.symbol = p.symbol
                          AND DATE(rf.timestamp,
                                   CASE WHEN CAST(strftime('%H', rf.timestamp) AS INTEGER) >= 17 
                                        THEN '+1 day' ELSE '+0 day' END) = '{trading_day}'
                    )
                    OR EXISTS (
                        SELECT 1 FROM realized_lifo rl
                        WHERE rl.symbol = p.symbol
                          AND DATE(rl.timestamp,
                                   CASE WHEN CAST(strftime('%H', rl.timestamp) AS INTEGER) >= 17 
                                        THEN '+1 day' ELSE '+0 day' END) = '{trading_day}'
                    )
                )
            )
        ORDER BY p.symbol
        """
        
        # Diagnostics: log how many rows are excluded by the trading-day filter
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # --- Compute tick-display columns (LivePXTX / ClosePXTX) ---
        # Helper: classify instrument type with safe fallback
        fallback_futures = {
            'TYU5 Comdty', 'USU5 Comdty', 'FVU5 Comdty', 'TUU5 Comdty',
            'TYZ5 Comdty', 'USZ5 Comdty', 'FVZ5 Comdty', 'TUZ5 Comdty'
        }

        def _classify_instrument(row) -> str:
            # Hard override: treat known Bloomberg futures as FUTURE regardless of upstream type
            symbol = (row.get('symbol') or '').strip()
            if symbol in fallback_futures:
                return 'FUTURE'

            itype = str(row.get('instrument_type') or '').upper().strip()
            if itype in {'F', 'FUTURE'}:
                return 'FUTURE'
            if itype in {'C', 'P', 'CALL', 'PUT', 'OPTION'}:
                return 'OPTION'
            # Default per requirement: treat as option if unknown
            return 'OPTION'

        # Helper: format decimal price to WHOLE'NNN per base (32 for futures, 64 for options)
        def _format_ticks_str(decimal_price, base: int):
            try:
                if decimal_price is None:
                    return None
                if isinstance(decimal_price, float) and pd.isna(decimal_price):
                    return None
                dec = Decimal(str(decimal_price))
                whole = int(dec)  # floor for positive numbers
                frac = dec - Decimal(whole)
                # quantize to half-tick units to avoid float jitter
                half_units = (frac * Decimal(base) * Decimal(2)).to_integral_value(rounding=ROUND_HALF_UP)
                limit = base * 2
                if half_units >= limit:
                    # Red flag scenario; clamp and log at debug level to avoid rollover
                    logger.debug(f"Tick half-units exceeded limit for price {decimal_price}: {half_units} >= {limit}. Clamping.")
                    half_units = Decimal(limit - 1)
                nnn = int(half_units) * 5  # map half-units to NNN (e.g., 17.5 -> 175)
                return f"{whole}'{nnn:03d}"
            except Exception as _e:
                logger.debug(f"Failed to format ticks for price {decimal_price}: {_e}")
                return None

        if not df.empty:
            def _format_future_symbol_aware(px, sym, inst):
                try:
                    if px is None or (isinstance(px, float) and pd.isna(px)):
                        return None
                    if inst == 'FUTURE':
                        if decimal_to_tt_bond_format_by_symbol:
                            return decimal_to_tt_bond_format_by_symbol(px, sym)
                        # Fallback to existing behavior (base 32) to avoid regressions
                        return _format_ticks_str(px, 32)
                    return None
                except Exception:
                    return None

            df['live_px_tx'] = df.apply(
                lambda r: (
                    _format_future_symbol_aware(r.get('live_px'), r.get('symbol'), _classify_instrument(r))
                    if _classify_instrument(r) == 'FUTURE'
                    else _format_ticks_str(r.get('live_px'), 64)
                ), axis=1
            )
            df['close_px_tx'] = df.apply(
                lambda r: (
                    _format_future_symbol_aware(r.get('close_px'), r.get('symbol'), _classify_instrument(r))
                    if _classify_instrument(r) == 'FUTURE'
                    else _format_ticks_str(r.get('close_px'), 64)
                ), axis=1
            )
        else:
            df['live_px_tx'] = None
            df['close_px_tx'] = None

        # Format columns
        columns = [
            {"name": "Symbol", "id": "symbol"},
            {"name": "Type", "id": "instrument_type"},
            {"name": "Open", "id": "open_position", "type": "numeric", "format": {"specifier": ","}},
            {"name": "Closed", "id": "closed_position", "type": "numeric", "format": {"specifier": ","}},
            {"name": "Delta Y", "id": "delta_y", "type": "numeric", "format": {"specifier": ",.0f"}},
            {"name": "Gamma Y", "id": "gamma_y", "type": "numeric", "format": {"specifier": ",.0f"}},
            {"name": "Speed Y", "id": "speed_y", "type": "numeric", "format": {"specifier": ",.0f"}},
            {"name": "Theta", "id": "theta", "type": "numeric", "format": {"specifier": ",.0f"}},
            {"name": "Vega", "id": "vega", "type": "numeric", "format": {"specifier": ",.0f"}},
            {"name": "PnL Live", "id": "pnl_live", "type": "numeric", "format": {"specifier": "$,.2f"}},
            {"name": "PnL Close", "id": "pnl_close", "type": "numeric", "format": {"specifier": "$,.2f"}},
            {"name": "Theta Decay Pnl", "id": "theta_decay_pnl", "type": "numeric", "format": {"specifier": "$,.6f"}},
            {"name": "LIFO", "id": "non_gamma_lifo", "type": "numeric", "format": {"specifier": "$,.2f"}},
            {"name": "LIFOc", "id": "non_gamma_lifoc", "type": "numeric", "format": {"specifier": "$,.2f"}},
            {"name": "Gamma LIFO", "id": "gamma_lifo", "type": "numeric", "format": {"specifier": "$,.2f"}},
            {"name": "LIFOC", "id": "lifoc", "type": "numeric", "format": {"specifier": "$,.2f"}},
            {"name": "LivePX", "id": "live_px", "type": "numeric", "format": {"specifier": ",.6f"}},
            {"name": "LivePXTX", "id": "live_px_tx", "type": "text"},
            {"name": "ClosePX", "id": "close_px", "type": "numeric", "format": {"specifier": ",.6f"}},
            {"name": "ClosePXTX", "id": "close_px_tx", "type": "text"}
        ]
        
        # Convert dataframe to records
        data = df.to_dict('records')
        
        # Calculate single aggregate row
        aggregate_row = {'symbol': 'AGGREGATE', 'instrument_type': 'AGGREGATE'}
        
        if not df.empty:
            # Sum all numeric columns except prices
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            exclude_cols = ['live_px', 'close_px', 'open_position', 'closed_position']
            
            for col in numeric_cols:
                if col not in exclude_cols:
                    total = df[col].sum()
                    aggregate_row[col] = total if total != 0 else None
        
        # Add aggregate row
        data.append(aggregate_row)
        
        # Update status (subtract 1 for single aggregate row)
        base_count = len(data) - 1
        status_text = f"Connected - {base_count} rows"
        
        # Update last update time (Chicago time)
        chicago_tz = pytz.timezone('America/Chicago')
        current_time = datetime.now(chicago_tz).strftime("%Y-%m-%d %H:%M:%S")
        
        # Calculate hash of the data to detect changes
        data_str = str(sorted(data, key=lambda x: x.get('symbol', '')))
        current_hash = hashlib.md5(data_str.encode()).hexdigest()
        
        # Get previous hash
        previous_hash = hash_store.get('hash') if hash_store else None
        
        # If data hasn't changed, prevent update (but still return data for initial load)
        if previous_hash == current_hash and n_intervals > 0:
            logger.debug("Data unchanged, preventing update")
            raise PreventUpdate
        
        # Return data with new hash
        new_hash_store = {'hash': current_hash}
        return columns, data, status_text, current_time, new_hash_store
        
    except PreventUpdate:
        raise
    except Exception as e:
        logger.error(f"Error updating positions table: {type(e).__name__}: {str(e)}", exc_info=True)
        return [], [], f"Error: {str(e)}", "--", hash_store

@app.callback(
    [Output("daily-positions-table", "columns"),
     Output("daily-positions-table", "data"),
     Output("daily-positions-status-text", "children"),
     Output("daily-positions-last-update-text", "children"),
     Output("daily-positions-inception-pnl", "children")],
    Input("frg-refresh-interval", "n_intervals"),
    prevent_initial_call=False  # Allow initial call to populate on startup
)
@monitor(sample_rate=0.5)
def update_daily_positions_table(trigger_data):
    """Update daily positions table from trades.db only when triggered by a new signal."""
    import sqlite3
    import pandas as pd
    from datetime import datetime
    import pytz
    
    # Allow initial load (trigger_data will be None on startup)

    try:
        # Database path (root folder)
        db_path = os.path.join(project_root, "trades.db")
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        
        # Fetch daily positions data - FIFO only, aggregated by date
        query = """
        SELECT 
            date,
            SUM(realized_pnl) as realized_pnl,
            SUM(unrealized_pnl) as unrealized_pnl
        FROM daily_positions
        WHERE LOWER(method) = 'fifo'
        GROUP BY date
        ORDER BY date DESC
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Convert timestamps to Chicago time
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
        
        # Add total P&L column
        df['total_pnl'] = df['realized_pnl'] + df['unrealized_pnl']
        
        # Format columns
        columns = [
            {"name": "Date", "id": "date"},
            {"name": "Realized P&L", "id": "realized_pnl", "type": "numeric", "format": {"specifier": "$,.2f"}},
            {"name": "Unrealized P&L", "id": "unrealized_pnl", "type": "numeric", "format": {"specifier": "$,.2f"}},
            {"name": "Total P&L", "id": "total_pnl", "type": "numeric", "format": {"specifier": "$,.2f"}}
        ]
        
        # Convert dataframe to records
        data = df.to_dict('records')
        
        # Calculate inception to date P&L
        inception_pnl = df['total_pnl'].sum() if 'total_pnl' in df.columns and not df.empty else 0
        inception_pnl_text = f"${inception_pnl:,.2f}"
        
        # Update status
        status_text = f"Connected - {len(data)} rows"
        
        # Update last update time (Chicago time)
        chicago_tz = pytz.timezone('America/Chicago')
        current_time = datetime.now(chicago_tz).strftime("%Y-%m-%d %H:%M:%S")
        
        return columns, data, status_text, current_time, inception_pnl_text
        
    except Exception as e:
        logger.error(f"Error updating daily positions table: {type(e).__name__}: {str(e)}", exc_info=True)
        return [], [], f"Error: {str(e)}", "--", "--"

# --- End FRGMonitor Callbacks ---

# --- Callbacks ---
@app.callback(
    Output("dynamic-options-area", "children"),
    Input("num-options-selector", "value")
)
@monitor()
def update_option_blocks(selected_num_options_str: str | None):
    # This function remains the same as in your provided file
    if selected_num_options_str is None:
        num_active_options = 1
    else:
        try:
            num_active_options = int(selected_num_options_str)
        except (ValueError, TypeError):
            num_active_options = 1
        if not 1 <= num_active_options <= 3:
            num_active_options = 1

    logger.info(f"Updating dynamic area to show {num_active_options} options.")
    output_children = []
    for i in range(3): 
        option_block_instance = create_option_input_block(i)
        display_style = {'display': 'block'} if i < num_active_options else {'display': 'none'}
        wrapper_div = html.Div(
            children=option_block_instance.render(),
            id=f"option-{i}-wrapper", 
            style=display_style
        )
        output_children.append(wrapper_div)
    return output_children

@app.callback(
    Output("results-display-area-content", "children"), 
    Input("update-sheet-button", "n_clicks"),
    [State(f"option-{i}-{field}", "value") for i in range(3) for field in ["desc-prefix", "desc-strike", "desc-type", "qty", "phase"]] +
    [State("num-options-selector", "value")],
    prevent_initial_call=True
)
# This is a key user action we want to trace for performance monitoring
@monitor()
def handle_update_sheet_button_click(n_clicks: int | None, *args: any):
    if n_clicks is None or n_clicks == 0: raise PreventUpdate

    num_options_str = args[-1]
    all_option_field_values = args[:-1]

    logger.info(f"'Run Automation' clicked. Processing inputs...")
    try: 
        num_active_options = int(str(num_options_str))
        if not 1 <= num_active_options <= 3: 
            num_active_options = 1
    except (ValueError, TypeError):
        logger.error(f"Invalid num options: {num_options_str}.")
        return [html.P("Invalid number of options.", style={'color': 'red'})]

    ui_options_data_for_pm = [] 
    
    fields_per_option = 5
    for i in range(num_active_options): 
        try:
            start_idx = i * fields_per_option
            if start_idx + fields_per_option <= len(all_option_field_values):
                prefix, strike_desc_part, opt_type, qty_str, phase_str = all_option_field_values[start_idx : start_idx + fields_per_option]
                
                if not all([prefix, strike_desc_part, opt_type, qty_str is not None, phase_str]):
                    logger.warning(f"Option {i+1} missing fields. Skipping.")
                    continue
                    
                try:
                    qty_val = int(str(qty_str)) if qty_str is not None else 0
                    phase_val = int(str(phase_str)) if phase_str is not None else 0 
                    if qty_val <= 0: 
                        logger.warning(f"Option {i+1} non-positive qty. Skipping.")
                        continue
                except (ValueError, TypeError):
                    logger.error(f"Invalid qty/phase for Option {i+1}. Skipping.")
                    continue
                    
                ui_options_data_for_pm.append({
                    'desc': f"{prefix} 10y note {strike_desc_part} out {opt_type}", 
                    'qty': qty_val, 
                    'phase': phase_val, 
                    'id': i 
                })
            else:
                logger.warning(f"Option {i+1} data not found in state values. Skipping.")
        except Exception as e:
            logger.warning(f"Error processing Option {i+1} input data: {str(e)}. Skipping.")
            continue

    if not ui_options_data_for_pm:
        logger.warning("No valid option data to send to PM automation.")
        return [html.P("No valid option data to process.", style=text_style)]

    list_of_option_dfs_from_pm = None 
    try:
        logger.info(f"Calling run_pm_automation with: {ui_options_data_for_pm}")
        # Call the PricingMonkey automation function directly - it already has @monitor applied
        list_of_option_dfs_from_pm = run_pm_automation(ui_options_data_for_pm) 
    except Exception as e:
        logger.error(f"Error in run_pm_automation: {e}", exc_info=True)
        return [html.P(f"Error during automation: {str(e)[:200]}...", style={'color': 'red'})]

    if not list_of_option_dfs_from_pm or not isinstance(list_of_option_dfs_from_pm, list):
        logger.warning("No list of DFs from PM automation or incorrect type.")
        return [html.P("No results from automation or an error (see logs).", style=text_style)]

    tabs_content_list = [] 

    for option_data_sent_to_pm in ui_options_data_for_pm:
        option_idx = option_data_sent_to_pm['id'] 

        if option_idx >= len(list_of_option_dfs_from_pm):
            logger.warning(f"Missing DataFrame from PM for original option index {option_idx}. Skipping tab.")
            continue

        current_option_df = list_of_option_dfs_from_pm[option_idx] 
        if not isinstance(current_option_df, pd.DataFrame):
            logger.warning(f"Item from PM at original index {option_idx} is not a DataFrame. Skipping tab.")
            continue

        tab_content_elements = [] 
        
        desc_to_display = option_data_sent_to_pm['desc']
        user_trade_amount_for_scaling = option_data_sent_to_pm['qty']

        desc_html = html.H4(f"Trade Description: {desc_to_display}", style={"color": default_theme.text_light, "marginTop": "10px", "marginBottom": "5px", "fontSize":"0.9rem"})
        amount_html = html.H5(f"Trade Amount: {user_trade_amount_for_scaling}", style={"color": default_theme.text_light, "marginBottom": "15px", "fontSize":"0.8rem"})
        tab_content_elements.extend([desc_html, amount_html])
        
        store_id = {"type": "option-data-store", "index": option_idx}
        data_for_store = {
            'df_json': current_option_df.to_json(orient='split', date_format='iso'),
            'trade_amount': user_trade_amount_for_scaling 
        }
        tab_content_elements.append(dcc.Store(id=store_id, data=data_for_store))
        
        # --- DataTable Preparation (exactly as in user's provided file) ---
        if not current_option_df.empty:
            df_for_table_display = current_option_df.copy() 
            if user_trade_amount_for_scaling > 0:
                multiplier = user_trade_amount_for_scaling / 1000.0
                for col_name_scale in ['DV01 Gamma', 'Theta', 'Vega']: 
                    if col_name_scale in df_for_table_display.columns:
                        numeric_col_scale = pd.to_numeric(df_for_table_display[col_name_scale], errors='coerce')
                        scaled_col_data = numeric_col_scale * multiplier
                        df_for_table_display[col_name_scale] = scaled_col_data.where(pd.notnull(scaled_col_data), df_for_table_display[col_name_scale])
            
            datatable_df_formatted = pd.DataFrame()
            for col_info_table in RESULT_TABLE_COLUMNS: 
                col_id = col_info_table['id']
                if col_id in df_for_table_display.columns:
                    datatable_df_formatted[col_id] = df_for_table_display[col_id]
                    if col_id in ['DV01 Gamma', 'Theta', 'Vega']: 
                        datatable_df_formatted[col_id] = datatable_df_formatted[col_id].apply(
                            lambda x_val: f"{x_val:.2f}" if pd.notna(x_val) and isinstance(x_val, (int, float)) else ("N/A" if pd.isna(x_val) else str(x_val))
                        )
                else: 
                    datatable_df_formatted[col_id] = "N/A"

            table_for_option = DataTable(
                id=f"results-datatable-option-{option_idx}", 
                data=datatable_df_formatted.to_dict('records'), 
                columns=RESULT_TABLE_COLUMNS, 
                theme=default_theme, 
                page_size=12, 
                style_table={'minWidth': '100%', 'marginTop': '10px'}, 
                style_header={'backgroundColor': default_theme.panel_bg, 'fontWeight': 'bold', 'color': default_theme.text_light, 'fontSize':'0.75rem'}, 
                style_cell={'backgroundColor': default_theme.base_bg, 'color': default_theme.text_light, 'textAlign': 'left', 'padding': '8px', 'fontSize':'0.7rem'},
            ).render()
            tab_content_elements.append(table_for_option)
        else:
            tab_content_elements.append(html.P("No detailed results for this option.", style=text_style))
        # --- End DataTable Preparation ---

        # --- ComboBox for Y-Axis Selection ---
        combobox_id = {"type": "y-axis-selector-combobox", "index": option_idx}
        y_axis_combobox = ComboBox(
            id=combobox_id,
            options=Y_AXIS_CHOICES,
            value=DEFAULT_Y_AXIS_COL, 
            theme=default_theme,
            clearable=False, 
            style={'width': '100%', 'marginBottom': '10px', 'marginTop': '20px'} 
        ).render()
        tab_content_elements.append(html.P("Select Y-Axis for Graph:", style={**text_style, 'marginTop': '20px', 'marginBottom':'5px'}))
        tab_content_elements.append(y_axis_combobox)
        # --- End ComboBox ---

        # --- Initial Graph Population (uses raw current_option_df) ---
        graph_figure_initial = go.Figure() 
        initial_y_col_name = DEFAULT_Y_AXIS_COL
        initial_y_col_label = next((item['label'] for item in Y_AXIS_CHOICES if item['value'] == initial_y_col_name), initial_y_col_name)
        initial_y_axis_title = initial_y_col_label 

        if not current_option_df.empty:
            if STRIKE_COLUMN_NAME in current_option_df.columns and initial_y_col_name in current_option_df.columns:
                strike_data_init = pd.to_numeric(current_option_df[STRIKE_COLUMN_NAME], errors='coerce')
                # Get raw Y-axis data for initial plot
                y_axis_data_init_raw = current_option_df[initial_y_col_name] # Keep as Series for now

                y_axis_data_init_processed = pd.Series(dtype='float64') # Default to empty float series

                if initial_y_col_name == "% Delta":
                    # Expects strings like "0.7%", convert to numeric 0.7
                    y_axis_data_init_processed = pd.to_numeric(y_axis_data_init_raw.astype(str).str.rstrip('%'), errors='coerce')
                    initial_y_axis_title = f"{initial_y_col_label}" # Label already includes (%)
                elif initial_y_col_name in GRAPH_SCALABLE_GREEKS:
                    y_axis_data_init_numeric = pd.to_numeric(y_axis_data_init_raw, errors='coerce')
                    if user_trade_amount_for_scaling > 0:
                        y_axis_data_init_processed = (y_axis_data_init_numeric / 1000.0) * user_trade_amount_for_scaling
                    else:
                        y_axis_data_init_processed = y_axis_data_init_numeric # Use raw numeric if no scaling
                else: # For "Implied Vol (Daily BP)" or other non-scaled, non-delta
                    y_axis_data_init_processed = pd.to_numeric(y_axis_data_init_raw, errors='coerce')

                plot_df_init = pd.DataFrame({'strike': strike_data_init, 'y_data': y_axis_data_init_processed}).dropna()

                if not plot_df_init.empty:
                    graph_figure_initial.add_trace(go.Scatter(
                        x=plot_df_init['strike'], y=plot_df_init['y_data'], mode='lines+markers',
                        marker=dict(color=default_theme.primary, size=8, line=dict(color=default_theme.accent, width=1)),
                        line=dict(color=default_theme.accent, width=2)
                    ))
                    graph_figure_initial.update_layout(title_text=f"{initial_y_col_label} vs. {STRIKE_COLUMN_NAME} (Option {option_idx+1})")
                else:
                    graph_figure_initial.update_layout(title_text=f"{initial_y_col_label} vs. {STRIKE_COLUMN_NAME} (Option {option_idx+1}) - No Plottable Data")
            else: 
                graph_figure_initial.update_layout(title_text=f"Initial Graph (Option {option_idx+1}) - Required Columns Missing")
        else: 
             graph_figure_initial.update_layout(title_text=f"Graph (Option {option_idx+1}) - No Data")
        
        graph_figure_initial.update_layout(
            xaxis_title=STRIKE_COLUMN_NAME, 
            yaxis_title=initial_y_axis_title, 
            paper_bgcolor=default_theme.panel_bg, 
            plot_bgcolor=default_theme.base_bg,
            font_color=default_theme.text_light,
            xaxis=dict(showgrid=True, gridcolor=default_theme.secondary),
            yaxis=dict(showgrid=True, gridcolor=default_theme.secondary),
            height=350
        )
        # --- End Initial Graph Population ---
        
        graph_id = {"type": "results-graph", "index": option_idx} 
        graph_component = Graph(
            id=graph_id, 
            figure=graph_figure_initial, 
            theme=default_theme, 
            style={'marginTop': '5px', 'border': f'1px solid {default_theme.secondary}', 'borderRadius': '5px'}
        ).render()
        
        tab_content_elements.append(graph_component)
        
        tab_content = html.Div(tab_content_elements, style={'padding': '10px'}) 
        tab_label = f"Option {option_idx+1}" 
        tabs_content_list.append((tab_label, tab_content))

    if not tabs_content_list: 
        return [html.P("No data to display in tabs.", style=text_style)]

    results_tabs_component = Tabs(id="results-tabs", tabs=tabs_content_list, theme=default_theme)
    return [results_tabs_component.render()]

# --- New Callback to Update Graph based on ComboBox Selection ---
@app.callback(
    Output({"type": "results-graph", "index": MATCH}, "figure"),
    Input({"type": "y-axis-selector-combobox", "index": MATCH}, "value"), 
    State({"type": "option-data-store", "index": MATCH}, "data"), 
    prevent_initial_call=True 
)
@monitor()
def update_graph_from_combobox(selected_y_column_value: str, stored_option_data: dict):
    if not selected_y_column_value or not stored_option_data or 'df_json' not in stored_option_data or 'trade_amount' not in stored_option_data:
        logger.warning("ComboBox callback triggered with no selection or incomplete stored data.")
        raise PreventUpdate

    try:
        option_df = pd.read_json(stored_option_data['df_json'], orient='split')
        trade_amount = stored_option_data['trade_amount'] 
    except Exception as e:
        logger.error(f"Error deserializing DataFrame/trade_amount from store: {e}")
        raise PreventUpdate

    fig = go.Figure()
    selected_y_column_label = next((item['label'] for item in Y_AXIS_CHOICES if item['value'] == selected_y_column_value), selected_y_column_value)
    y_axis_title_on_graph = selected_y_column_label # Use the label from Y_AXIS_CHOICES which might include (%)

    if STRIKE_COLUMN_NAME in option_df.columns and selected_y_column_value in option_df.columns:
        strike_data_numeric = pd.to_numeric(option_df[STRIKE_COLUMN_NAME], errors='coerce')
        # Get raw Y-axis data as a Series first for consistent processing
        y_axis_data_series_raw = option_df[selected_y_column_value] 

        y_axis_data_processed_for_graph = pd.Series(dtype='float64') # Default to empty float series

        if selected_y_column_value == "% Delta":
            # Expects strings like "0.7%", convert to numeric 0.7 for plotting
            # The label in Y_AXIS_CHOICES ("Delta (%)" already indicates the unit.
            y_axis_data_processed_for_graph = pd.to_numeric(y_axis_data_series_raw.astype(str).str.rstrip('%'), errors='coerce')
            # y_axis_title_on_graph is already "Delta (%)" from selected_y_column_label
        elif selected_y_column_value in GRAPH_SCALABLE_GREEKS:
            y_axis_data_numeric_raw = pd.to_numeric(y_axis_data_series_raw, errors='coerce')
            if trade_amount > 0: 
                y_axis_data_processed_for_graph = (y_axis_data_numeric_raw / 1000.0) * trade_amount
            else: 
                y_axis_data_processed_for_graph = y_axis_data_numeric_raw
                logger.warning(f"Trade amount is {trade_amount} for scaling {selected_y_column_value}. Using raw numeric values for graph.")
        else: # For "Implied Vol (Daily BP)" or other non-scaled, non-delta
            y_axis_data_processed_for_graph = pd.to_numeric(y_axis_data_series_raw, errors='coerce')

        plot_df = pd.DataFrame({'strike': strike_data_numeric, 'y_data': y_axis_data_processed_for_graph}).dropna()

        if not plot_df.empty:
            fig.add_trace(go.Scatter(
                x=plot_df['strike'],
                y=plot_df['y_data'],
                mode='lines+markers',
                marker=dict(color=default_theme.primary, size=8, line=dict(color=default_theme.accent, width=1)),
                line=dict(color=default_theme.accent, width=2)
            ))
            fig.update_layout(
                title_text=f"{selected_y_column_label} vs. {STRIKE_COLUMN_NAME}", # Use label which might include (%)
                xaxis_title=STRIKE_COLUMN_NAME,
                yaxis_title=y_axis_title_on_graph, 
            )
            logger.info(f"Graph updated with Y-axis: {selected_y_column_label}, {len(plot_df)} points.")
        else:
            fig.update_layout(title_text=f"{selected_y_column_label} vs. {STRIKE_COLUMN_NAME} - No Plottable Data")
    else: 
        missing_cols = []
        if STRIKE_COLUMN_NAME not in option_df.columns: missing_cols.append(STRIKE_COLUMN_NAME)
        if selected_y_column_value not in option_df.columns: missing_cols.append(selected_y_column_value)
        fig.update_layout(title_text=f"Data Missing for Graph ({', '.join(missing_cols)})")

    fig.update_layout(
        paper_bgcolor=default_theme.panel_bg,
        plot_bgcolor=default_theme.base_bg,
        font_color=default_theme.text_light,
        xaxis=dict(showgrid=True, gridcolor=default_theme.secondary),
        yaxis=dict(showgrid=True, gridcolor=default_theme.secondary),
        height=350
    )
    return fig

# --- Analysis Tab Callbacks ---
@app.callback(
    Output("market-movement-data-store", "data"),
    Output("analysis-graph", "figure"),
    Output("analysis-underlying-selector", "options"),
    Output("analysis-underlying-selector", "value"),
    Output("analysis-data-table", "data"),
    Output("analysis-data-table", "columns"),
    Input("analysis-refresh-button", "n_clicks"),
    Input("analysis-y-axis-selector", "value"),
    Input("analysis-underlying-selector", "value"),
    State("market-movement-data-store", "data"),
    prevent_initial_call=True
)
@monitor()
def handle_analysis_interactions(refresh_clicks, selected_y_axis, selected_underlying, stored_data):
    """Unified callback to handle all Analysis tab interactions"""
    # Determine which input triggered the callback
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
    
    # Default values
    data_json = stored_data
    fig = go.Figure()
    underlying_options = []
    underlying_value = selected_underlying
    table_data = []
    table_columns = [{"name": "Strike", "id": "Strike"}]
    
    # Apply default styling to empty figure
    fig.update_layout(
        xaxis_title="Strike",
        yaxis_title="Selected Metric",
        paper_bgcolor=default_theme.panel_bg,
        plot_bgcolor=default_theme.base_bg,
        font_color=default_theme.text_light,
        xaxis=dict(showgrid=True, gridcolor=default_theme.secondary),
        yaxis=dict(showgrid=True, gridcolor=default_theme.secondary),
        height=400
    )
    
    # Handle refresh button click
    if trigger_id == "analysis-refresh-button" and refresh_clicks:
        logger.info("Refresh Data button clicked. Fetching market movement data...")
        try:
            # Get market movement data (nested dictionary by underlying and expiry)
            # Call the function directly - it already has @monitor applied
            result_dict = get_market_movement_data_df()
            
            if not result_dict or 'data' not in result_dict:
                logger.warning("Retrieved empty data dictionary from market movement data")
                # Create empty figure with message
                fig.update_layout(
                    title="No market data available",
                    xaxis_title="Strike",
                    yaxis_title="Selected Metric",
                    annotations=[dict(text="No data available. Please try again.", showarrow=False, xref="paper", yref="paper", x=0.5, y=0.5)],
                    paper_bgcolor=default_theme.panel_bg,
                    plot_bgcolor=default_theme.base_bg,
                    font_color=default_theme.text_light,
                    xaxis=dict(showgrid=True, gridcolor=default_theme.secondary),
                    yaxis=dict(showgrid=True, gridcolor=default_theme.secondary)
                )
                return None, fig, [], None, [], table_columns
            
            # Access the data and metadata from the result dictionary
            data_dict = result_dict['data']
            metadata = result_dict['metadata']
            
            # Create dropdown options for underlying values
            underlying_options = []
            
            # Function to detect and format contract transitions
            def format_underlying_option(key, values, display_name):
                if not values:
                    # Fallback if no values were collected
                    return {"label": display_name, "value": key}
                
                # Check for contract transitions (different underlying values)
                unique_values = list(set(values))
                if len(unique_values) == 1:
                    # Single contract type
                    return {"label": f"{display_name} ({unique_values[0]})", "value": key}
                else:
                    # Multiple contract types (transition)
                    value_display = f"{unique_values[0]} → {unique_values[-1]}"
                    return {"label": f"{display_name} ({value_display})", "value": key}
            
            # Add options for each scenario
            for scenario_key, scenario_info in SCENARIOS.items():
                display_name = scenario_info['display_name']
                values = metadata.get(scenario_key, [])
                underlying_options.append(format_underlying_option(scenario_key, values, display_name))
            
            # Set initial underlying selection if none exists
            if not selected_underlying and underlying_options:
                underlying_value = underlying_options[0]["value"]
            
            # Count total rows across all DataFrames
            total_rows = 0
            for underlying, expiry_dict in data_dict.items():
                for expiry, df in expiry_dict.items():
                    total_rows += len(df)
            logger.info(f"Successfully retrieved market data: {len(data_dict)} underlyings, {total_rows} total rows")
            
            # Use current y-axis selection or default
            y_axis = selected_y_axis or "Implied Vol (Daily BP)"
            
            # Create graph with selected or default underlying
            underlying_to_use = underlying_value if underlying_value in data_dict else list(data_dict.keys())[0]
            
            # Extract values for each scenario for graph title
            scenario_values = {key: metadata.get(key, []) for key in SCENARIOS.keys()}
            
            # Create the graph
            fig = create_analysis_graph(data_dict, y_axis, underlying_to_use, scenario_values)
            
            # Prepare data for the table
            table_data, table_columns = prepare_table_data(data_dict, underlying_to_use, y_axis)
            
            # Store data dictionary as JSON in the dcc.Store
            # Convert each DataFrame in each underlying group to JSON and store in a nested dictionary
            data_json_dict = {
                'data': {},
                'metadata': metadata
            }
            
            for underlying, expiry_dict in data_dict.items():
                data_json_dict['data'][underlying] = {}
                for expiry, df in expiry_dict.items():
                    data_json_dict['data'][underlying][expiry] = df.to_json(date_format='iso', orient='split')
            
            # Store the dictionary structure as JSON
            data_json = json.dumps(data_json_dict)
            
        except Exception as e:
            logger.error(f"Error fetching market movement data: {str(e)}", exc_info=True)
            # Create error figure
            fig.update_layout(
                title="Error fetching data",
                xaxis_title="Strike",
                yaxis_title="Selected Metric",
                annotations=[dict(text=f"Error: {str(e)[:100]}...", showarrow=False, xref="paper", yref="paper", x=0.5, y=0.5)],
                paper_bgcolor=default_theme.panel_bg,
                plot_bgcolor=default_theme.base_bg,
                font_color=default_theme.text_light,
                xaxis=dict(showgrid=True, gridcolor=default_theme.secondary),
                yaxis=dict(showgrid=True, gridcolor=default_theme.secondary)
            )
    
    # Handle y-axis or underlying selection change
    elif (trigger_id == "analysis-y-axis-selector" or trigger_id == "analysis-underlying-selector") and stored_data:
        try:
            # Check if y-axis is deselected (edge case)
            if not selected_y_axis:
                # Create an empty figure but preserve styling
                fig = go.Figure()
                fig.update_layout(
                    title="Select a metric for the Y-axis",
                    xaxis_title="Strike",
                    yaxis_title="Selected Metric",
                    paper_bgcolor=default_theme.panel_bg,
                    plot_bgcolor=default_theme.base_bg,
                    font_color=default_theme.text_light,
                    xaxis=dict(showgrid=True, gridcolor=default_theme.secondary),
                    yaxis=dict(showgrid=True, gridcolor=default_theme.secondary),
                    height=400
                )
            else:
                # Parse the stored data JSON
                data_json_dict = json.loads(stored_data)
                
                # Make sure data_json_dict has the expected structure
                if 'data' not in data_json_dict:
                    # Legacy format, restructure it
                    logger.warning("Legacy format detected in stored data, restructuring")
                    new_data_json_dict = {'data': {}, 'metadata': {}}
                    
                    # Extract metadata if it exists
                    if 'metadata' in data_json_dict:
                        new_data_json_dict['metadata'] = data_json_dict['metadata']
                    else:
                        # Create empty metadata
                        new_data_json_dict['metadata'] = {key: [] for key in SCENARIOS.keys()}
                    
                    # Move data to data field
                    for key, value in data_json_dict.items():
                        if key != 'metadata':
                            new_data_json_dict['data'][key] = value
                    
                    data_json_dict = new_data_json_dict
                
                # Get data and metadata
                data_dict = {}
                metadata = data_json_dict.get('metadata', {})
                
                # Parse the data from JSON strings back to DataFrames
                for underlying, expiry_dict in data_json_dict['data'].items():
                    data_dict[underlying] = {}
                    for expiry, df_json in expiry_dict.items():
                        df = pd.read_json(StringIO(df_json), orient='split')
                        
                        # Ensure numeric columns are properly typed after JSON deserialization
                        numeric_columns = ["Strike", "Implied Vol (Daily BP)", "DV01 Gamma", "Theta", "Vega"]
                        if "%Delta" in df.columns:
                            # Special handling for Delta column
                            df["%Delta"] = pd.to_numeric(df["%Delta"].astype(str).str.replace('%', ''), errors='coerce')
                            numeric_columns.append("%Delta")
                            
                        # Convert other numeric columns
                        for col in numeric_columns:
                            if col in df.columns:
                                df[col] = pd.to_numeric(df[col], errors='coerce')
                        
                        data_dict[underlying][expiry] = df
                
                # Create dropdown options for underlying values
                underlying_options = []
                
                # Function to detect and format contract transitions
                def format_underlying_option(key, values, display_name):
                    if not values:
                        # Fallback if no values were collected
                        return {"label": display_name, "value": key}
                    
                    # Check for contract transitions (different underlying values)
                    unique_values = list(set(values))
                    if len(unique_values) == 1:
                        # Single contract type
                        return {"label": f"{display_name} ({unique_values[0]})", "value": key}
                    else:
                        # Multiple contract types (transition)
                        value_display = f"{unique_values[0]} → {unique_values[-1]}"
                        return {"label": f"{display_name} ({value_display})", "value": key}
                
                # Add options for each scenario
                for scenario_key, scenario_info in SCENARIOS.items():
                    display_name = scenario_info['display_name']
                    values = metadata.get(scenario_key, [])
                    underlying_options.append(format_underlying_option(scenario_key, values, display_name))
                
                # Handle case where selected underlying doesn't exist in data
                if not selected_underlying or selected_underlying not in data_dict:
                    underlying_value = list(data_dict.keys())[0]
                
                # Extract values for each scenario for graph title
                scenario_values = {key: metadata.get(key, []) for key in SCENARIOS.keys()}
                
                # Create graph with filtered data based on selected underlying
                fig = create_analysis_graph(data_dict, selected_y_axis, underlying_value, scenario_values)
                
                # Prepare data for the table
                table_data, table_columns = prepare_table_data(data_dict, underlying_value, selected_y_axis)
        except Exception as e:
            logger.error(f"Error updating analysis graph: {str(e)}", exc_info=True)
            fig.update_layout(
                title="Error updating graph",
                xaxis_title="Strike",
                yaxis_title=selected_y_axis or "Selected Metric",
                annotations=[dict(text=f"Error: {str(e)[:100]}...", showarrow=False, xref="paper", yref="paper", x=0.5, y=0.5)],
                paper_bgcolor=default_theme.panel_bg,
                plot_bgcolor=default_theme.base_bg,
                font_color=default_theme.text_light,
                xaxis=dict(showgrid=True, gridcolor=default_theme.secondary),
                yaxis=dict(showgrid=True, gridcolor=default_theme.secondary)
            )
    
    return data_json, fig, underlying_options, underlying_value, table_data, table_columns

@monitor()
def create_analysis_graph(data_dict, y_axis_column, underlying_key='base', scenario_values=None):
    """
    Helper function to create the analysis graph figure with multiple series from different expiries
    for a selected underlying value.
    
    Args:
        data_dict (dict): Nested dictionary with structure {underlying: {expiry: dataframe}}
        y_axis_column (str): Column name to use for the Y-axis
        underlying_key (str): Key of the underlying value to plot (e.g., 'base', '-4bp', '-8bp', etc.)
        scenario_values (dict): Dictionary containing scenario values for graph title
        
    Returns:
        go.Figure: Plotly figure object with all series
    """
    fig = go.Figure()
    
    # Get appropriate label for the y-axis based on predefined options
    y_axis_options = [
        {"label": "Implied Vol", "value": "Implied Vol (Daily BP)"},
        {"label": "Delta (%)", "value": "%Delta"},
        {"label": "Vega", "value": "Vega"},
        {"label": "Gamma", "value": "DV01 Gamma"},
        {"label": "Theta", "value": "Theta"},
    ]
    y_axis_label = next((item["label"] for item in y_axis_options if item["value"] == y_axis_column), y_axis_column)
    
    # Check if we have any valid data for the selected underlying
    if not data_dict or underlying_key not in data_dict:
        fig.update_layout(
            title="No data available for selected underlying",
            xaxis_title="Strike",
            yaxis_title=y_axis_label,
            annotations=[dict(text="No data available", showarrow=False, xref="paper", yref="paper", x=0.5, y=0.5)],
            paper_bgcolor=default_theme.panel_bg,
            plot_bgcolor=default_theme.base_bg,
            font_color=default_theme.text_light,
            xaxis=dict(showgrid=True, gridcolor=default_theme.secondary),
            yaxis=dict(showgrid=True, gridcolor=default_theme.secondary),
            height=400
        )
        return fig
    
    # Get the expiry dictionary for the selected underlying
    expiry_dict = data_dict[underlying_key]
    
    # Track if any data was actually plotted
    data_plotted = False
    
    # Plot each expiry series for the selected underlying
    for expiry, df in sorted(expiry_dict.items()):
        # Skip if DataFrame is empty or missing required columns
        if df.empty or "Strike" not in df.columns or y_axis_column not in df.columns:
            logger.debug(f"Skipping {underlying_key}/{expiry}: Missing data or required columns")
            continue
        
        # Get color for this expiry (fallback to 'other' if not in color map)
        color = EXPIRY_COLORS.get(expiry, EXPIRY_COLORS["other"])
        
        # Get the data for plotting
        x_data = df["Strike"]
        y_data = df[y_axis_column]
        
        # Ensure numeric conversion for all numeric columns, especially %Delta
        if y_axis_column == "%Delta":
            # Handle percentage values by removing % if present and converting to numeric
            y_data = pd.to_numeric(y_data.astype(str).str.replace('%', ''), errors='coerce')
        elif y_axis_column in ["Strike", "Implied Vol (Daily BP)", "DV01 Gamma", "Theta", "Vega"]:
            # Also ensure other numeric columns are properly converted
            y_data = pd.to_numeric(y_data, errors='coerce')
        
        # Get Trade Description data for hover tooltips
        if "Trade Description" in df.columns:
            trade_desc = df["Trade Description"]
            # Create custom hover text
            hovertemplate = "<b>%{customdata}</b><br>" + \
                           f"Strike: %{{x}}<br>" + \
                           f"{y_axis_label}: %{{y}}<br>" + \
                           "<extra></extra>"  # Hide secondary box
        else:
            trade_desc = None
            hovertemplate = None
        
        # Skip series with all NaN values
        if y_data.isna().all():
            logger.debug(f"Skipping {underlying_key}/{expiry}: All NaN values for {y_axis_column}")
            continue
        
        # Add the scatter trace to the figure
        fig.add_trace(go.Scatter(
            x=x_data,
            y=y_data,
            mode='lines+markers',
            name=expiry,  # Use expiry as the series name in legend
            customdata=trade_desc,  # Add trade description as custom data
            hovertemplate=hovertemplate,  # Use custom hover template
            marker=dict(color=color, size=8),
            line=dict(color=color, width=2)
        ))
        
        data_plotted = True
    
    # If no data was plotted, show a message
    if not data_plotted:
        fig.update_layout(
            title=f"No plottable data for selected metric and underlying",
            xaxis_title="Strike",
            yaxis_title=y_axis_label,
            annotations=[dict(text=f"No data available for {y_axis_label}", showarrow=False, xref="paper", yref="paper", x=0.5, y=0.5)],
            paper_bgcolor=default_theme.panel_bg,
            plot_bgcolor=default_theme.base_bg,
            font_color=default_theme.text_light,
            xaxis=dict(showgrid=True, gridcolor=default_theme.secondary),
            yaxis=dict(showgrid=True, gridcolor=default_theme.secondary),
            height=400
        )
        return fig
    
    # Get display name for the underlying scenario
    scenario_display = SCENARIOS.get(underlying_key, {}).get('display_name', underlying_key)
    
    # Get underlying values for this specific scenario
    underlying_values = scenario_values.get(underlying_key, []) if scenario_values else []
    
    # Create title with underlying info
    title = f"{y_axis_label} vs Strike"
    
    # Add underlying information to title
    if underlying_values:
        unique_values = list(set(underlying_values))
        if len(unique_values) == 1:
            # Single contract
            title += f" - {scenario_display} ({unique_values[0]})"
        elif len(unique_values) > 1:
            # Contract transition
            contracts_display = f"{unique_values[0]} → {unique_values[-1]}"
            title += f" - {scenario_display} ({contracts_display})"
        else:
            # No unique values
            title += f" - {scenario_display}"
    else:
        # Fallback if no underlying values available
        title += f" - {scenario_display}"
    
    # Update layout with proper titles and styling
    fig.update_layout(
        title=title,
        xaxis_title="Strike",
        yaxis_title=y_axis_label,
        paper_bgcolor=default_theme.panel_bg,
        plot_bgcolor=default_theme.base_bg,
        font_color=default_theme.text_light,
        xaxis=dict(showgrid=True, gridcolor=default_theme.secondary),
        yaxis=dict(showgrid=True, gridcolor=default_theme.secondary),
        height=400,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            bgcolor=default_theme.panel_bg,
            font=dict(color=default_theme.text_light)
        )
    )
    
    return fig
@monitor()
def prepare_table_data(data_dict, underlying_key, y_axis_column):
    """
    Transform nested dictionary data to a flat format suitable for DataTable display.
    
    Args:
        data_dict (dict): Nested dictionary with structure {underlying: {expiry: dataframe}}
        underlying_key (str): Key of the underlying value to use
        y_axis_column (str): Column name to extract for table values
        
    Returns:
        tuple: (data_records, columns) where:
            - data_records is a list of dicts for DataTable's data prop
            - columns is a list of column definitions for DataTable's columns prop
    """
    # Check if we have valid data
    if not data_dict or underlying_key not in data_dict:
        # Return empty data and basic columns if no data
        columns = [
            {"name": "Strike", "id": "Strike"},
        ] + [{"name": f"{expiry}", "id": f"{expiry}"} for expiry in ["1st", "2nd", "3rd", "4th", "5th", "6th", "7th"]]
        return [], columns
    
    # Get data for the selected underlying
    expiry_dict = data_dict[underlying_key]
    
    # Collect all unique strikes across all expiries
    all_strikes = set()
    for expiry, df in expiry_dict.items():
        if not df.empty and "Strike" in df.columns:
            all_strikes.update(df["Strike"].dropna().unique())
    
    # Sort strikes in ascending order
    all_strikes = sorted(all_strikes)
    
    # Create a record for each strike with values from each expiry
    data_records = []
    for strike in all_strikes:
        record = {"Strike": strike}
        
        # Get value for each expiry
        for expiry, df in expiry_dict.items():
            if not df.empty and "Strike" in df.columns and y_axis_column in df.columns:
                # Find row with matching strike
                strike_row = df[df["Strike"] == strike]
                if not strike_row.empty:
                    value = strike_row[y_axis_column].iloc[0]
                    
                    # Format the value based on type
                    if pd.isna(value):
                        record[expiry] = "-"
                    elif isinstance(value, (int, float)):
                        # For Delta column, show as percentage
                        if y_axis_column == "%Delta":
                            record[expiry] = f"{value*100:.2f}%"
                        # Format with appropriate decimal places based on magnitude
                        elif abs(value) < 0.01:
                            record[expiry] = f"{value:.4f}"
                        else:
                            record[expiry] = f"{value:.2f}"
                    else:
                        # Try to convert string to number if possible
                        try:
                            num_value = float(str(value).replace('%', ''))
                            if y_axis_column == "%Delta":
                                record[expiry] = f"{num_value:.2f}%"
                            elif abs(num_value) < 0.01:
                                record[expiry] = f"{num_value:.4f}"
                            else:
                                record[expiry] = f"{num_value:.2f}"
                        except (ValueError, TypeError):
                            record[expiry] = str(value)
                else:
                    record[expiry] = "-"
            else:
                record[expiry] = "-"
        
        data_records.append(record)
    
    # Define columns for the DataTable
    columns = [
        {"name": "Strike", "id": "Strike"},
    ] + [{"name": f"{expiry}", "id": f"{expiry}"} for expiry in ["1st", "2nd", "3rd", "4th", "5th", "6th", "7th"]]
    
    return data_records, columns

# Callback to toggle between Graph and Table views
@app.callback(
    [Output("graph-view-container", "style"),
     Output("table-view-container", "style"),
     Output("view-toggle-graph", "style"),
     Output("view-toggle-table", "style")],
    [Input("view-toggle-graph", "n_clicks"),
     Input("view-toggle-table", "n_clicks")],
    prevent_initial_call=True
)
@monitor()
def toggle_view(graph_clicks, table_clicks):
    # Determine which button was clicked last
    ctx = dash.callback_context
    if not ctx.triggered:
        # Default to graph view on page load
        return {'display': 'block'}, {'display': 'none'}, \
               {'borderTopRightRadius': '0', 'borderBottomRightRadius': '0', 'borderRight': 'none', 
                'backgroundColor': default_theme.primary}, \
               {'borderTopLeftRadius': '0', 'borderBottomLeftRadius': '0', 'backgroundColor': default_theme.panel_bg}
    
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if triggered_id == "view-toggle-graph":
        # Switch to Graph view
        return {'display': 'block'}, {'display': 'none'}, \
               {'borderTopRightRadius': '0', 'borderBottomRightRadius': '0', 'borderRight': 'none', 
                'backgroundColor': default_theme.primary}, \
               {'borderTopLeftRadius': '0', 'borderBottomLeftRadius': '0', 'backgroundColor': default_theme.panel_bg}
    else:
        # Switch to Table view
        return {'display': 'none'}, {'display': 'block'}, \
               {'borderTopRightRadius': '0', 'borderBottomRightRadius': '0', 'borderRight': 'none', 
                'backgroundColor': default_theme.panel_bg}, \
               {'borderTopLeftRadius': '0', 'borderBottomLeftRadius': '0', 'backgroundColor': default_theme.primary}

# --- Logs Tab Callbacks ---
@app.callback(
    [Output("flow-trace-grid", "style"),
     Output("performance-metrics-grid", "style"),
     Output("logs-toggle-flow", "style"),
     Output("logs-toggle-performance", "style")],
    [Input("logs-toggle-flow", "n_clicks"),
     Input("logs-toggle-performance", "n_clicks")],
    prevent_initial_call=False
)
@monitor()
def toggle_logs_tables(flow_clicks, performance_clicks):
    """Toggle visibility between Flow Trace and Performance tables."""
    # Set basic styles
    flow_trace_style = {"backgroundColor": default_theme.panel_bg, "padding": "15px", "borderRadius": "5px"}
    performance_style = {"backgroundColor": default_theme.panel_bg, "padding": "15px", "borderRadius": "5px"}
    
    # Button style bases
    flow_btn_style = {
        'borderTopRightRadius': '0',
        'borderBottomRightRadius': '0',
        'borderRight': 'none'
    }
    perf_btn_style = {
        'borderTopLeftRadius': '0', 
        'borderBottomLeftRadius': '0'
    }
    
    # Determine which button was clicked last
    ctx = dash.callback_context
    
    # Default to flow trace view on first load or if no clear trigger
    if not ctx.triggered or flow_clicks is None or performance_clicks is None:
        flow_trace_style["display"] = "block"
        performance_style["display"] = "none"
        flow_btn_style["backgroundColor"] = default_theme.primary
        perf_btn_style["backgroundColor"] = default_theme.panel_bg
        return flow_trace_style, performance_style, flow_btn_style, perf_btn_style
    
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if triggered_id == "logs-toggle-flow":
        # Show Flow Trace
        flow_trace_style["display"] = "block"
        performance_style["display"] = "none"
        flow_btn_style["backgroundColor"] = default_theme.primary  # Active
        perf_btn_style["backgroundColor"] = default_theme.panel_bg  # Inactive
    else:  # logs-toggle-performance
        # Show Performance
        flow_trace_style["display"] = "none"
        performance_style["display"] = "block"
        flow_btn_style["backgroundColor"] = default_theme.panel_bg  # Inactive
        perf_btn_style["backgroundColor"] = default_theme.primary   # Active
    
    return flow_trace_style, performance_style, flow_btn_style, perf_btn_style

@app.callback(
    [Output("flow-trace-table", "data"),
     Output("performance-metrics-table", "data")],
    [Input("logs-refresh-button", "n_clicks")],
    prevent_initial_call=True
)
@monitor()
def refresh_log_data(n_clicks):
    """
    Refresh log data by querying the SQLite database.
    Updates both tables' data when the Refresh Logs button is clicked.
    """
    # Return empty lists instead of raising PreventUpdate
    if n_clicks is None:
        return [], []
    
    try:
        # Query both tables
        flow_trace_data = query_flow_trace_logs(limit=100)
        performance_data = query_performance_metrics()
        
        logger.info(f"Refreshed log data: {len(flow_trace_data)} flow trace records, {len(performance_data)} performance records")
        
        return flow_trace_data, performance_data
    except Exception as e:
        logger.error(f"Error refreshing log data: {e}", exc_info=True)
        return [], []

# --- End Callbacks ---

@monitor()
def empty_log_tables():
    """
    Empty the flowTrace and AveragePerformance tables in the SQLite log database.
    """
    try:
        import sqlite3
        conn = sqlite3.connect(LOG_DB_PATH)
        cursor = conn.cursor()
        
        # Delete all rows from the flowTrace table
        cursor.execute("DELETE FROM flowTrace")
        
        # Delete all rows from the AveragePerformance table
        cursor.execute("DELETE FROM AveragePerformance")
        
        # Commit the changes
        conn.commit()
        
        # Get the number of deleted rows (for logging purposes)
        cursor.execute("SELECT changes()")
        deleted_rows = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        logger.info(f"Emptied log tables: {deleted_rows} rows deleted")
        return True
    except Exception as e:
        logger.error(f"Error emptying log tables: {e}", exc_info=True)
        return False

@app.callback(
    [Output("logs-empty-button", "n_clicks"),
     Output("logs-refresh-button", "n_clicks")],
    Input("logs-empty-button", "n_clicks"),
    prevent_initial_call=True
)
@monitor()
def empty_logs(n_clicks):
    """
    Empty the logs database tables when the Empty Table button is clicked.
    Resets the n_clicks to avoid retriggering and increments the refresh button's n_clicks
    to trigger a refresh of the tables.
    """
    if n_clicks is None or n_clicks == 0:
        raise PreventUpdate
    
    success = empty_log_tables()
    
    if success:
        logger.info("Successfully emptied log tables")
    else:
        logger.error("Failed to empty log tables")
    
    # Return 0 to reset the empty button n_clicks counter and
    # an incremented value for the refresh button to trigger refresh
    return 0, n_clicks

# --- End Function Wrappers ---

# --- Greek Analysis Callbacks ---
@app.callback(
    [Output("acp-greek-profiles-store", "data"),
     Output("acp-implied-vol-display", "children"),
     Output("acp-greek-summary-container", "children"),
     Output("acp-greek-table-container", "children"),
     # Greek profile outputs
     Output("acp-profile-delta-container", "children"),
     Output("acp-profile-gamma-container", "children"),
     Output("acp-profile-vega-container", "children"),
     Output("acp-profile-theta-container", "children"),
     Output("acp-profile-volga-container", "children"),
     Output("acp-profile-vanna-container", "children"),
     Output("acp-profile-charm-container", "children"),
     Output("acp-profile-speed-container", "children"),
     Output("acp-profile-color-container", "children"),
     Output("acp-profile-ultima-container", "children"),
     Output("acp-profile-zomma-container", "children"),
     # Taylor error output
     Output("acp-taylor-error-container", "children")],
    [Input("acp-recalculate-button", "n_clicks")],
    [State("acp-strike-input", "value"),
     State("acp-future-price-input", "value"),
     State("acp-days-to-expiry-input", "value"),
     State("acp-market-price-input", "value"),
     State("acp-dv01-input", "value"),
     State("acp-convexity-input", "value"),
     State("acp-option-type-selector", "value")]
)
@monitor()
def acp_update_greek_analysis(n_clicks, strike, future_price, time_to_expiry, market_price_decimal,
                         dv01, convexity, option_type):
    """Recalculate Greeks based on input parameters"""
    
    # Validate inputs - ensure no None values
    if any(x is None for x in [strike, future_price, time_to_expiry, market_price_decimal, dv01, convexity]):
        # Return empty results if any input is missing
        return {}, "Please fill in all input fields", html.Div("Missing input values"), html.Div(), \
               html.Div(), html.Div(), html.Div(), html.Div(), html.Div(), html.Div(), \
               html.Div(), html.Div(), html.Div(), html.Div(), html.Div(), html.Div()
    
    # Market price is already in decimal format
    market_price = market_price_decimal
    
    # Time to expiry is already in years
    T = time_to_expiry
    
    # Run analysis
    results = analyze_bond_future_option_greeks(
        future_dv01=dv01,
        future_convexity=convexity,
        F=future_price,
        K=strike,
        T=T,
        market_price=market_price,
        option_type=option_type
    )
    
    # Get the results
    df_profiles = pd.DataFrame(results['greek_profiles'])
    implied_vol = results['implied_volatility']
    current_greeks = results['current_greeks']
    
    # Format implied volatility display
    yield_vol = results['model'].convert_price_to_yield_volatility(implied_vol)
    vol_display = f"Price Vol: {implied_vol:.2f} | Yield Vol: {yield_vol:.2f}"
    
    # Individual Greek graphs removed from display
    
    # Placeholder for Greek tables - will be populated later after store_data is created
    greek_tables_grid = html.Div()
    
    # Create Greek Summary Table showing current values at market price
    greek_summary_data = []
    
    # Define Greek mapping with proper column names and display names
    greek_mapping = [
        ('delta_y', 'Delta (Y-Space)', 'Y-Space'),
        ('gamma_y', 'Gamma (Y-Space)', 'Y-Space'),
        ('vega_y', 'Vega (Y-Space)', 'Y-Space'),
        ('theta_F', 'Theta (F-Space)', 'F-Space'),
        ('volga_price', 'Volga (Price Vol)', 'Price'),
        ('vanna_F_price', 'Vanna (F-Price)', 'F-Price'),
        ('charm_F', 'Charm (F-Space)', 'F-Space'),
        ('speed_F', 'Speed (F-Space)', 'F-Space'),
        ('color_F', 'Color (F-Space)', 'F-Space'),
        ('ultima', 'Ultima', ''),
        ('zomma', 'Zomma', '')
    ]
    
    # Extract current Greek values
    for greek_key, greek_name, space_type in greek_mapping:
        if greek_key in current_greeks:
            value = current_greeks[greek_key]
            # Format the value based on its magnitude
            if abs(value) < 0.0001:
                formatted_value = f"{value:.6f}"
            elif abs(value) < 0.01:
                formatted_value = f"{value:.4f}"
            else:
                formatted_value = f"{value:.2f}"
            
            row = {
                'Greek': greek_name,
                'Value': formatted_value,
                'Space': space_type
            }
            greek_summary_data.append(row)
    
    # Create the summary table
    greek_summary_table = DataTable(
        id="acp-greek-summary-table",
        data=greek_summary_data,
        columns=[
            {"name": "Greek", "id": "Greek"},
            {"name": "Value", "id": "Value"},
            {"name": "Space", "id": "Space"}
        ],
        theme=default_theme,
        style_cell={
            'backgroundColor': default_theme.base_bg,
            'color': default_theme.text_light,
            'textAlign': 'left',
            'padding': '10px',
            'whiteSpace': 'normal',
            'height': 'auto',
            'minWidth': '100px',
            'width': '120px',
            'maxWidth': '150px',
        },
        style_header={
            'backgroundColor': default_theme.secondary,
            'color': default_theme.primary,
            'fontWeight': '500',
            'textAlign': 'center'
        },
        style_data_conditional=[
            {
                'if': {'column_id': 'Value'},
                'textAlign': 'right',
                'fontWeight': 'bold'
            },
            {
                'if': {'column_id': 'Space'},
                'textAlign': 'center',
                'fontStyle': 'italic',
                'color': default_theme.text_subtle
            }
        ],
        style_table={
            'width': '100%',
            'maxWidth': '500px',
            'margin': 'auto'
        }
    ).render()
    
    # Create the summary container
    greek_summary_container = Container(
        id="acp-greek-summary-panel",
        children=[
            html.H4("Current Greek Values at Market Price", 
                   style={"color": default_theme.primary, "marginBottom": "15px", "textAlign": "center"}),
            greek_summary_table
        ],
        theme=default_theme,
        style={'padding': '20px', 'marginBottom': '20px', 'backgroundColor': default_theme.panel_bg, 
               'borderRadius': '4px', 'border': f'1px solid {default_theme.secondary}'}
    ).render()
    
    # Generate Greek profile data from bachelier_greek.py
    tau = time_to_expiry  # Already in years
    F_range = (future_price - 10, future_price + 10)  # ±10 from current price
    
    # Generate profile data
    profile_data = generate_greek_profiles_data(
        K=strike,
        sigma=implied_vol,
        tau=tau,
        F_range=F_range
    )
    
    # Generate Taylor error data
    taylor_data = generate_taylor_error_data(
        K=strike,
        sigma=implied_vol,
        tau=tau,
        dF=0.1,  # Standard shock sizes
        dSigma=0.01,
        dTau=0.01,
        F_range=F_range
    )
    
    # Create profile graphs with appropriate mapping and scaling
    # Map bachelier names to dashboard names and apply scaling
    greek_profile_mapping = [
        ('delta', 'delta_y', 'Delta (Y-Space)', dv01),
        ('gamma', 'gamma_y', 'Gamma (Y-Space)', dv01 * dv01),
        ('vega', 'vega_y', 'Vega (Y-Space)', dv01),
        ('theta', 'theta_F', 'Theta (F-Space)', 1.0),
        ('volga', 'volga_price', 'Volga (Price Vol)', 1.0),
        ('vanna', 'vanna_F_price', 'Vanna (F-Price)', 1.0),
        ('charm', 'charm_F', 'Charm (F-Space)', 1.0),
        ('speed', 'speed_F', 'Speed (F-Space)', 1.0),
        ('color', 'color_F', 'Color (F-Space)', 1.0),
        ('ultima', 'ultima', 'Ultima', 1.0),
        ('zomma', 'zomma', 'Zomma', 1.0)
    ]
    
    profile_graphs = []
    for bachelier_name, dashboard_name, title, scale_factor in greek_profile_mapping:
        if bachelier_name in profile_data.get('greeks_ana', {}):
            # Create data with scaling applied
            F_values = profile_data['F_vals']
            greek_values = np.array(profile_data['greeks_ana'][bachelier_name])
            
            # Apply option type adjustment for delta
            if bachelier_name == 'delta' and option_type == 'put':
                greek_values = greek_values - 1.0
            
            # Apply daily conversion for theta
            if bachelier_name == 'theta':
                greek_values = greek_values / 252.0
            
            # Apply scaling
            greek_values = greek_values * scale_factor * 1000  # Apply scale and ×1000
            
            # Create the figure with both analytical and numerical profiles
            fig = go.Figure()
            
            # Add analytical profile
            fig.add_trace(go.Scatter(
                x=F_values,
                y=greek_values,
                mode='lines',
                name='Analytical (Bachelier Model)',
                line=dict(color=default_theme.primary, width=2)
            ))
            
            # Add vertical lines for current price and strike
            fig.add_vline(x=future_price, line_dash="dash", line_color=default_theme.accent, 
                         annotation_text="Current", annotation_position="top")
            fig.add_vline(x=strike, line_dash="dot", line_color=default_theme.danger, 
                         annotation_text="Strike", annotation_position="bottom")
            
            # Update layout
            fig.update_layout(
                title=title,
                xaxis_title="Future Price",
                yaxis_title=dashboard_name,
                plot_bgcolor=default_theme.base_bg,
                paper_bgcolor=default_theme.panel_bg,
                font_color=default_theme.text_light,
                xaxis=dict(showgrid=True, gridcolor=default_theme.secondary),
                yaxis=dict(showgrid=True, gridcolor=default_theme.secondary),
                margin=dict(l=60, r=20, t=60, b=50),
                height=300,
                legend=dict(
                    orientation='h',  # Horizontal layout
                    x=1.0,  # Right edge
                    y=1.15,  # Above the plot area, inline with title
                    xanchor='right',
                    yanchor='bottom',
                    bgcolor='rgba(0,0,0,0)',  # Transparent background
                    bordercolor=default_theme.text_subtle,
                    borderwidth=0
                )
            )
            
            # Create Graph component
            graph = Graph(
                id=f"acp-profile-{dashboard_name}-graph",
                figure=fig,
                theme=default_theme
            ).render()
            
            profile_graphs.append(graph)
        else:
            profile_graphs.append(html.Div("Greek not available", style={"color": default_theme.text_subtle}))
    
    # Create Taylor error graph
    taylor_fig = go.Figure()
    
    # Add lines for different approximation methods
    F_values = taylor_data['F_vals']
    colors = {
        'errors_ana': default_theme.primary,
        'errors_ana_cross': default_theme.accent,
    }
    
    method_names = {
        'errors_ana': 'Analytical',
        'errors_ana_cross': 'Analytical + Cross',
    }
    
    # Get future prices for basis points calculation
    F_values = taylor_data.get('F_vals', None)
    
    for method_key, display_name in method_names.items():
        if method_key in taylor_data:
            # Convert absolute error to basis points of underlying
            if F_values is not None:
                # Calculate error in basis points: (absolute_error / future_price) * 10000
                # Avoid division by zero by using a small epsilon
                epsilon = 1e-10
                basis_points_errors = []
                for i, abs_error in enumerate(taylor_data[method_key]):
                    future_price = F_values[i]
                    if abs(future_price) > epsilon:
                        basis_points_error = (abs_error / abs(future_price)) * 10000
                    else:
                        basis_points_error = 0.0  # Set to 0 when future price is near zero
                    basis_points_errors.append(basis_points_error)
                
                y_data = basis_points_errors
            else:
                # Fallback: if F_values not available, multiply by 10000 assuming already normalized
                y_data = [val * 10000 for val in taylor_data[method_key]]
            
            taylor_fig.add_trace(go.Scatter(
                x=F_values,
                y=y_data,
                mode='lines',
                name=display_name,
                line=dict(color=colors[method_key], width=2)
            ))
    
    # Add vertical lines
    taylor_fig.add_vline(x=future_price, line_dash="dash", line_color=default_theme.accent, 
                        annotation_text="Current", annotation_position="top")
    taylor_fig.add_vline(x=strike, line_dash="dot", line_color=default_theme.danger, 
                        annotation_text="Strike", annotation_position="bottom")
    
    # Update layout
    taylor_fig.update_layout(
        title="Taylor Approximation Error Analysis",
        xaxis_title="Future Price",
        yaxis_title="Prediction Error (bps of Underlying)",
        plot_bgcolor=default_theme.base_bg,
        paper_bgcolor=default_theme.panel_bg,
        font_color=default_theme.text_light,
        xaxis=dict(showgrid=True, gridcolor=default_theme.secondary),
        yaxis=dict(
            showgrid=True, 
            gridcolor=default_theme.secondary, 
            type='linear',
            tickformat='.1f',  # Format ticks to 1 decimal place
            ticksuffix=' bps'  # Add bps suffix to tick labels
        ),
        margin=dict(l=60, r=20, t=60, b=50),
        height=400,
        legend=dict(
            orientation='h',  # Horizontal layout
            x=1.0,  # Right edge
            y=1.12,  # Above the plot area, inline with title
            xanchor='right',
            yanchor='bottom',
            bgcolor='rgba(0,0,0,0)',  # Transparent background
            bordercolor=default_theme.text_subtle,
            borderwidth=0
        )
    )
    
    taylor_graph = Graph(
        id="acp-taylor-error-graph",
        figure=taylor_fig,
        theme=default_theme
    ).render()
    
    # Store data for potential export
    store_data = {
        'profiles': df_profiles.to_dict('records'),
        'current_greeks': current_greeks,
        'profile_data': profile_data,  # Add profile data for table generation
        'taylor_data': taylor_data,     # Add taylor data for table generation
        'parameters': {
            'strike': strike,
            'future_price': future_price,
            'time_to_expiry': time_to_expiry,
            'option_type': option_type,
            'implied_vol': implied_vol,
            'dv01': dv01
        }
    }
    
    # Return all outputs including new profile graphs
    return (store_data, vol_display, greek_summary_container, greek_tables_grid,
            # Profile graphs
            profile_graphs[0], profile_graphs[1], profile_graphs[2], profile_graphs[3],
            profile_graphs[4], profile_graphs[5], profile_graphs[6], profile_graphs[7],
            profile_graphs[8], profile_graphs[9], profile_graphs[10],
            # Taylor error graph
            taylor_graph)

@app.callback(
    Output("acp-greek-table-container", "children", allow_duplicate=True),
    [Input("acp-greek-profiles-store", "data"),
     Input("acp-view-mode-table-btn", "n_clicks")],
    [State("acp-view-mode-graph-btn", "n_clicks")],
    prevent_initial_call=True
)
@monitor()
def acp_generate_table_view(store_data, table_clicks, graph_clicks):
    """Generate table view content when in table mode"""
    # Determine if we're in table view
    ctx = dash.callback_context
    if not store_data:
        return html.Div()
    
    # Check which button was clicked last
    is_table_view = False
    if ctx.triggered:
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if triggered_id == "acp-view-mode-table-btn":
            is_table_view = True
    else:
        # Check click counts
        table_clicks = table_clicks or 0
        graph_clicks = graph_clicks or 0
        is_table_view = table_clicks > graph_clicks
    
    if not is_table_view:
        return html.Div()
    
    # Generate tables from stored data
    profile_data = store_data.get('profile_data', {})
    taylor_data = store_data.get('taylor_data', {})
    parameters = store_data.get('parameters', {})
    
    if not profile_data:
        return html.Div("No profile data available", style={"color": default_theme.text_subtle})
    
    # Extract parameters
    dv01 = parameters.get('dv01', 100.0)
    option_type = parameters.get('option_type', 'call')
    
    # Create tables from the profile data
    greek_profile_tables = []
    
    # Greek profile mapping (same as used for graphs)
    greek_profile_mapping = [
        ('delta', 'delta_y', 'Delta (Y-Space)', dv01),
        ('gamma', 'gamma_y', 'Gamma (Y-Space)', dv01 * dv01),
        ('vega', 'vega_y', 'Vega (Y-Space)', dv01),
        ('theta', 'theta_F', 'Theta (F-Space)', 1.0),
        ('volga', 'volga_price', 'Volga (Price Vol)', 1.0),
        ('vanna', 'vanna_F_price', 'Vanna (F-Price)', 1.0),
        ('charm', 'charm_F', 'Charm (F-Space)', 1.0),
        ('speed', 'speed_F', 'Speed (F-Space)', 1.0),
        ('color', 'color_F', 'Color (F-Space)', 1.0),
        ('ultima', 'ultima', 'Ultima', 1.0),
        ('zomma', 'zomma', 'Zomma', 1.0),
        ('veta', 'veta', 'Veta', 1.0)  # Include veta if available
    ]
    
    # Generate table for each Greek profile
    for bachelier_name, dashboard_name, title, scale_factor in greek_profile_mapping:
        if bachelier_name in profile_data.get('greeks_ana', {}):
            # Create table data
            table_rows = []
            F_values = profile_data['F_vals']
            greek_ana = np.array(profile_data['greeks_ana'][bachelier_name])
            
            # Apply option type and daily conversion adjustments
            if bachelier_name == 'delta' and option_type == 'put':
                greek_ana = greek_ana - 1.0
            if bachelier_name == 'theta':
                greek_ana = greek_ana / 252.0
                
            # Apply scaling
            greek_ana = greek_ana * scale_factor * 1000
            
            # Get numerical values if available
            # Commented out numerical calculations - showing analytical only
            # greek_num = None
            # if bachelier_name in profile_data.get('greeks_num', {}):
            #     greek_num = np.array(profile_data['greeks_num'][bachelier_name])
            #     if bachelier_name == 'delta' and option_type == 'put':
            #         greek_num = greek_num - 1.0
            #     if bachelier_name == 'theta':
            #         greek_num = greek_num / 252.0
            #     greek_num = greek_num * scale_factor * 1000
            greek_num = None  # Force None to skip numerical display
            
            # Create table rows (show all points)
            for i in range(len(F_values)):
                row = {
                    'Future Price': f"{F_values[i]:.3f}",
                    'Analytical': f"{greek_ana[i]:.6f}",
                }
                if greek_num is not None:
                    row['Numerical'] = f"{greek_num[i]:.6f}"
                table_rows.append(row)
            
            # Create columns
            columns = [
                {"name": "Future Price", "id": "Future Price"},
                {"name": "Analytical", "id": "Analytical"},
            ]
            if greek_num is not None:
                columns.append({"name": "Numerical", "id": "Numerical"})
            
            # Create the table
            table = Container(
                id=f"acp-profile-{dashboard_name}-table-container",
                children=[
                    html.H6(title, style={"color": default_theme.primary, "marginBottom": "10px"}),
                    DataTable(
                        id=f"acp-profile-{dashboard_name}-table",
                        data=table_rows,
                        columns=columns,
                        theme=default_theme,
                        page_size=len(table_rows),  # Show all rows without pagination
                        style_cell={
                            'backgroundColor': default_theme.base_bg,
                            'color': default_theme.text_light,
                            'textAlign': 'right',
                            'padding': '5px',
                            'fontSize': '12px'
                        },
                        style_header={
                            'backgroundColor': default_theme.secondary,
                            'color': default_theme.primary,
                            'fontWeight': '500',
                            'textAlign': 'center'
                        },
                        style_table={
                            'overflowY': 'auto'  # Removed fixed height to show all rows
                        },
                        style_data_conditional=[
                            {
                                'if': {'column_id': 'Future Price'},
                                'fontWeight': 'bold'
                            }
                        ]
                    ).render()
                ],
                theme=default_theme,
                style={'marginBottom': '20px'}
            ).render()
            
            greek_profile_tables.append((table, {"width": 4}))
    
    # Create Taylor error table
    if taylor_data:
        taylor_rows = []
        F_values = taylor_data.get('F_vals', [])
        
        # Show all points
        for i in range(len(F_values)):
            row = {'Future Price': f"{F_values[i]:.3f}"}
            
            # Convert absolute errors to basis points of underlying
            if F_values:
                # Calculate basis points error with division by zero protection
                epsilon = 1e-10
                future_price = F_values[i]
                abs_future_price = abs(future_price) if abs(future_price) > epsilon else epsilon
                
                if 'errors_ana' in taylor_data:
                    basis_points_error = (taylor_data['errors_ana'][i] / abs_future_price) * 10000
                    row['Analytical'] = f"{basis_points_error:.1f} bps"
                if 'errors_ana_cross' in taylor_data:
                    basis_points_error = (taylor_data['errors_ana_cross'][i] / abs_future_price) * 10000
                    row['Analytical + Cross'] = f"{basis_points_error:.1f} bps"
                # Commented out numerical + cross error display
                # if 'errors_num_cross' in taylor_data:
                #     basis_points_error = (taylor_data['errors_num_cross'][i] / abs_future_price) * 10000
                #     row['Numerical + Cross'] = f"{basis_points_error:.1f} bps"
            else:
                # Fallback: assume values are already normalized, multiply by 10000
                if 'errors_ana' in taylor_data:
                    row['Analytical'] = f"{taylor_data['errors_ana'][i] * 10000:.1f} bps"
                if 'errors_ana_cross' in taylor_data:
                    row['Analytical + Cross'] = f"{taylor_data['errors_ana_cross'][i] * 10000:.1f} bps"
                # Commented out numerical + cross column
                # if 'errors_num_cross' in taylor_data:
                #     row['Numerical + Cross'] = f"{taylor_data['errors_num_cross'][i] * 10000:.1f} bps"
            
            taylor_rows.append(row)
        
        # Create columns
        taylor_columns = [{"name": "Future Price", "id": "Future Price"}]
        if 'errors_ana' in taylor_data:
            taylor_columns.append({"name": "Analytical", "id": "Analytical"})
        if 'errors_ana_cross' in taylor_data:
            taylor_columns.append({"name": "Analytical + Cross", "id": "Analytical + Cross"})
        # Commented out numerical + cross column
        # if 'errors_num_cross' in taylor_data:
        #     taylor_columns.append({"name": "Numerical + Cross", "id": "Numerical + Cross"})
        
        # Create Taylor error table
        taylor_table = Container(
            id="acp-taylor-error-table-container",
            children=[
                html.H5("Taylor Approximation Error Analysis", 
                       style={"color": default_theme.primary, "marginBottom": "15px", "textAlign": "center"}),
                DataTable(
                    id="acp-taylor-error-table",
                    data=taylor_rows,
                    columns=taylor_columns,
                    theme=default_theme,
                    page_size=len(taylor_rows),  # Show all rows without pagination
                    style_cell={
                        'backgroundColor': default_theme.base_bg,
                        'color': default_theme.text_light,
                        'textAlign': 'right',
                        'padding': '5px'
                    },
                    style_header={
                        'backgroundColor': default_theme.secondary,
                        'color': default_theme.primary,
                        'fontWeight': '500',
                        'textAlign': 'center'
                    },
                    style_table={
                        'overflowY': 'auto',  # Removed fixed height to show all rows
                        'margin': 'auto'
                    },
                    style_data_conditional=[
                        {
                            'if': {'column_id': 'Future Price'},
                            'fontWeight': 'bold'
                        }
                    ]
                ).render()
            ],
            theme=default_theme,
            style={'marginTop': '30px'}
        ).render()
        
        # Combine all tables in a grid
        return html.Div([
            Grid(
                id="acp-greek-profile-tables-grid",
                children=greek_profile_tables,
                theme=default_theme
            ).render(),
            taylor_table
        ])
    else:
        # Just Greek tables
        return Grid(
            id="acp-greek-profile-tables-grid",
            children=greek_profile_tables,
            theme=default_theme
        ).render()

@app.callback(
    [Output("acp-graph-view-container", "style"),
     Output("acp-table-view-container", "style"),
     Output("acp-greek-profile-graphs-container", "style"),
     Output("acp-view-mode-graph-btn", "style"),
     Output("acp-view-mode-table-btn", "style")],
    [Input("acp-view-mode-graph-btn", "n_clicks"),
     Input("acp-view-mode-table-btn", "n_clicks")],
    prevent_initial_call=True
)
@monitor()
def acp_toggle_view_mode(graph_clicks, table_clicks):
    """Toggle between graph and table views"""
    ctx = dash.callback_context
    if not ctx.triggered:
        # Default to graph view
        return (
            {"display": "block"}, {"display": "none"}, {"display": "block"},
            {
                'borderTopRightRadius': '0',
                'borderBottomRightRadius': '0',
                'borderRight': 'none',
                'backgroundColor': default_theme.primary
            },
            {
                'borderTopLeftRadius': '0',
                'borderBottomLeftRadius': '0',
                'backgroundColor': default_theme.panel_bg
            }
        )
    
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if triggered_id == "acp-view-mode-graph-btn":
        # Show graph view - show Greek profile graphs
        return (
            {"display": "block"}, {"display": "none"}, {"display": "block"},
            {
                'borderTopRightRadius': '0',
                'borderBottomRightRadius': '0',
                'borderRight': 'none',
                'backgroundColor': default_theme.primary
            },
            {
                'borderTopLeftRadius': '0',
                'borderBottomLeftRadius': '0',
                'backgroundColor': default_theme.panel_bg
            }
        )
    else:
        # Show table view - hide Greek profile graphs
        return (
            {"display": "none"}, {"display": "block"}, {"display": "none"},
            {
                'borderTopRightRadius': '0',
                'borderBottomRightRadius': '0',
                'borderRight': 'none',
                'backgroundColor': default_theme.panel_bg
            },
            {
                'borderTopLeftRadius': '0',
                'borderBottomLeftRadius': '0',
                'backgroundColor': default_theme.primary
            }
        )

# Trigger initial calculation on load for Greek Analysis
@app.callback(
    Output("acp-recalculate-button", "n_clicks"),
    Input("acp-main-container", "id"),
    prevent_initial_call=False
)
@monitor()
def acp_trigger_initial_calculation(container_id):
    """Trigger calculation on page load"""
    return 1

# --- End Greek Analysis Callbacks ---

# --- Scenario Ladder Callbacks ---
@app.callback(
    [Output('scl-scenario-ladder-table', 'data'),
     Output('scl-scenario-ladder-table-wrapper', 'style'),
     Output('scl-scenario-ladder-message', 'children'),
     Output('scl-scenario-ladder-message', 'style'),
     Output('scl-baseline-store', 'data'),
     Output('scl-baseline-display', 'children')],
    [Input('scl-scenario-ladder-store', 'data'),
     Input('scl-spot-price-store', 'data'),
     Input('scl-refresh-data-button', 'n_clicks')],
    [State('scl-scenario-ladder-table', 'data'),
     State('scl-baseline-store', 'data'),
     State('scl-demo-mode-store', 'data')],
    prevent_initial_call=False
)
@monitor()
def scl_load_and_display_orders(store_data, spot_price_data, n_clicks, current_table_data, baseline_data, demo_mode_data):
    """Load and display working orders from TT API with spot price integration"""
    logger.info("Scenario Ladder callback triggered: load_and_display_orders")
    
    # Determine trigger context
    ctx = dash.callback_context
    triggered_input_info = ctx.triggered[0] if ctx.triggered else {}
    context_id = triggered_input_info.get('prop_id', '')
    
    # Handle different trigger sources  
    is_initial_app_load = (context_id == '.')
    is_store_trigger = (context_id == 'scl-scenario-ladder-store.data')
    
    # Full refresh needed if button clicked or initial load
    full_refresh_needed = (
        context_id == 'scl-refresh-data-button.n_clicks' or
        (is_initial_app_load and store_data and store_data.get('initial_load_trigger')) or
        (is_store_trigger and store_data and store_data.get('initial_load_trigger'))
    )
    
    logger.info(f"Trigger context: '{context_id}', Full refresh needed: {full_refresh_needed}")
    
    # If triggered only by spot price update, just update spot indicators on existing data
    if context_id == 'scl-spot-price-store.data' and spot_price_data and not full_refresh_needed:
        if current_table_data and len(current_table_data) > 0:
            logger.info(f"Spot price update only. current_table_data has {len(current_table_data)} rows.")
            base_pos = baseline_data.get('base_pos', 0) if baseline_data else 0
            base_pnl = baseline_data.get('base_pnl', 0.0) if baseline_data else 0.0
            updated_data = scl_update_data_with_spot_price(current_table_data, spot_price_data, base_pos, base_pnl)
            return updated_data, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        else:
            logger.info("Spot price update, but current_table_data is empty. Letting full load proceed.")
    
    # If not an initial load or refresh button click, don't proceed with full refresh
    if not full_refresh_needed:
        logger.info("Callback skipped: not triggered by initial load or refresh button")
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    # Constants for data paths
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    MOCK_DATA_FILE = os.path.join(project_root, "data", "input", "ladder", "my_working_orders_response.json")
    ACTANT_CSV_FILE = os.path.join(project_root, "data", "input", "sod", "SampleSOD.csv")
    ACTANT_DB_FILEPATH = os.path.join(project_root, "data", "output", "ladder", "actant_data.db")
    ACTANT_TABLE_NAME = "actant_sod_fills"
    
    # Check demo mode state
    use_demo_mode = demo_mode_data.get('demo_mode', True) if demo_mode_data else True
    
    # Price increment for ZN-like instruments
    PRICE_INCREMENT_DECIMAL = 1.0 / 64.0
    
    # TT API constants
    TT_API_BASE_URL = "https://ttrestapi.trade.tt"
    
    orders_data = []
    error_message_str = ""
    
    # Extract spot price
    spot_decimal_val = None
    if spot_price_data and 'decimal_price' in spot_price_data:
        spot_decimal_val = spot_price_data.get('decimal_price')
        if spot_decimal_val is not None:
            logger.info(f"Extracted spot_decimal_val: {spot_decimal_val}")
        else:
            logger.info("spot_price_data present, but decimal_price is None.")
    else:
        logger.info("spot_price_data is None or does not contain 'decimal_price'.")
    
    # Fetch or load working orders
    if use_demo_mode:
        logger.info(f"Using demo mode - loading mock data from: {MOCK_DATA_FILE}")
        try:
            with open(MOCK_DATA_FILE, 'r') as f:
                api_response = json.load(f)
            orders_data = api_response.get('orders', [])
            if not orders_data and isinstance(api_response, list):
                orders_data = api_response
            logger.info(f"Loaded {len(orders_data)} orders from mock file.")
        except Exception as e:
            error_message_str = f"Error loading mock data: {e}"
            logger.error(error_message_str)
            orders_data = []
    else:
        logger.info("Fetching live data from TT API...")
        try:
            token_manager = TTTokenManager(
                environment=ENVIRONMENT,
                token_file_base=TOKEN_FILE,
                app_name=APP_NAME,
                company_name=COMPANY_NAME
            )
            token = token_manager.get_token()
            if not token:
                error_message_str = "Failed to acquire TT API token."
                logger.error(error_message_str)
            else:
                service = "ttledger"
                endpoint = "/orders"
                url = f"{TT_API_BASE_URL}/{service}/{token_manager.env_path_segment}{endpoint}"
                
                request_id = token_manager.create_request_id()
                params = {"requestId": request_id}
                
                headers = {
                    "x-api-key": token_manager.api_key,
                    "accept": "application/json",
                    "Authorization": f"Bearer {token}"
                }
                
                logger.info(f"Making API request to {url} with params: {params}")
                response = requests.get(url, headers=headers, params=params, timeout=30)
                response.raise_for_status()
                
                api_response = response.json()
                orders_data = api_response.get('orders', [])
                if not orders_data and isinstance(api_response, list):
                    orders_data = api_response
                logger.info(f"Received {len(orders_data)} orders from API.")
                
        except requests.exceptions.HTTPError as http_err:
            error_message_str = f"HTTP error fetching orders: {http_err} - {http_err.response.text if http_err.response else 'No response text'}"
            logger.error(error_message_str)
        except Exception as e:
            error_message_str = f"Error fetching live orders: {e}"
            logger.error(error_message_str)
        
        if error_message_str:
            orders_data = []
    
    # Process orders and build ladder
    ladder_table_data = []
    
    # Filter for relevant working orders (status '1') and valid price/qty
    processed_orders = []
    if isinstance(orders_data, list):
        for order in orders_data:
            if isinstance(order, dict) and \
               order.get('orderStatus') == '1' and \
               isinstance(order.get('price'), (int, float)) and \
               isinstance(order.get('leavesQuantity'), (int, float)) and \
               order.get('leavesQuantity') > 0 and \
               order.get('side') in ['1', '2']:
                processed_orders.append({
                    'price': float(order['price']),
                    'qty': float(order['leavesQuantity']),
                    'side': order.get('side')
                })
    logger.info(f"Processed {len(processed_orders)} relevant working orders.")
    
    # Process Actant fill data to get baseline position and P&L
    actant_fills = []
    baseline_results = {'base_pos': 0, 'base_pnl': 0.0}
    baseline_display_text = "No Actant data available"
    
    try:
        # Check if CSV exists and update the SQLite database
        if os.path.exists(ACTANT_CSV_FILE):
            try:
                # Try to use SQLite first
                if os.path.exists(ACTANT_DB_FILEPATH):
                    from lib.trading.ladder import query_sqlite_table
                    logger.info(f"Loading Actant data from SQLite DB {ACTANT_DB_FILEPATH}")
                    
                    # Query the database
                    columns = ["PRICE_TODAY", "QUANTITY", "LONG_SHORT", "ASSET", "PRODUCT_CODE"]
                    df = query_sqlite_table(ACTANT_DB_FILEPATH, ACTANT_TABLE_NAME, columns=columns)
                    
                    if not df.empty:
                        # Filter for ZN futures
                        zn_future_fills = df[(df['ASSET'] == 'ZN') & (df['PRODUCT_CODE'] == 'FUTURE')]
                        
                        if not zn_future_fills.empty:
                            logger.info(f"Found {len(zn_future_fills)} ZN future fills in database")
                            
                            # Process each fill
                            for _, row in zn_future_fills.iterrows():
                                price_str = row.get('PRICE_TODAY')
                                price = scl_convert_tt_special_format_to_decimal(price_str)
                                
                                if price is None:
                                    continue
                                
                                quantity = float(row.get('QUANTITY', 0))
                                if pd.isna(quantity) or quantity == 0:
                                    continue
                                
                                side = row.get('LONG_SHORT', '')
                                if side == 'S':
                                    quantity = -quantity
                                
                                actant_fills.append({
                                    'price': price,
                                    'qty': int(quantity)
                                })
                else:
                    # Fall back to CSV
                    actant_fills = scl_load_actant_zn_fills(ACTANT_CSV_FILE)
            except Exception as e:
                logger.error(f"Error loading from SQLite DB: {e}, falling back to CSV")
                actant_fills = scl_load_actant_zn_fills(ACTANT_CSV_FILE)
        
        logger.info(f"Loaded {len(actant_fills)} Actant ZN fills")
        
        # Calculate baseline position and P&L if we have fills and spot price
        if spot_decimal_val is not None and actant_fills:
            baseline_results = scl_calculate_baseline_from_actant_fills(actant_fills, spot_decimal_val)
            
            # Prepare display text
            pos_str = f"Long {baseline_results['base_pos']}" if baseline_results['base_pos'] > 0 else \
                     f"Short {-baseline_results['base_pos']}" if baseline_results['base_pos'] < 0 else "FLAT"
            pnl_str = f"${baseline_results['base_pnl']:.2f}"
            baseline_display_text = f"Current Position: {pos_str}, Realized P&L @ Spot: {pnl_str}"
            logger.info(f"Baseline from Actant: {baseline_display_text}")
        else:
            logger.info("Either spot price or Actant fills not available for baseline calculation")
    except Exception as e:
        logger.error(f"Error processing Actant data: {e}")
        baseline_display_text = f"Error processing Actant data: {str(e)}"
    
    # Handle early exit cases
    if not processed_orders and not error_message_str and spot_decimal_val is None:
        message_text = "No working orders or spot price found to display."
        logger.info(message_text)
        message_style_visible = {'textAlign': 'center', 'color': default_theme.warning, 'marginBottom': '20px', 'display': 'block'}
        table_style_hidden = {'display': 'none'}
        return [], table_style_hidden, message_text, message_style_visible, baseline_results, baseline_display_text
    elif error_message_str and not processed_orders:
        message_text = error_message_str
        logger.info(f"Displaying error: {message_text}")
        message_style_visible = {'textAlign': 'center', 'color': default_theme.danger, 'marginBottom': '20px', 'display': 'block'}
        table_style_hidden = {'display': 'none'}
        return [], table_style_hidden, message_text, message_style_visible, baseline_results, baseline_display_text
    
    # Build price ladder
    if processed_orders or spot_decimal_val is not None:
        # Calculate overall raw min/max prices
        current_min_raw_price = None
        current_max_raw_price = None
        
        if processed_orders:
            order_prices = [o['price'] for o in processed_orders]
            if order_prices:
                min_order_val = min(order_prices)
                max_order_val = max(order_prices)
                current_min_raw_price = min_order_val
                current_max_raw_price = max_order_val
                logger.info(f"Min/Max from orders: {min_order_val}/{max_order_val}")
        
        if spot_decimal_val is not None:
            logger.info(f"Considering spot_decimal_val for range: {spot_decimal_val}")
            if current_min_raw_price is None or spot_decimal_val < current_min_raw_price:
                current_min_raw_price = spot_decimal_val
            if current_max_raw_price is None or spot_decimal_val > current_max_raw_price:
                current_max_raw_price = spot_decimal_val
        
        logger.info(f"Overall raw min/max before rounding: {current_min_raw_price}/{current_max_raw_price}")
        
        if current_min_raw_price is None:
            logger.info("No valid price data (orders or spot) to form ladder. Returning empty.")
            message_text = "No price data available to display ladder."
            message_style_visible = {'textAlign': 'center', 'color': default_theme.warning, 'marginBottom': '20px', 'display': 'block'}
            table_style_hidden = {'display': 'none'}
            return [], table_style_hidden, message_text, message_style_visible, baseline_results, baseline_display_text
        
        # Round to nearest tick
        ladder_min_price = math.floor(current_min_raw_price / PRICE_INCREMENT_DECIMAL) * PRICE_INCREMENT_DECIMAL
        ladder_max_price = math.ceil(current_max_raw_price / PRICE_INCREMENT_DECIMAL) * PRICE_INCREMENT_DECIMAL
        
        logger.info(f"Ladder min/max after initial rounding: {ladder_min_price}/{ladder_max_price}")
        
        # Add padding
        ladder_min_price -= PRICE_INCREMENT_DECIMAL
        ladder_max_price += PRICE_INCREMENT_DECIMAL
        
        # Re-round for precision after padding
        ladder_min_price = round(ladder_min_price / PRICE_INCREMENT_DECIMAL) * PRICE_INCREMENT_DECIMAL
        ladder_max_price = round(ladder_max_price / PRICE_INCREMENT_DECIMAL) * PRICE_INCREMENT_DECIMAL
        
        logger.info(f"Ladder min/max after padding and re-rounding: {ladder_min_price}/{ladder_max_price}")
        
        # Ensure num_levels is positive
        num_levels = round((ladder_max_price - ladder_min_price) / PRICE_INCREMENT_DECIMAL) + 1
        if num_levels <= 0:
            num_levels = 1
        
        logger.info(f"Final Ladder Price Range: {decimal_to_tt_bond_format(ladder_min_price)} to {decimal_to_tt_bond_format(ladder_max_price)}, Levels: {num_levels}")
        
        current_price_level = ladder_max_price
        epsilon = PRICE_INCREMENT_DECIMAL / 100.0
        
        for _ in range(num_levels):
            formatted_price = decimal_to_tt_bond_format(current_price_level)
            my_qty_at_level = 0
            side_at_level = ""
            
            for order in processed_orders:
                if abs(order['price'] - current_price_level) < epsilon:
                    my_qty_at_level += order['qty']
                    if not side_at_level:
                        side_at_level = order['side']
            
            # Create the row data with spot price indicators
            row_data = {
                'price': formatted_price,
                'my_qty': int(my_qty_at_level) if my_qty_at_level > 0 else "",
                'working_qty_side': side_at_level if my_qty_at_level > 0 else "",
                'decimal_price_val': current_price_level,
                'is_exact_spot': 0,
                'is_below_spot': 0,
                'is_above_spot': 0,
                'projected_pnl': 0,
                'position_debug': 0,
                'risk': 0,
                'breakeven': 0,
            }
            
            ladder_table_data.append(row_data)
            current_price_level -= PRICE_INCREMENT_DECIMAL
            current_price_level = round(current_price_level / PRICE_INCREMENT_DECIMAL) * PRICE_INCREMENT_DECIMAL
        
        # Apply spot price indicators to the ladder data if spot price is available
        if spot_price_data and spot_price_data.get('decimal_price') is not None:
            ladder_table_data = scl_update_data_with_spot_price(
                ladder_table_data,
                spot_price_data,
                base_position=baseline_results['base_pos'],
                base_pnl=baseline_results['base_pnl']
            )
        
        logger.info(f"Generated {len(ladder_table_data)} rows for the ladder.")
        message_text = ""
        message_style_hidden = {'display': 'none'}
        table_style_visible = {'display': 'block', 'width': '600px', 'margin': 'auto'}
        return ladder_table_data, table_style_visible, message_text, message_style_hidden, baseline_results, baseline_display_text
    else:
        message_text = error_message_str if error_message_str else "No working orders or spot price available to display ladder."
        logger.info(f"Final fallback: {message_text}")
        message_style_visible = {'textAlign': 'center', 'color': default_theme.danger if error_message_str else default_theme.text_light, 'marginBottom': '20px', 'display': 'block'}
        table_style_hidden = {'display': 'none'}
    return [], table_style_hidden, message_text, message_style_visible, baseline_results, baseline_display_text

@app.callback(
    [Output('scl-spot-price-store', 'data'),
     Output('scl-spot-price-error-div', 'children')],
    [Input('scl-refresh-data-button', 'n_clicks')],
    prevent_initial_call=True
)
@monitor()
def scl_fetch_spot_price_callback(n_clicks):
    """Fetch spot price from Pricing Monkey"""
    if n_clicks is None or n_clicks == 0:
        raise PreventUpdate
    
    logger.info(f"Fetching spot price from Pricing Monkey (button clicks: {n_clicks})")
    
    try:
        spot_data, error_msg = scl_fetch_spot_price_from_pm()
        return spot_data, error_msg
    except Exception as e:
        error_msg = f"Unexpected error fetching spot price: {str(e)}"
        logger.error(error_msg)
        return {'decimal_price': None, 'special_string_price': None}, error_msg

# --- End Scenario Ladder Callbacks ---

# --- Actant EOD Helper Functions ---
def aeod_create_shock_amount_options(shock_values, shock_type=None):
    """
    Create formatted options for shock amount listbox.
    
    Args:
        shock_values: List of shock values
        shock_type: Type of shock for formatting, or None for mixed display
        
    Returns:
        List of option dictionaries with label and value
    """
    if not shock_values:
        return []
    
    options = []
    for value in shock_values:
        if shock_type:
            # Use specific formatting for known shock type
            label = format_shock_value_for_display(value, shock_type)
        else:
            # Mixed display - determine type based on value range
            # Percentage values are between -0.5 and 0.5 (excluding larger absolute values)
            # This handles the case where we have both percentage (-0.3 to 0.3) and absolute (-2.0 to 2.0)
            if -0.5 <= value <= 0.5:
                label = format_shock_value_for_display(value, "percentage")
            else:
                label = format_shock_value_for_display(value, "absolute_usd")
        
        options.append({"label": label, "value": value})
    
    return options

def aeod_create_density_aware_marks(shock_values, shock_type):
    """
    Create marks dictionary with mode-specific labeling strategies.
    
    Args:
        shock_values: List of shock values to create marks for
        shock_type: Type of shock for formatting
        
    Returns:
        Dictionary mapping shock values to label strings (empty string = no label)
    """
    if not shock_values:
        return {}
    
    marks = {}
    
    if shock_type == "absolute_usd":
        # Absolute mode: label everything (less cluttered by nature)
        for val in shock_values:
            marks[val] = format_shock_value_for_display(val, shock_type)
    
    elif shock_type == "percentage":
        # Percentage mode: surgical labeling strategy
        outer_threshold = 0.005  # ±0.5% boundary
        inner_targets = [-0.0025, 0.0, 0.0025]  # -0.25%, 0%, +0.25%
        tolerance = 0.0001  # Floating-point precision tolerance
        
        for val in shock_values:
            if abs(val) >= outer_threshold:
                # Sparse outer regions: show all labels
                marks[val] = format_shock_value_for_display(val, shock_type)
            else:
                # Dense inner region: only specific target values
                if any(abs(val - target) < tolerance for target in inner_targets):
                    marks[val] = format_shock_value_for_display(val, shock_type)
                else:
                    marks[val] = ""  # Tick exists but no label
    
    return marks
def aeod_create_tooltip_config(shock_type):
    """
    Create tooltip configuration that matches label formatting.
    
    Args:
        shock_type: Type of shock for formatting
        
    Returns:
        Dictionary with tooltip configuration
    """
    if shock_type == "percentage":
        # For percentage mode, use a basic tooltip configuration
        return {
            "placement": "bottom",
            "always_visible": False,
            "template": "{value:.1%}"  # Try percentage format
        }
    else:  # absolute_usd
        # For absolute mode, use currency format
        return {
            "placement": "bottom",
            "always_visible": False,
            "template": "${value:.2f}"  # Try currency format
        }

def aeod_get_data_service():
    """Get or create ActantDataService instance"""
    if not hasattr(aeod_get_data_service, '_instance'):
        aeod_get_data_service._instance = ActantDataService()
    return aeod_get_data_service._instance

def aeod_get_toggle_state_from_buttons(ctx, button_id_false, button_id_true, default_false=True):
    """Extract toggle state from button clicks using callback context."""
    if not ctx.triggered:
        return default_false
    
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if triggered_id == button_id_true:
        return True
    elif triggered_id == button_id_false:
        return False
    else:
        return default_false

def aeod_get_global_shock_range_for_metric(selected_scenarios, shock_type):
    """Calculate global shock range across all selected scenarios for a given shock type."""
    data_service = aeod_get_data_service()
    global_min = float('inf')
    global_max = float('-inf')
    
    for scenario in selected_scenarios:
        min_shock, max_shock = data_service.get_shock_range_by_scenario(scenario, shock_type)
        global_min = min(global_min, min_shock)
        global_max = max(global_max, max_shock)
    
    return global_min, global_max

def aeod_get_global_shock_values_for_metric(selected_scenarios, shock_type):
    """Get unique shock values across all selected scenarios for consistent tick marks."""
    data_service = aeod_get_data_service()
    all_shock_values = set()
    
    for scenario in selected_scenarios:
        scenario_shock_values = data_service.get_distinct_shock_values_by_scenario_and_type(scenario, shock_type)
        all_shock_values.update(scenario_shock_values)
    
    return sorted(list(all_shock_values))

def aeod_create_scenario_view_grid(selected_scenarios, selected_metrics, is_table_view, is_percentage):
    """Create scenario-based visualization grid (each scenario = one graph)."""
    # Calculate grid layout
    num_scenarios = len(selected_scenarios)
    if num_scenarios == 1:
        columns = 1
    elif num_scenarios <= 4:
        columns = 2
    else:
        columns = 3
    
    grid_children = []
    
    # Determine shock type based on percentage toggle
    shock_type = "percentage" if is_percentage else "absolute_usd"
    
    # Get data service
    data_service = aeod_get_data_service()
    
    for i, scenario in enumerate(selected_scenarios):
        # Get shock range for this scenario with specific shock type
        min_shock, max_shock = data_service.get_shock_range_by_scenario(scenario, shock_type)
        
        # Get distinct shock values for tick marks
        shock_values = data_service.get_distinct_shock_values_by_scenario_and_type(scenario, shock_type)
        
        # Create marks dictionary for range slider
        if shock_values:
            marks = aeod_create_density_aware_marks(shock_values, shock_type)
        else:
            marks = None
        
        # Create visualization container for this scenario
        scenario_container = Container(
            id=f"aeod-scenario-container-{scenario.replace(' ', '-').replace('.', '-')}",
            children=[
                html.H5(
                    f"Scenario: {scenario}",
                    style={
                        "color": default_theme.text_light,
                        "textAlign": "center",
                        "marginBottom": "15px",
                        "fontSize": "16px",
                        "fontWeight": "500"
                    }
                ),
                
                # Range slider for this scenario
                html.Div([
                    html.P("Shock Range:", style={
                        "color": default_theme.text_light,
                        "marginBottom": "5px",
                        "fontSize": "14px"
                    }),
                    RangeSlider(
                        id={"type": "aeod-range-slider", "scenario": scenario},
                        min=min_shock,
                        max=max_shock,
                        value=[min_shock, max_shock],
                        marks=marks,
                        tooltip=aeod_create_tooltip_config(shock_type),
                        theme=default_theme
                    ).render()
                ], style={"marginBottom": "15px"}),
                
                # Visualization area (graph or table)
                html.Div(
                    id=f"aeod-viz-container-{scenario.replace(' ', '-').replace('.', '-')}",
                    children=[
                        Graph(
                            id={"type": "aeod-scenario-graph", "scenario": scenario},
                            figure={
                                'data': [],
                                'layout': go.Layout(
                                    title=f"Metrics for {scenario}",
                                    xaxis_title="Shock Value",
                                    yaxis_title="Metric Value",
                                    plot_bgcolor=default_theme.base_bg,
                                    paper_bgcolor=default_theme.panel_bg,
                                    font_color=default_theme.text_light,
                                    height=400
                                )
                            },
                            theme=default_theme,
                            style={"height": "400px", "display": "block" if not is_table_view else "none"}
                        ).render(),
                        html.Div([
                            DataTable(
                                id={"type": "aeod-scenario-table", "scenario": scenario},
                                data=[],
                                columns=[],
                                theme=default_theme,
                                page_size=10,
                                style_table={"height": "400px", "overflowY": "auto"}
                            ).render()
                        ], id={"type": "aeod-scenario-table-container", "scenario": scenario}, 
                           style={"display": "none" if not is_table_view else "block"})
                    ]
                )
            ],
            style={
                "backgroundColor": default_theme.panel_bg,
                "padding": "15px",
                "borderRadius": "5px",
                "marginBottom": "20px"
            }
        )
        
        # Calculate column width based on number of scenarios
        width = 12 // columns if num_scenarios % columns == 0 else 12 // columns
        if i == num_scenarios - 1 and num_scenarios % columns != 0:
            width = 12 - (num_scenarios - 1) * (12 // columns)
        
        grid_children.append((scenario_container, {"width": width}))
    
    return Grid(id="aeod-visualization-grid", children=grid_children).render()

def aeod_create_metric_view_grid(selected_scenarios, selected_metrics, is_table_view, is_percentage):
    """Create metric-based visualization grid (each metric = one graph)."""
    # Calculate grid layout
    num_metrics = len(selected_metrics)
    if num_metrics == 1:
        columns = 1
    elif num_metrics <= 4:
        columns = 2
    else:
        columns = 3
    
    grid_children = []
    
    # Determine shock type based on percentage toggle
    shock_type = "percentage" if is_percentage else "absolute_usd"
    
    for i, metric in enumerate(selected_metrics):
        # Calculate global shock range across all selected scenarios for this metric
        min_shock, max_shock = aeod_get_global_shock_range_for_metric(selected_scenarios, shock_type)
        
        # Get global shock values across all scenarios for consistent tick marks
        global_shock_values = aeod_get_global_shock_values_for_metric(selected_scenarios, shock_type)
        
        # Create marks dictionary for range slider
        if global_shock_values:
            marks = aeod_create_density_aware_marks(global_shock_values, shock_type)
        else:
            marks = None
        
        # Create visualization container for this metric
        metric_container = Container(
            id=f"aeod-metric-container-{metric.replace(' ', '-').replace('.', '-')}",
            children=[
                html.H5(
                    f"Metric: {metric}",
                    style={
                        "color": default_theme.text_light,
                        "textAlign": "center",
                        "marginBottom": "15px",
                        "fontSize": "16px",
                        "fontWeight": "500"
                    }
                ),
                
                # Range slider for this metric (global range)
                html.Div([
                    html.P("Shock Range:", style={
                        "color": default_theme.text_light,
                        "marginBottom": "5px",
                        "fontSize": "14px"
                    }),
                    RangeSlider(
                        id={"type": "aeod-metric-range-slider", "metric": metric},
                        min=min_shock,
                        max=max_shock,
                        value=[min_shock, max_shock],
                        marks=marks,
                        tooltip=aeod_create_tooltip_config(shock_type),
                        theme=default_theme
                    ).render()
                ], style={"marginBottom": "15px"}),
                
                # Visualization area (graph or table)
                html.Div(
                    id=f"aeod-metric-viz-container-{metric.replace(' ', '-').replace('.', '-')}",
                    children=[
                        Graph(
                            id={"type": "aeod-metric-graph", "metric": metric},
                            figure={
                                'data': [],
                                'layout': go.Layout(
                                    title=f"Scenarios for {metric}",
                                    xaxis_title="Shock Value",
                                    yaxis_title="Metric Value",
                                    plot_bgcolor=default_theme.base_bg,
                                    paper_bgcolor=default_theme.panel_bg,
                                    font_color=default_theme.text_light,
                                    height=400
                                )
                            },
                            theme=default_theme,
                            style={"height": "400px", "display": "block" if not is_table_view else "none"}
                        ).render(),
                        html.Div([
                            DataTable(
                                id={"type": "aeod-metric-table", "metric": metric},
                                data=[],
                                columns=[],
                                theme=default_theme,
                                page_size=10,
                                style_table={"height": "400px", "overflowY": "auto"}
                            ).render()
                        ], id={"type": "aeod-metric-table-container", "metric": metric},
                           style={"display": "none" if not is_table_view else "block"})
                    ]
                )
            ],
            style={
                "backgroundColor": default_theme.panel_bg,
                "padding": "15px",
                "borderRadius": "5px",
                "marginBottom": "20px"
            }
        )
        
        # Calculate column width based on number of metrics
        width = 12 // columns if num_metrics % columns == 0 else 12 // columns
        if i == num_metrics - 1 and num_metrics % columns != 0:
            width = 12 - (num_metrics - 1) * (12 // columns)
        
        grid_children.append((metric_container, {"width": width}))
    
    return Grid(id="aeod-metric-visualization-grid", children=grid_children).render()

def aeod_create_dashboard_layout():
    """Create the main dashboard layout with complete Actant EOD functionality."""
    return Container(
        id="aeod-main-layout",
        children=[
            # Title Section
            html.Div([
                html.H1(
                    "Actant EOD Dashboard", 
                    style={
                        "textAlign": "center", 
                        "color": default_theme.primary, 
                        "marginBottom": "10px",
                        "fontSize": "2.5em",
                        "fontWeight": "600"
                    }
                ),
                # Load data section
                Container(
                    id="aeod-load-data-container",
                    children=[
                        html.Div([
                            Button(
                                id="aeod-load-data-button",
                                label="Load Latest Actant Data",
                                theme=default_theme,
                                style={"marginRight": "10px"}
                            ).render(),
                            Button(
                                id="aeod-load-pm-button", 
                                label="Load PM Data",
                                theme=default_theme,
                                style={"marginRight": "20px"}
                            ).render(),
                            html.Div(
                                id="aeod-current-file-display",
                                children="No data loaded",
                                style={
                                    "color": default_theme.text_light,
                                    "fontSize": "14px",
                                    "display": "inline-block",
                                    "verticalAlign": "middle"
                                }
                            )
                        ], style={
                            "display": "flex",
                            "alignItems": "center",
                            "justifyContent": "center",
                            "marginBottom": "20px"
                        })
                    ],
                    style={
                        "backgroundColor": default_theme.panel_bg,
                        "padding": "15px",
                        "borderRadius": "5px",
                        "marginBottom": "20px"
                    }
                ).render()
            ]),
            
            # Top Controls Grid
            html.Div(
                id="aeod-controls-section",
                children=[
                    Grid(
                        id="aeod-controls-grid",
                        children=[
                            # Scenarios Column
                            (Container(
                                id="aeod-scenarios-container",
                                children=[
                                    html.H4("Scenarios", style={
                                        "color": default_theme.text_light,
                                        "marginBottom": "10px",
                                        "fontSize": "16px",
                                        "fontWeight": "500"
                                    }),
                                    ListBox(
                                        id="aeod-scenario-listbox",
                                        options=[],
                                        value=[],
                                        multi=True,
                                        theme=default_theme,
                                        style={"height": "200px"}
                                    ).render()
                                ],
                                style={
                                    "backgroundColor": default_theme.panel_bg,
                                    "padding": "15px",
                                    "borderRadius": "5px"
                                }
                            ), {"width": 3}),
                            
                            # Metric Categories Column
                            (Container(
                                id="aeod-categories-container",
                                children=[
                                    html.H4("Metric Categories", style={
                                        "color": default_theme.text_light,
                                        "marginBottom": "10px",
                                        "fontSize": "16px",
                                        "fontWeight": "500"
                                    }),
                                    html.Div(id="aeod-metric-categories-container")
                                ],
                                style={
                                    "backgroundColor": default_theme.panel_bg,
                                    "padding": "15px",
                                    "borderRadius": "5px"
                                }
                            ), {"width": 4}),
                            
                            # Filters Column
                            (Container(
                                id="aeod-filters-container",
                                children=[
                                    html.H4("Filters", style={
                                        "color": default_theme.text_light,
                                        "marginBottom": "10px",
                                        "fontSize": "16px",
                                        "fontWeight": "500"
                                    }),
                                    html.P("Prefix Filter:", style={
                                        "color": default_theme.text_light,
                                        "marginBottom": "5px",
                                        "fontSize": "14px"
                                    }),
                                    ListBox(
                                        id="aeod-prefix-filter-listbox",
                                        options=[
                                            {"label": "All", "value": "all"},
                                            {"label": "Base (no prefix)", "value": "base"},
                                            {"label": "AB prefixed", "value": "ab"},
                                            {"label": "BS prefixed", "value": "bs"},
                                            {"label": "PA prefixed", "value": "pa"}
                                        ],
                                        value="all",
                                        multi=False,
                                        theme=default_theme,
                                        style={"height": "120px"}
                                    ).render()
                                ],
                                style={
                                    "backgroundColor": default_theme.panel_bg,
                                    "padding": "15px",
                                    "borderRadius": "5px"
                                }
                            ), {"width": 2}),
                            
                            # View Options Column
                            (Container(
                                id="aeod-toggles-container",
                                children=[
                                    html.H4("View Options", style={
                                        "color": default_theme.text_light,
                                        "marginBottom": "15px",
                                        "fontSize": "16px",
                                        "fontWeight": "500"
                                    }),
                                    
                                    # Vertical stack of button pairs
                                    html.Div([
                                        # Graph/Table toggle
                                        html.Div([
                                            html.P("View:", style={
                                                "color": default_theme.text_light, 
                                                "marginBottom": "5px", 
                                                "fontSize": "14px",
                                                "textAlign": "center"
                                            }),
                                            html.Div([
                                                Button(
                                                    id="aeod-view-mode-graph-btn",
                                                    label="Graph",
                                                    theme=default_theme,
                                                    n_clicks=1,  # Default selected
                                                    style={
                                                        'borderTopRightRadius': '0',
                                                        'borderBottomRightRadius': '0',
                                                        'borderRight': 'none',
                                                        'backgroundColor': default_theme.primary
                                                    }
                                                ).render(),
                                                Button(
                                                    id="aeod-view-mode-table-btn",
                                                    label="Table",
                                                    theme=default_theme,
                                                    n_clicks=0,
                                                    style={
                                                        'borderTopLeftRadius': '0',
                                                        'borderBottomLeftRadius': '0',
                                                        'backgroundColor': default_theme.panel_bg
                                                    }
                                                ).render()
                                            ], style={"display": "flex", "justifyContent": "center"})
                                        ], style={"textAlign": "center", "marginBottom": "15px"}),
                                        
                                        # Absolute/Percentage toggle
                                        html.Div([
                                            html.P("Values:", style={
                                                "color": default_theme.text_light, 
                                                "marginBottom": "5px", 
                                                "fontSize": "14px",
                                                "textAlign": "center"
                                            }),
                                            html.Div([
                                                Button(
                                                    id="aeod-percentage-absolute-btn",
                                                    label="Absolute",
                                                    theme=default_theme,
                                                    n_clicks=1,  # Default selected
                                                    style={
                                                        'borderTopRightRadius': '0',
                                                        'borderBottomRightRadius': '0',
                                                        'borderRight': 'none',
                                                        'backgroundColor': default_theme.primary
                                                    }
                                                ).render(),
                                                Button(
                                                    id="aeod-percentage-percentage-btn",
                                                    label="Percentage",
                                                    theme=default_theme,
                                                    n_clicks=0,
                                                    style={
                                                        'borderTopLeftRadius': '0',
                                                        'borderBottomLeftRadius': '0',
                                                        'backgroundColor': default_theme.panel_bg
                                                    }
                                                ).render()
                                            ], style={"display": "flex", "justifyContent": "center"})
                                        ], style={"textAlign": "center", "marginBottom": "15px"}),
                                        
                                        # Scenario/Metric View toggle
                                        html.Div([
                                            html.P("Mode:", style={
                                                "color": default_theme.text_light, 
                                                "marginBottom": "5px", 
                                                "fontSize": "14px",
                                                "textAlign": "center"
                                            }),
                                            html.Div([
                                                Button(
                                                    id="aeod-viz-mode-scenario-btn",
                                                    label="Scenario",
                                                    theme=default_theme,
                                                    n_clicks=1,  # Default selected
                                                    style={
                                                        'borderTopRightRadius': '0',
                                                        'borderBottomRightRadius': '0',
                                                        'borderRight': 'none',
                                                        'backgroundColor': default_theme.primary
                                                    }
                                                ).render(),
                                                Button(
                                                    id="aeod-viz-mode-metric-btn",
                                                    label="Metric",
                                                    theme=default_theme,
                                                    n_clicks=0,
                                                    style={
                                                        'borderTopLeftRadius': '0',
                                                        'borderBottomLeftRadius': '0',
                                                        'backgroundColor': default_theme.panel_bg
                                                    }
                                                ).render()
                                            ], style={"display": "flex", "justifyContent": "center"})
                                        ], style={"textAlign": "center"})
                                        
                                    ], style={
                                        "display": "flex",
                                        "flexDirection": "column",
                                        "alignItems": "center"
                                    })
                                ],
                                style={
                                    "backgroundColor": default_theme.panel_bg,
                                    "padding": "15px",
                                    "borderRadius": "5px"
                                }
                            ), {"width": 3})
                        ]
                    ).render()
                ],
                style={"marginBottom": "20px"}
            ),
            
            # Bottom Visualization Grid
            html.Div(
                id="aeod-visualization-section",
                children=[
                    html.Div(id="aeod-dynamic-visualization-grid")
                ]
            ),
            
            # Data stores
            dcc.Store(id="aeod-data-loaded-store", data=False),
            dcc.Store(id="aeod-pm-data-loaded-store", data=False),
            dcc.Store(id="aeod-metric-categories-store", data={}),
            dcc.Store(id="aeod-selected-metrics-store", data=[]),
            dcc.Store(id="aeod-shock-ranges-store", data={}),
            dcc.Store(id="aeod-toggle-states-store", data={
                "is_table_view": False,
                "is_percentage": False,
                "is_metric_view": False
            })
        ],
        theme=default_theme,
        style={"padding": "20px", "backgroundColor": default_theme.base_bg, "minHeight": "100vh"}
    ).render()

# --- End Actant EOD Helper Functions ---

# --- Actant EOD Callbacks ---
@app.callback(
    [Output("aeod-current-file-display", "children"),
     Output("aeod-data-loaded-store", "data"),
     Output("aeod-scenario-listbox", "options"),
     Output("aeod-metric-categories-store", "data")],
    Input("aeod-load-data-button", "n_clicks"),
    prevent_initial_call=False
)
@monitor()
def aeod_load_data(n_clicks):
    """Load the most recent JSON file and populate filter options."""
    try:
        data_service = aeod_get_data_service()
        json_file = get_most_recent_json_file()
        
        if json_file is None:
            return "No valid JSON files found", False, [], {}
        
        success = data_service.load_data_from_json(json_file)
        
        if not success:
            return f"Failed to load {json_file.name}", False, [], {}
        
        # Get metadata for display
        metadata = get_json_file_metadata(json_file)
        file_display = (
            f"Loaded: {metadata['filename']} "
            f"({metadata['size_mb']:.1f} MB, {metadata['scenario_count']} scenarios)"
        )
        
        # Get filter options
        scenarios = data_service.get_scenario_headers()
        scenario_options = [{"label": s, "value": s} for s in scenarios]
        
        # Get categorized metrics
        metric_categories = data_service.categorize_metrics()
        
        logger.info(f"Successfully loaded Actant EOD data from {json_file.name}")
        return file_display, True, scenario_options, metric_categories
        
    except Exception as e:
        logger.error(f"Error loading Actant EOD data: {e}")
        return f"Error loading data: {str(e)}", False, [], {}

@app.callback(
    [Output("aeod-current-file-display", "children", allow_duplicate=True),
     Output("aeod-pm-data-loaded-store", "data")],
    Input("aeod-load-pm-button", "n_clicks"),
    prevent_initial_call=True
)
@monitor()
def aeod_load_pm_data(n_clicks):
    """Load PM data for Actant EOD"""
    try:
        logger.info("Actant EOD PM data loading initiated")
        # Placeholder for PM data loading logic
        file_display = "PM Data loaded successfully for Actant EOD"
        return file_display, True
    except Exception as e:
        logger.error(f"Error loading Actant EOD PM data: {e}")
        return f"Error loading PM data: {str(e)}", False

@app.callback(
    Output("aeod-toggle-states-store", "data"),
    [Input("aeod-view-mode-graph-btn", "n_clicks"),
     Input("aeod-view-mode-table-btn", "n_clicks"),
     Input("aeod-percentage-absolute-btn", "n_clicks"),
     Input("aeod-percentage-percentage-btn", "n_clicks"),
     Input("aeod-viz-mode-scenario-btn", "n_clicks"),
     Input("aeod-viz-mode-metric-btn", "n_clicks")],
    State("aeod-toggle-states-store", "data"),
    prevent_initial_call=False
)
@monitor()
def aeod_update_toggle_states_store(graph_btn, table_btn, abs_btn, pct_btn, scenario_btn, metric_btn, current_states):
    """Update toggle states store for Actant EOD dashboard"""
    if current_states is None:
        current_states = {
            "is_table_view": False,
            "is_percentage": False,
            "is_metric_view": False
        }
    
    ctx = dash.callback_context
    if not ctx.triggered:
        return current_states
    
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    new_states = current_states.copy()
    
    # Handle view mode toggle (graph/table)
    if triggered_id == "aeod-view-mode-table-btn":
        new_states["is_table_view"] = True
    elif triggered_id == "aeod-view-mode-graph-btn":
        new_states["is_table_view"] = False
    
    # Handle percentage/absolute toggle
    elif triggered_id == "aeod-percentage-percentage-btn":
        new_states["is_percentage"] = True
    elif triggered_id == "aeod-percentage-absolute-btn":
        new_states["is_percentage"] = False
    
    # Handle visualization mode toggle (scenario/metric)
    elif triggered_id == "aeod-viz-mode-metric-btn":
        new_states["is_metric_view"] = True
    elif triggered_id == "aeod-viz-mode-scenario-btn":
        new_states["is_metric_view"] = False
    
    logger.info(f"Actant EOD toggle states updated: {new_states}")
    return new_states

@app.callback(
    Output("aeod-dynamic-visualization-grid", "children"),
    [Input("aeod-scenario-listbox", "value"),
     Input("aeod-selected-metrics-store", "data"),
     Input("aeod-toggle-states-store", "data")],
    State("aeod-data-loaded-store", "data"),
    prevent_initial_call=True
)
@monitor()
def aeod_create_dynamic_visualization_grid(selected_scenarios, selected_metrics, toggle_states, data_loaded):
    """Create dynamic visualization grid based on current selections and toggle states."""
    if not data_loaded:
        return html.Div(
            "Please load data first using the 'Load Latest Actant Data' button.",
            style={
                "textAlign": "center",
                "color": default_theme.text_light,
                "padding": "50px",
                "fontSize": "16px"
            }
        )
    
    if not selected_scenarios:
        return html.Div(
            "Please select one or more scenarios to visualize.",
            style={
                "textAlign": "center",
                "color": default_theme.text_light,
                "padding": "50px",
                "fontSize": "16px"
            }
        )
    
    if not selected_metrics:
        return html.Div(
            "Please select one or more metrics to visualize.",
            style={
                "textAlign": "center", 
                "color": default_theme.text_light,
                "padding": "50px",
                "fontSize": "16px"
            }
        )
    
    try:
        # Extract toggle states
        is_table_view = toggle_states.get("is_table_view", False)
        is_percentage = toggle_states.get("is_percentage", False) 
        is_metric_view = toggle_states.get("is_metric_view", False)
        
        # Create appropriate visualization grid based on view mode
        if is_metric_view:
            # Metric view: each metric gets its own visualization
            return aeod_create_metric_view_grid(selected_scenarios, selected_metrics, is_table_view, is_percentage)
        else:
            # Scenario view: each scenario gets its own visualization  
            return aeod_create_scenario_view_grid(selected_scenarios, selected_metrics, is_table_view, is_percentage)
            
    except Exception as e:
        logger.error(f"Error creating Actant EOD visualization grid: {e}")
        return html.Div(
            f"Error creating visualization: {str(e)}",
            style={
                "textAlign": "center",
                "color": default_theme.error if hasattr(default_theme, 'error') else "#ff6b6b",
                "padding": "50px",
                "fontSize": "16px"
            }
        )

# --- End Actant EOD Callbacks ---

@app.callback(
    Output("aeod-metric-categories-container", "children"),
    [Input("aeod-metric-categories-store", "data"),
     Input("aeod-prefix-filter-listbox", "value")],
    prevent_initial_call=True
)
@monitor()
def aeod_update_metric_categories(metric_categories, prefix_filter):
    """Create metric category checkboxes and listboxes."""
    if not metric_categories:
        return html.Div("No metrics available", style={"color": default_theme.text_light})
    
    # Get data service for prefix filtering
    data_service = aeod_get_data_service()
    
    # Define all expected categories in order
    all_categories = ["Delta", "Epsilon", "Gamma", "Theta", "Vega", "Zeta", "Vol", "OEV", "Th PnL", "Misc"]
    category_components = []
    
    for category in all_categories:
        # Get metrics for this category (empty list if category doesn't exist)
        metrics = metric_categories.get(category, [])
        
        # Filter metrics by prefix
        filtered_metrics = data_service.filter_metrics_by_prefix(metrics, prefix_filter)
        
        # Determine if category should be disabled
        is_disabled = len(filtered_metrics) == 0
        
        # Create options for the listbox
        metric_options = [{"label": m, "value": m} for m in filtered_metrics]
        
        # Style for disabled categories
        checkbox_style = {"marginBottom": "5px"}
        if is_disabled:
            checkbox_style["opacity"] = "0.5"
        
        category_div = html.Div([
            # Category checkbox
            Checkbox(
                id=f"aeod-category-{category.lower().replace(' ', '-')}-checkbox",
                options=[{"label": f"{category} ({len(filtered_metrics)} metrics)", "value": category}],
                value=[],
                theme=default_theme,
                style=checkbox_style
            ).render(),
            
            # Metrics listbox (initially collapsed)
            html.Div([
                ListBox(
                    id=f"aeod-category-{category.lower().replace(' ', '-')}-listbox",
                    options=metric_options if not is_disabled else [{"label": "No metrics available", "value": "", "disabled": True}],
                    value=[],
                    multi=True,
                    theme=default_theme,
                    style={
                        "height": "100px", 
                        "fontSize": "12px",
                        "opacity": "0.5" if is_disabled else "1.0",
                        "pointerEvents": "none" if is_disabled else "auto"
                    }
                ).render()
            ], id=f"aeod-category-{category.lower().replace(' ', '-')}-container",
               style={"display": "none", "marginLeft": "20px", "marginBottom": "10px"})
        ], style={"marginBottom": "5px"})
        
        category_components.append(category_div)
    
    return category_components

@app.callback(
    [Output("aeod-category-delta-container", "style", allow_duplicate=True),
     Output("aeod-category-epsilon-container", "style", allow_duplicate=True),
     Output("aeod-category-gamma-container", "style", allow_duplicate=True),
     Output("aeod-category-theta-container", "style", allow_duplicate=True),
     Output("aeod-category-vega-container", "style", allow_duplicate=True),
     Output("aeod-category-zeta-container", "style", allow_duplicate=True),
     Output("aeod-category-vol-container", "style", allow_duplicate=True),
     Output("aeod-category-oev-container", "style", allow_duplicate=True),
     Output("aeod-category-th-pnl-container", "style", allow_duplicate=True),
     Output("aeod-category-misc-container", "style", allow_duplicate=True)],
    [Input("aeod-category-delta-checkbox", "value"),
     Input("aeod-category-epsilon-checkbox", "value"),
     Input("aeod-category-gamma-checkbox", "value"),
     Input("aeod-category-theta-checkbox", "value"),
     Input("aeod-category-vega-checkbox", "value"),
     Input("aeod-category-zeta-checkbox", "value"),
     Input("aeod-category-vol-checkbox", "value"),
     Input("aeod-category-oev-checkbox", "value"),
     Input("aeod-category-th-pnl-checkbox", "value"),
     Input("aeod-category-misc-checkbox", "value")],
    prevent_initial_call=True
)
@monitor()
def aeod_toggle_category_visibility(*checkbox_values):
    """Toggle visibility of metric listboxes based on checkbox state."""
    styles = []
    
    for value in checkbox_values:
        if value:  # Checkbox is checked
            styles.append({"display": "block", "marginLeft": "20px", "marginBottom": "10px"})
        else:  # Checkbox is unchecked
            styles.append({"display": "none", "marginLeft": "20px", "marginBottom": "10px"})
    
    return styles

@app.callback(
    Output("aeod-selected-metrics-store", "data"),
    [Input("aeod-category-delta-listbox", "value"),
     Input("aeod-category-epsilon-listbox", "value"),
     Input("aeod-category-gamma-listbox", "value"),
     Input("aeod-category-theta-listbox", "value"),
     Input("aeod-category-vega-listbox", "value"),
     Input("aeod-category-zeta-listbox", "value"),
     Input("aeod-category-vol-listbox", "value"),
     Input("aeod-category-oev-listbox", "value"),
     Input("aeod-category-th-pnl-listbox", "value"),
     Input("aeod-category-misc-listbox", "value"),
     Input("aeod-category-delta-checkbox", "value"),
     Input("aeod-category-epsilon-checkbox", "value"),
     Input("aeod-category-gamma-checkbox", "value"),
     Input("aeod-category-theta-checkbox", "value"),
     Input("aeod-category-vega-checkbox", "value"),
     Input("aeod-category-zeta-checkbox", "value"),
     Input("aeod-category-vol-checkbox", "value"),
     Input("aeod-category-oev-checkbox", "value"),
     Input("aeod-category-th-pnl-checkbox", "value"),
     Input("aeod-category-misc-checkbox", "value")],
    prevent_initial_call=True
)
@monitor()
def aeod_collect_selected_metrics(*inputs):
    """Collect selected metrics from category listboxes, but only if the category checkbox is checked."""
    # Split inputs into listbox values and checkbox states
    num_categories = 10
    listbox_values = inputs[:num_categories]
    checkbox_values = inputs[num_categories:]
    
    all_selected_metrics = []
    
    for metrics, checkbox_state in zip(listbox_values, checkbox_values):
        # Only include metrics if the category checkbox is checked AND metrics are selected
        if checkbox_state and metrics:  # checkbox_state is truthy (checked) and metrics exist
            all_selected_metrics.extend(metrics)
    
    return all_selected_metrics

# --- End Actant EOD Callbacks ---

# MATCH Pattern Callbacks for Dynamic Visualizations
@app.callback(
    Output({"type": "aeod-scenario-graph", "scenario": MATCH}, "figure"),
    [Input("aeod-selected-metrics-store", "data"),
     Input("aeod-toggle-states-store", "data"),
     Input({"type": "aeod-range-slider", "scenario": MATCH}, "value")],
    State({"type": "aeod-scenario-graph", "scenario": MATCH}, "id"),
    State("aeod-data-loaded-store", "data"),
    prevent_initial_call=False
)
@monitor()
def aeod_update_scenario_graph(selected_metrics, toggle_states, range_values, graph_id, data_loaded):
    """Update graph for a specific scenario based on selected metrics and range."""
    if not data_loaded or not selected_metrics or not range_values:
        return {
            'data': [],
            'layout': go.Layout(
                title="Select metrics to visualize",
                xaxis_title="Shock Value",
                yaxis_title="Metric Value",
                plot_bgcolor=default_theme.base_bg,
                paper_bgcolor=default_theme.panel_bg,
                font_color=default_theme.text_light,
                height=400
            )
        }
    
    try:
        scenario = graph_id["scenario"]
        is_percentage = toggle_states.get("is_percentage", False)
        
        # Determine shock type based on percentage toggle
        shock_type = "percentage" if is_percentage else "absolute_usd"
        
        # Get data service
        data_service = aeod_get_data_service()
        
        # Get filtered data for this scenario within the range
        shock_ranges = {scenario: range_values}
        df = data_service.get_filtered_data_with_range(
            scenario_headers=[scenario],
            shock_types=[shock_type],
            shock_ranges=shock_ranges,
            metrics=selected_metrics
        )
        
        if df.empty:
            return {
                'data': [],
                'layout': go.Layout(
                    title=f"No data for {scenario}",
                    xaxis_title="Shock Value", 
                    yaxis_title="Metric Value",
                    plot_bgcolor=default_theme.base_bg,
                    paper_bgcolor=default_theme.panel_bg,
                    font_color=default_theme.text_light,
                    height=400
                )
            }
        
        fig = go.Figure()
        colors = px.colors.qualitative.Set1
        
        for i, metric in enumerate(selected_metrics):
            if metric in df.columns:
                fig.add_trace(go.Scatter(
                    x=df['shock_value'],
                    y=df[metric],
                    mode='lines+markers',
                    name=metric,
                    line=dict(color=colors[i % len(colors)]),
                    marker=dict(size=6)
                ))
        
        fig.update_layout(
            title=f"Metrics for {scenario}",
            xaxis_title="Shock Value",
            yaxis_title="Metric Value",
            plot_bgcolor=default_theme.base_bg,
            paper_bgcolor=default_theme.panel_bg,
            font_color=default_theme.text_light,
            xaxis=dict(
                showgrid=True, 
                gridcolor=default_theme.secondary,
            ),
            yaxis=dict(showgrid=True, gridcolor=default_theme.secondary),
            height=400,
            margin=dict(l=60, r=20, t=60, b=50),
            legend=dict(
                bgcolor=default_theme.panel_bg,
                bordercolor=default_theme.secondary,
                borderwidth=1
            )
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Error updating scenario graph: {e}")
        return {
            'data': [],
            'layout': go.Layout(
                title=f"Error: {str(e)}",
                plot_bgcolor=default_theme.base_bg,
                paper_bgcolor=default_theme.panel_bg,
                font_color=default_theme.text_light,
                height=400
            )
        }

@app.callback(
    [Output({"type": "aeod-scenario-table", "scenario": MATCH}, "data"),
     Output({"type": "aeod-scenario-table", "scenario": MATCH}, "columns")],
    [Input("aeod-selected-metrics-store", "data"),
     Input("aeod-toggle-states-store", "data"),
     Input({"type": "aeod-range-slider", "scenario": MATCH}, "value")],
    State({"type": "aeod-scenario-table", "scenario": MATCH}, "id"),
    State("aeod-data-loaded-store", "data"),
    prevent_initial_call=False
)
@monitor()
def aeod_update_scenario_table(selected_metrics, toggle_states, range_values, table_id, data_loaded):
    """Update table for a specific scenario based on selected metrics and range."""
    if not data_loaded or not selected_metrics or not range_values:
        return [], []
    
    try:
        scenario = table_id["scenario"]
        is_percentage = toggle_states.get("is_percentage", False)
        
        # Determine shock type based on percentage toggle
        shock_type = "percentage" if is_percentage else "absolute_usd"
        
        # Get data service
        data_service = aeod_get_data_service()
        
        # Get filtered data for this scenario within the range
        shock_ranges = {scenario: range_values}
        df = data_service.get_filtered_data_with_range(
            scenario_headers=[scenario],
            shock_types=[shock_type],
            shock_ranges=shock_ranges,
            metrics=selected_metrics
        )
        
        if df.empty:
            return [], []
        
        # Select relevant columns for display
        display_columns = ['shock_value'] + selected_metrics
        display_df = df[display_columns].copy()
        
        # Apply shock value formatting based on percentage toggle
        if is_percentage:
            display_df['shock_value'] = display_df['shock_value'].apply(
                lambda x: format_shock_value_for_display(x, "percentage")
            )
        else:
            display_df['shock_value'] = display_df['shock_value'].apply(
                lambda x: format_shock_value_for_display(x, "absolute_usd")
            )
        
        # Create columns configuration
        columns = []
        for col in display_df.columns:
            column_config = {"name": col, "id": col}
            
            # Format numeric columns
            if display_df[col].dtype in ['float64', 'int64']:
                column_config["type"] = "numeric"
                column_config["format"] = {"specifier": ",.4f"}
            
            columns.append(column_config)
        
        return display_df.to_dict('records'), columns
        
    except Exception as e:
        logger.error(f"Error updating scenario table: {e}")
        return [], []

@app.callback(
    Output({"type": "aeod-metric-graph", "metric": MATCH}, "figure"),
    [Input("aeod-scenario-listbox", "value"),
     Input("aeod-toggle-states-store", "data"),
     Input({"type": "aeod-metric-range-slider", "metric": MATCH}, "value")],
    State({"type": "aeod-metric-graph", "metric": MATCH}, "id"),
    State("aeod-data-loaded-store", "data"),
    prevent_initial_call=False
)
@monitor()
def aeod_update_metric_graph(selected_scenarios, toggle_states, range_values, graph_id, data_loaded):
    """Update graph for a specific metric based on selected scenarios and range."""
    if not data_loaded or not selected_scenarios or not range_values:
        return {
            'data': [],
            'layout': go.Layout(
                title="Select scenarios to visualize",
                xaxis_title="Shock Value",
                yaxis_title="Metric Value",
                plot_bgcolor=default_theme.base_bg,
                paper_bgcolor=default_theme.panel_bg,
                font_color=default_theme.text_light,
                height=400
            )
        }
    
    try:
        metric = graph_id["metric"]
        is_percentage = toggle_states.get("is_percentage", False)
        
        # Determine shock type based on percentage toggle
        shock_type = "percentage" if is_percentage else "absolute_usd"
        
        # Get data service
        data_service = aeod_get_data_service()
        
        # Create global shock range for this metric across all scenarios
        global_shock_ranges = {}
        for scenario in selected_scenarios:
            global_shock_ranges[scenario] = range_values  # Same range for all scenarios
        
        # Get filtered data for all scenarios within the range
        df = data_service.get_filtered_data_with_range(
            scenario_headers=selected_scenarios,
            shock_types=[shock_type],
            shock_ranges=global_shock_ranges,
            metrics=[metric]
        )
        
        if df.empty:
            return {
                'data': [],
                'layout': go.Layout(
                    title=f"No data for {metric}",
                    xaxis_title="Shock Value", 
                    yaxis_title="Metric Value",
                    plot_bgcolor=default_theme.base_bg,
                    paper_bgcolor=default_theme.panel_bg,
                    font_color=default_theme.text_light,
                    height=400
                )
            }
        
        fig = go.Figure()
        colors = px.colors.qualitative.Set1
        
        # Add one trace per scenario for this metric
        for i, scenario in enumerate(selected_scenarios):
            scenario_df = df[df['scenario_header'] == scenario]
            if not scenario_df.empty and metric in scenario_df.columns:
                fig.add_trace(go.Scatter(
                    x=scenario_df['shock_value'],
                    y=scenario_df[metric],
                    mode='lines+markers',
                    name=scenario,
                    line=dict(color=colors[i % len(colors)]),
                    marker=dict(size=6)
                ))
        
        fig.update_layout(
            title=f"Scenarios for {metric}",
            xaxis_title="Shock Value",
            yaxis_title="Metric Value",
            plot_bgcolor=default_theme.base_bg,
            paper_bgcolor=default_theme.panel_bg,
            font_color=default_theme.text_light,
            xaxis=dict(
                showgrid=True, 
                gridcolor=default_theme.secondary,
            ),
            yaxis=dict(showgrid=True, gridcolor=default_theme.secondary),
            height=400,
            margin=dict(l=60, r=20, t=60, b=50),
            legend=dict(
                bgcolor=default_theme.panel_bg,
                bordercolor=default_theme.secondary,
                borderwidth=1
            )
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Error updating metric graph: {e}")
        return {
            'data': [],
            'layout': go.Layout(
                title=f"Error: {str(e)}",
                plot_bgcolor=default_theme.base_bg,
                paper_bgcolor=default_theme.panel_bg,
                font_color=default_theme.text_light,
                height=400
            )
        }

@app.callback(
    [Output({"type": "aeod-metric-table", "metric": MATCH}, "data"),
     Output({"type": "aeod-metric-table", "metric": MATCH}, "columns")],
    [Input("aeod-scenario-listbox", "value"),
     Input("aeod-toggle-states-store", "data"),
     Input({"type": "aeod-metric-range-slider", "metric": MATCH}, "value")],
    State({"type": "aeod-metric-table", "metric": MATCH}, "id"),
    State("aeod-data-loaded-store", "data"),
    prevent_initial_call=False
)
@monitor()
def aeod_update_metric_table(selected_scenarios, toggle_states, range_values, table_id, data_loaded):
    """Update table for a specific metric based on selected scenarios and range."""
    if not data_loaded or not selected_scenarios or not range_values:
        return [], []
    
    try:
        metric = table_id["metric"]
        is_percentage = toggle_states.get("is_percentage", False)
        
        # Determine shock type based on percentage toggle
        shock_type = "percentage" if is_percentage else "absolute_usd"
        
        # Get data service
        data_service = aeod_get_data_service()
        
        # Create global shock range for this metric across all scenarios
        global_shock_ranges = {}
        for scenario in selected_scenarios:
            global_shock_ranges[scenario] = range_values  # Same range for all scenarios
        
        # Get filtered data for all scenarios within the range
        df = data_service.get_filtered_data_with_range(
            scenario_headers=selected_scenarios,
            shock_types=[shock_type],
            shock_ranges=global_shock_ranges,
            metrics=[metric]
        )
        
        if df.empty:
            return [], []
        
        # Pivot data: shock_value as index, scenarios as columns, metric values as data
        pivot_df = df.pivot_table(
            index='shock_value', 
            columns='scenario_header', 
            values=metric,
            fill_value=np.nan
        )
        
        # Flatten column names to "metric-scenario" format
        pivot_df.columns = [f"{metric}-{scenario}" for scenario in pivot_df.columns]
        
        # Reset index to make shock_value a regular column
        display_df = pivot_df.reset_index()
        
        # Apply shock value formatting based on percentage toggle
        if is_percentage:
            display_df['shock_value'] = display_df['shock_value'].apply(
                lambda x: format_shock_value_for_display(x, "percentage")
            )
        else:
            display_df['shock_value'] = display_df['shock_value'].apply(
                lambda x: format_shock_value_for_display(x, "absolute_usd")
            )
        
        # Create columns configuration
        columns = []
        for col in display_df.columns:
            column_config = {"name": col, "id": col}
            
            # Format numeric columns
            if display_df[col].dtype in ['float64', 'int64']:
                column_config["type"] = "numeric"
                column_config["format"] = {"specifier": ",.4f"}
            
            columns.append(column_config)
        
        return display_df.to_dict('records'), columns
        
    except Exception as e:
        logger.error(f"Error updating metric table: {e}")
        return [], []

# --- End Actant EOD Callbacks ---

# Button Style Callbacks for Visual Feedback
@app.callback(
    [Output("aeod-view-mode-graph-btn", "style"),
     Output("aeod-view-mode-table-btn", "style")],
    [Input("aeod-view-mode-graph-btn", "n_clicks"),
     Input("aeod-view-mode-table-btn", "n_clicks")],
    prevent_initial_call=False
)
@monitor()
def aeod_update_view_mode_button_styles(graph_clicks, table_clicks):
    """Update button styles for view mode toggle."""
    ctx = dash.callback_context
    
    # Default to graph view
    if not ctx.triggered:
        return (
            {'borderTopRightRadius': '0', 'borderBottomRightRadius': '0', 'borderRight': 'none', 
             'backgroundColor': default_theme.primary},
            {'borderTopLeftRadius': '0', 'borderBottomLeftRadius': '0', 'backgroundColor': default_theme.panel_bg}
        )
    
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if triggered_id == "aeod-view-mode-graph-btn":
        # Graph selected
        return (
            {'borderTopRightRadius': '0', 'borderBottomRightRadius': '0', 'borderRight': 'none', 
             'backgroundColor': default_theme.primary},
            {'borderTopLeftRadius': '0', 'borderBottomLeftRadius': '0', 'backgroundColor': default_theme.panel_bg}
        )
    else:
        # Table selected
        return (
            {'borderTopRightRadius': '0', 'borderBottomRightRadius': '0', 'borderRight': 'none', 
             'backgroundColor': default_theme.panel_bg},
            {'borderTopLeftRadius': '0', 'borderBottomLeftRadius': '0', 'backgroundColor': default_theme.primary}
        )

@app.callback(
    [Output("aeod-percentage-absolute-btn", "style"),
     Output("aeod-percentage-percentage-btn", "style")],
    [Input("aeod-percentage-absolute-btn", "n_clicks"),
     Input("aeod-percentage-percentage-btn", "n_clicks")],
    prevent_initial_call=False
)
@monitor()
def aeod_update_percentage_button_styles(abs_clicks, pct_clicks):
    """Update button styles for percentage toggle."""
    ctx = dash.callback_context
    
    # Default to absolute view
    if not ctx.triggered:
        return (
            {'borderTopRightRadius': '0', 'borderBottomRightRadius': '0', 'borderRight': 'none', 
             'backgroundColor': default_theme.primary},
            {'borderTopLeftRadius': '0', 'borderBottomLeftRadius': '0', 'backgroundColor': default_theme.panel_bg}
        )
    
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if triggered_id == "aeod-percentage-absolute-btn":
        # Absolute selected
        return (
            {'borderTopRightRadius': '0', 'borderBottomRightRadius': '0', 'borderRight': 'none', 
             'backgroundColor': default_theme.primary},
            {'borderTopLeftRadius': '0', 'borderBottomLeftRadius': '0', 'backgroundColor': default_theme.panel_bg}
        )
    else:
        # Percentage selected
        return (
            {'borderTopRightRadius': '0', 'borderBottomRightRadius': '0', 'borderRight': 'none', 
             'backgroundColor': default_theme.panel_bg},
            {'borderTopLeftRadius': '0', 'borderBottomLeftRadius': '0', 'backgroundColor': default_theme.primary}
        )

@app.callback(
    [Output("aeod-viz-mode-scenario-btn", "style"),
     Output("aeod-viz-mode-metric-btn", "style")],
    [Input("aeod-viz-mode-scenario-btn", "n_clicks"),
     Input("aeod-viz-mode-metric-btn", "n_clicks")],
    prevent_initial_call=False
)
@monitor()
def aeod_update_viz_mode_button_styles(scenario_clicks, metric_clicks):
    """Update button styles for visualization mode toggle."""
    ctx = dash.callback_context
    
    # Default to scenario view
    if not ctx.triggered:
        return (
            {'borderTopRightRadius': '0', 'borderBottomRightRadius': '0', 'borderRight': 'none', 
             'backgroundColor': default_theme.primary},
            {'borderTopLeftRadius': '0', 'borderBottomLeftRadius': '0', 'backgroundColor': default_theme.panel_bg}
        )
    
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if triggered_id == "aeod-viz-mode-scenario-btn":
        # Scenario selected
        return (
            {'borderTopRightRadius': '0', 'borderBottomRightRadius': '0', 'borderRight': 'none', 
             'backgroundColor': default_theme.primary},
            {'borderTopLeftRadius': '0', 'borderBottomLeftRadius': '0', 'backgroundColor': default_theme.panel_bg}
        )
    else:
        # Metric selected
        return (
            {'borderTopRightRadius': '0', 'borderBottomRightRadius': '0', 'borderRight': 'none', 
             'backgroundColor': default_theme.panel_bg},
            {'borderTopLeftRadius': '0', 'borderBottomLeftRadius': '0', 'backgroundColor': default_theme.primary}
        )

# --- End Actant EOD Callbacks ---

# Scenario Ladder Demo Mode Toggle Callback
@app.callback(
    [Output("scl-demo-mode-store", "data"),
     Output("scl-demo-mode-btn", "style"), 
     Output("scl-live-mode-btn", "style")],
    [Input("scl-demo-mode-btn", "n_clicks"),
     Input("scl-live-mode-btn", "n_clicks")],
    prevent_initial_call=False
)
@monitor()
def scl_toggle_demo_mode(demo_clicks, live_clicks):
    """Toggle between demo and live mode"""
    ctx = dash.callback_context
    
    # Default to demo mode
    if not ctx.triggered:
        return (
            {'demo_mode': True},
            {'borderTopRightRadius': '0', 'borderBottomRightRadius': '0', 'borderRight': 'none', 
             'backgroundColor': default_theme.primary},
            {'borderTopLeftRadius': '0', 'borderBottomLeftRadius': '0', 'backgroundColor': default_theme.panel_bg}
        )
    
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if triggered_id == "scl-demo-mode-btn":
        # Demo mode selected
        return (
            {'demo_mode': True},
            {'borderTopRightRadius': '0', 'borderBottomRightRadius': '0', 'borderRight': 'none', 
             'backgroundColor': default_theme.primary},
            {'borderTopLeftRadius': '0', 'borderBottomLeftRadius': '0', 'backgroundColor': default_theme.panel_bg}
        )
    else:
        # Live mode selected
        return (
            {'demo_mode': False},
            {'borderTopRightRadius': '0', 'borderBottomRightRadius': '0', 'borderRight': 'none', 
             'backgroundColor': default_theme.panel_bg},
            {'borderTopLeftRadius': '0', 'borderBottomLeftRadius': '0', 'backgroundColor': default_theme.primary}
        )

if __name__ == "__main__":
    # Comprehensive logger configuration:
    # - All user interactions are traced with @monitor decorator
    # - All data processing functions include full tracing
    # - All INFO/ERROR/WARNING logs are sent to the database tables
    # - External functions are wrapped with traced versions
    logger.info("Starting Dashboard...")
    app.run(debug=True, port=8052, use_reloader=False, host='0.0.0.0')