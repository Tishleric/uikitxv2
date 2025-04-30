# demo/app.py (Bootstrap CSS Added Example - Style Fix)

import dash
from dash import html, dash_table
import dash_bootstrap_components as dbc # Import dbc
import os
import sys
import logging
import atexit

# --- Adjust Python path ---
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.join(project_root, 'src')
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)-8s - %(name)s - %(message)s')
if src_path not in sys.path:
    sys.path.insert(0, src_path)
    logger.debug(f"Added '{src_path}' to sys.path")
else:
    logger.debug(f"'{src_path}' already in sys.path")
# --- End Path Adjustment ---

# --- Import uikitxv2 components ---
try:
    from components import Button, Tabs, Grid, DataTable
    from lumberjack.logging_config import setup_logging, shutdown_logging
    # Import the theme object to access colors directly for body styling
    from utils.colour_palette import default_theme # IMPORT THEME
    logger.debug("Successfully imported uikitxv2 components and theme")
except ImportError as e:
    logger.error(f"Error importing uikitxv2 components: {e}")
    sys.exit(1)
# --- End uikitxv2 Import ---

# --- Logging Configuration ---
LOG_DB_DIR = os.path.join(project_root, 'logs')
LOG_DB_PATH = os.path.join(LOG_DB_DIR, 'demo_app_simple_logs.db')
os.makedirs(LOG_DB_DIR, exist_ok=True)
logger.debug(f"Ensuring log database directory exists: {LOG_DB_DIR}")
logger.debug(f"Using log database: {LOG_DB_PATH}")
console_handler, db_handler = setup_logging(
    db_path=LOG_DB_PATH,
    log_level_console=logging.DEBUG
)
atexit.register(shutdown_logging)
logger.info("Logging configured via setup_logging and shutdown registered.")

# --- Initialize Dash App ---
# Added standard Bootstrap CSS for structure
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "UIKitXv2 Tabs Demo - CSS Fix"

# --- UI Component Instantiation ---
simple_button = Button(label="Click Me!", id="simple-demo-button")
logger.debug("Instantiated uikitxv2.Button")

log_table = DataTable(
    id="log-table-display",
    columns=[
        {"name": "Timestamp", "id": "timestamp"},
        {"name": "Function", "id": "function_name"},
        {"name": "Duration (s)", "id": "execution_time_s", "type": "numeric", "format": dash_table.Format.Format(precision=3, scheme=dash_table.Format.Scheme.fixed)},
        {"name": "CPU Δ (%)", "id": "cpu_usage_delta", "type": "numeric", "format": dash_table.Format.Format(precision=2, scheme=dash_table.Format.Scheme.fixed)},
        {"name": "Memory Δ (MB)", "id": "memory_usage_delta_mb", "type": "numeric", "format": dash_table.Format.Format(precision=3, scheme=dash_table.Format.Scheme.fixed)},
        {"name": "Log UUID", "id": "log_uuid"},
    ],
    data=[],
    filter_action="none",
    sort_action="native",
    page_size=10
)
logger.debug("Instantiated uikitxv2.DataTable for logs tab")

# --- Define Tab Content using uikitxv2.Grid ---
components_tab_content_grid = Grid(
    id="grid-components-tab",
    children=[simple_button],
)
logs_tab_content_grid = Grid(
    id="grid-logs-tab",
    children=[log_table],
)
logger.debug("Defined tab content using uikitxv2.Grid")

# --- Instantiate Tabs Component ---
# Ensure you are using the updated tabs.py which includes label_style/active_label_style
main_tabs = Tabs(
    id="main-demo-tabs",
    tabs=[
        ("Components", components_tab_content_grid),
        ("Logs", logs_tab_content_grid)
    ]
)
logger.debug("Instantiated uikitxv2.Tabs")

# --- App Layout ---
# Using a minimal layout - just the Tabs component wrapped in a Div.
app.layout = html.Div([ # Wrap layout in a div
    # --- CORRECTED: Changed html.style to html.Style ---
    # Set background to match your theme's base and default text color
    html.Style(f"""
        body {{
            background-color: {default_theme.base_bg};
            color: {default_theme.text_light}; /* Set default text color */
            margin: 0;
            padding: 15px; /* Add some padding around the content */
            font-family: Inter, sans-serif; /* Optional: Set default font */
        }}
        /* Minor adjustment for tabs appearance with Bootstrap base */
        .nav-tabs {{
            border-bottom: none; /* Remove default bootstrap border if Tabs component adds its own */
            margin-bottom: 0 !important; /* Override bootstrap margin if needed */
        }}
        .tab-content {{
             /* Add padding/margin to content area below tabs if needed */
             /* Example: padding-top: 1rem; */
        }}
        /* Ensure tab links inherit color correctly */
        .nav-tabs .nav-link {{
            color: inherit; /* Make links inherit color from parent style */
        }}
        /* Remove default Bootstrap active tab background/border */
        .nav-tabs .nav-link.active {{
            background-color: transparent !important;
            border-color: transparent transparent transparent !important;
        }}

    """),
    # Render the Tabs component
    main_tabs.render()
])
logger.debug("Dash layout defined using only main_tabs.render() within a Div")

# --- Execution ---
if __name__ == "__main__":
    logger.info("Starting Dash server...")
    app.run(debug=True, port=8050)

