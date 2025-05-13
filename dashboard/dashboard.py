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
import json
from io import StringIO

# --- Adjust Python path ---
current_script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_script_dir) 

if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"Added '{project_root}' to sys.path for package 'src'")

# --- Create module alias for imports ---
import src
sys.modules['uikitxv2'] = src
# --- End Path ---

# --- Imports ---
try:
    from uikitxv2.lumberjack.logging_config import setup_logging, shutdown_logging
    from uikitxv2.utils.colour_palette import default_theme
    # ComboBox and Graph are already imported from your file.
    from uikitxv2.components import Tabs, Grid, Button, ComboBox, Container, DataTable, Graph, RadioButton, Mermaid
    print("Successfully imported uikitxv2 logging, theme, and UI components.")
    from uikitxv2.PricingMonkey.pMoneyAuto import run_pm_automation 
    from uikitxv2.PricingMonkey.pMoneyMovement import get_market_movement_data_df, SCENARIOS
    print("Successfully imported PM modules from 'uikitxv2.PricingMonkey'.")
    # Import decorator functions
    from uikitxv2.decorators.trace_closer import TraceCloser
    from uikitxv2.decorators.trace_cpu import TraceCpu
    from uikitxv2.decorators.trace_time import TraceTime
    from uikitxv2.decorators.trace_memory import TraceMemory
    print("Successfully imported tracing decorators.")
except ImportError as e:
    print(f"Error importing from 'uikitxv2' package: {e}")
    print(f"Current sys.path: {sys.path}")
    print(f"Project root evaluated as: {project_root}")
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

# Wrapper function to trace logging setup
@TraceCloser()
@TraceTime(log_args=False, log_return=False)
def setup_logging_traced():
    """Wrapper to trace the execution time of setup_logging."""
    return setup_logging(
        db_path=LOG_DB_PATH, 
        log_level_console=logging.DEBUG, 
        log_level_db=logging.INFO, 
        log_level_main=logging.DEBUG
    )

# Wrapper function to trace logging shutdown
@TraceCloser()
@TraceTime(log_args=False, log_return=False)
def shutdown_logging_traced():
    """Wrapper to trace the execution time of shutdown_logging."""
    return shutdown_logging()

if not logger_root.handlers: 
    console_handler, db_handler = setup_logging_traced()
    atexit.register(shutdown_logging_traced)
logger = logging.getLogger(__name__)

@TraceCloser()
@TraceTime(log_args=False, log_return=False)
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
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP], 
    assets_folder=assets_folder_path_absolute,
    suppress_callback_exceptions=True 
)
app.title = "Pricing Monkey Automation Dashboard"
# --- End App Init ---

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
@TraceCloser()
@TraceTime(log_args=True, log_return=False)
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

@TraceCloser()
@TraceTime(log_args=False, log_return=False)
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
        md --> | options order |cmeDirect
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
    
    # Wrap it all in a Container
    mermaid_container = Container(
        id="mermaid-tab-container",
        children=[
            html.H4("Diagram Visualization", style={"color": default_theme.primary, "marginBottom": "20px", "textAlign": "center"}),
            mermaid_grid.render()
        ],
        style={"padding": "15px"}
    )
    
    return mermaid_container.render()

main_tabs_rendered = Tabs(
    id="main-dashboard-tabs",
    tabs=[
        ("Pricing Monkey Setup", pricing_monkey_tab_main_container_rendered),
        ("Analysis", analysis_tab_content),
        ("Logs", create_logs_tab()),
        ("Mermaid", create_mermaid_tab())
    ], 
    theme=default_theme
).render()

app.layout = html.Div(
    children=[
        html.H1("Pricing Monkey Automation", style={"textAlign": "center", "color": default_theme.primary, "padding": "20px 0"}), 
        main_tabs_rendered
    ],
    style={"backgroundColor": default_theme.base_bg, "padding": "20px", "minHeight": "100vh", "fontFamily": "Inter, sans-serif"} 
)
logger.info("UI layout defined.")
# --- End Layout ---

# --- Callbacks ---
@app.callback(
    Output("dynamic-options-area", "children"),
    Input("num-options-selector", "value")
)
@TraceCloser()
@TraceTime(log_args=False, log_return=False)
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
@TraceCloser()
@TraceCpu()
@TraceMemory()
@TraceTime(log_args=False, log_return=False)
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
        list_of_option_dfs_from_pm = run_pm_automation_traced(ui_options_data_for_pm) 
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
@TraceCloser()
@TraceTime(log_args=False, log_return=False)
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
@TraceCloser()
@TraceCpu()
@TraceMemory()
@TraceTime(log_args=False, log_return=False)
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
            result_dict = get_market_movement_data_df_traced()
            
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

@TraceCloser()
@TraceCpu()
@TraceMemory()
@TraceTime(log_args=False, log_return=False)
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

@TraceCloser()
@TraceCpu()
@TraceMemory()
@TraceTime(log_args=False, log_return=False)
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
@TraceCloser()
@TraceTime(log_args=False, log_return=False)
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
@TraceCloser()
@TraceTime(log_args=False, log_return=False)
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
@TraceCloser()
@TraceCpu()
@TraceMemory()
@TraceTime(log_args=True, log_return=False)
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

# --- Add Wrapped External Functions ---
@TraceCloser()
@TraceCpu()
@TraceMemory()
@TraceTime(log_args=True, log_return=False)
def run_pm_automation_traced(ui_options_data_for_pm):
    """Traced wrapper for run_pm_automation."""
    return run_pm_automation(ui_options_data_for_pm)

@TraceCloser()
@TraceCpu()
@TraceMemory()
@TraceTime(log_args=False, log_return=False)
def get_market_movement_data_df_traced():
    """Traced wrapper for get_market_movement_data_df."""
    return get_market_movement_data_df()

# --- End Function Wrappers ---

# --- End Callbacks ---

@TraceCloser()
@TraceTime(log_args=True, log_return=False)
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
@TraceCloser()
@TraceCpu()
@TraceMemory()
@TraceTime(log_args=True, log_return=False)
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

if __name__ == "__main__":
    # Comprehensive logger configuration:
    # - All user interactions are traced with @TraceCloser, @TraceCpu, @TraceTime
    # - All data processing functions include full tracing
    # - All INFO/ERROR/WARNING logs are sent to the database tables
    # - External functions are wrapped with traced versions
    logger.info("Starting Dashboard...")
    app.run(debug=True, port=8052, use_reloader=False)
