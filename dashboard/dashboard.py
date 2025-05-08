# uikitxv2/dashboard/dashboard.py

import dash
from dash import html, dcc, Input, Output, State
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import os
import sys
import logging
import atexit
import pandas as pd
import traceback

# --- Adjust Python path ---
current_script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_script_dir) 

if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"Added '{project_root}' to sys.path for package 'src'")
# --- End Path ---

# --- Imports ---
try:
    from src.lumberjack.logging_config import setup_logging, shutdown_logging
    from src.utils.colour_palette import default_theme
    from src.components import Tabs, Grid, Button, ComboBox, Container, DataTable
    print("Successfully imported uikitxv2 logging, theme, and UI components from 'src'.")
    # MODIFIED: Import the correct function name
    from src.PricingMonkey.pMoneyAuto import run_pm_automation 
    print("Successfully imported run_pm_automation from 'src.PricingMonkey.pMoneyAuto'.")
except ImportError as e:
    print(f"Error importing from 'src' package: {e}")
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
console_handler, db_handler = setup_logging(
    db_path=LOG_DB_PATH, log_level_console=logging.DEBUG, log_level_db=logging.INFO, log_level_main=logging.DEBUG
)
atexit.register(shutdown_logging)
logger = logging.getLogger(__name__)
# --- End Logging ---

# --- Initialize Dash App ---
assets_folder_path_absolute = os.path.abspath(os.path.join(project_root, 'assets'))
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    assets_folder=assets_folder_path_absolute,
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

# PREDEFINED_UI_COLUMNS - these 'id' fields must match the DataFrame columns after processing
PREDEFINED_UI_COLUMNS = [
    {'name': 'Trade Amount', 'id': 'Trade Amount'},
    {'name': 'Trade Description', 'id': 'Trade Description'},
    {'name': 'Underlying', 'id': 'Underlying'},
    {'name': 'DV01 Gamma', 'id': 'DV01 Gamma'}, 
    {'name': 'Theta', 'id': 'Theta'},
    {'name': 'Vega', 'id': 'Vega'},
]

def create_option_input_block(option_index: int) -> Container:
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
            html.P("Phase of entry:", style=text_style), phase_combo_instance,
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
    label="Run Pricing Monkey Automation", id="update-sheet-button", theme=default_theme, n_clicks=0 # Changed Label
).render()
update_sheet_button_wrapper = html.Div(update_sheet_button_rendered, style={'marginTop': '25px', 'textAlign': 'center'})

initial_empty_datatable_instance = DataTable(
    id="results-datatable", data=[], columns=PREDEFINED_UI_COLUMNS, theme=default_theme,
    page_size=10, 
    style_table={'minWidth': '100%', 'marginTop': '20px'},
    style_header={'backgroundColor': default_theme.panel_bg, 'fontWeight': 'bold', 'color': default_theme.text_light},
    style_cell={'backgroundColor': default_theme.base_bg, 'color': default_theme.text_light, 'textAlign': 'left', 'padding': '10px'},
)

results_grid_rendered = Grid(
    id="results-grid-area",
    children=[initial_empty_datatable_instance], # Children is a list
    style={'marginTop': '30px', 'width': '100%'}
).render()

pricing_monkey_tab_main_container_rendered = Container(
    id="pm-tab-main-container",
    children=[
        num_options_question_text,
        num_options_selector_rendered,
        dynamic_options_area,
        update_sheet_button_wrapper,
        results_grid_rendered # Grid component itself, not its children
    ]
).render()

main_tabs_rendered = Tabs(
    id="main-dashboard-tabs",
    tabs=[("Pricing Monkey Setup", pricing_monkey_tab_main_container_rendered)],
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
def update_option_blocks(selected_num_options_str: str | None):
    if selected_num_options_str is None: num_active_options = 1
    else:
        try: num_active_options = int(selected_num_options_str)
        except (ValueError, TypeError): num_active_options = 1
        if not 1 <= num_active_options <= 3: num_active_options = 1

    logger.info(f"Updating dynamic area to show {num_active_options} options.")
    output_children = []
    for i in range(3): # Always create 3, hide/show as needed
        option_block_instance = create_option_input_block(i)
        display_style = {'display': 'block'} if i < num_active_options else {'display': 'none'}
        wrapper_div = html.Div(
            children=option_block_instance.render(), # Render the container
            id=f"option-{i}-wrapper", # ID for the wrapper div
            style=display_style
        )
        output_children.append(wrapper_div)
    return output_children


@app.callback(
    Output("results-grid-area", "children"), 
    Input("update-sheet-button", "n_clicks"),
    [State(f"option-{i}-{field}", "value") for i in range(3) for field in ["desc-prefix", "desc-strike", "desc-type", "qty", "phase"]] +
    [State("num-options-selector", "value")],
    prevent_initial_call=True
)
def handle_update_sheet_button_click(n_clicks, *args):
    if n_clicks is None or n_clicks == 0: raise PreventUpdate

    num_options_str = args[-1]
    all_option_field_values = args[:-1]

    logger.info(f"'Run Pricing Monkey Automation' button clicked. Processing inputs...")
    try: num_active_options = int(num_options_str)
    except (ValueError, TypeError):
        logger.error(f"Invalid number of options: {num_options_str}.")
        error_message = html.P("Invalid number of options selected.", style={'color': 'red', 'textAlign': 'center', 'marginTop': '10px'})
        empty_table = DataTable(id="results-datatable", data=[], columns=PREDEFINED_UI_COLUMNS, theme=default_theme, page_size=10).render()
        return [error_message, empty_table]

    ui_options_data = [] # This will be passed to run_pm_automation
    fields_per_option = 5
    for i in range(num_active_options):
        start_idx = i * fields_per_option
        prefix, strike, opt_type, qty_str, phase_str = all_option_field_values[start_idx : start_idx + fields_per_option]

        if not all([prefix, strike, opt_type, qty_str is not None, phase_str]):
            logger.warning(f"Option {i+1} missing fields. Skipping."); continue
        try:
            qty_val, phase_val = int(qty_str), int(phase_str)
            if qty_val <= 0: logger.warning(f"Option {i+1} non-positive qty. Skipping."); continue
        except (ValueError, TypeError):
            logger.error(f"Invalid qty/phase for Option {i+1}. Skipping."); continue
        
        # Construct the description string as expected by pMoneyAuto
        trade_desc_string = f"{prefix} 10y note {strike} out {opt_type}"
        ui_options_data.append({'desc': trade_desc_string, 'qty': qty_val, 'phase': phase_val, 'id': i})

    if not ui_options_data:
        logger.warning("No valid option data to process.")
        message = html.P("No valid option data. Please check inputs.", style={'color': default_theme.text_light, 'textAlign': 'center', 'marginTop': '10px'})
        empty_table = DataTable(id="results-datatable", data=[], columns=PREDEFINED_UI_COLUMNS, theme=default_theme, page_size=10).render()
        return [message, empty_table]

    results_df_from_pm = None # This will be the joined_df
    try:
        logger.info(f"Calling run_pm_automation with: {ui_options_data}")
        # Call the integrated function
        results_df_from_pm = run_pm_automation(ui_options_data) 
    except Exception as e:
        logger.error(f"Error in run_pm_automation: {e}", exc_info=True)
        error_message = html.P(f"Error during automation: {e}", style={'color': 'red', 'textAlign': 'center', 'marginTop': '10px'})
        empty_table = DataTable(id="results-datatable", data=[], columns=PREDEFINED_UI_COLUMNS, theme=default_theme, page_size=10).render()
        return [error_message, empty_table]

    if results_df_from_pm is not None and isinstance(results_df_from_pm, pd.DataFrame) and not results_df_from_pm.empty:
        logger.info(f"PM Automation returned DataFrame. Shape: {results_df_from_pm.shape}")
        logger.info(f"Columns from PM Automation: {results_df_from_pm.columns.tolist()}")

        # The DataFrame from run_pm_automation should have columns:
        # "Trade Amount", "Trade Description", "Underlying", "DV01 Gamma", "Theta", "Vega"
        
        # Ensure all PREDEFINED_UI_COLUMNS are present, fill with "N/A" if missing
        # This step is crucial if run_pm_automation might not return all expected columns
        for col_info in PREDEFINED_UI_COLUMNS:
            if col_info['id'] not in results_df_from_pm.columns:
                logger.warning(f"Column '{col_info['id']}' missing from PM results, adding as N/A.")
                results_df_from_pm[col_info['id']] = "N/A"
        
        # Format numerical columns (Greeks) to string with 2 decimal places
        # The column names "DV01 Gamma", "Theta", "Vega" should now directly match.
        for col_name in ['DV01 Gamma', 'Theta', 'Vega']:
            if col_name in results_df_from_pm.columns:
                results_df_from_pm[col_name] = results_df_from_pm[col_name].apply(
                    lambda x: f"{x:.2f}" if pd.notna(x) and isinstance(x, (int, float)) else ("N/A" if pd.isna(x) else str(x))
                )
            # No need for an else to add the column here, as the previous loop should handle it.

        # Select and order columns for the UI table
        ordered_column_ids = [col['id'] for col in PREDEFINED_UI_COLUMNS]
        results_df_for_ui_ordered = results_df_from_pm[ordered_column_ids]

        logger.info(f"Displaying results. Columns for UI: {results_df_for_ui_ordered.columns.tolist()}")
        
        final_table = DataTable(
            id="results-datatable", 
            data=results_df_for_ui_ordered.to_dict('records'), 
            columns=PREDEFINED_UI_COLUMNS, # Use the predefined column structure
            theme=default_theme, page_size=10, 
            style_table={'minWidth': '100%', 'marginTop': '20px'},
            style_header={'backgroundColor': default_theme.panel_bg, 'fontWeight': 'bold', 'color': default_theme.text_light},
            style_cell={'backgroundColor': default_theme.base_bg, 'color': default_theme.text_light, 'textAlign': 'left', 'padding': '10px'},
        ).render()
        return [final_table] # Return as a list for Grid children
    
    elif results_df_from_pm is not None and results_df_from_pm.empty:
        logger.warning("PM Automation returned an empty DataFrame.")
        message = html.P("Automation ran but returned no data.", style={'color': default_theme.text_light, 'textAlign': 'center', 'marginTop': '10px'})
        empty_table = DataTable(id="results-datatable", data=[], columns=PREDEFINED_UI_COLUMNS, theme=default_theme, page_size=10).render()
        return [message, empty_table]
    else: # results_df_from_pm is None
        logger.warning("No DataFrame returned from PM automation (it was None).")
        message = html.P("No results from automation or an error occurred (see logs).", style={'color': default_theme.text_light, 'textAlign': 'center', 'marginTop': '10px'})
        empty_table = DataTable(id="results-datatable", data=[], columns=PREDEFINED_UI_COLUMNS, theme=default_theme, page_size=10).render()
        return [message, empty_table]

# --- End Callbacks ---

if __name__ == "__main__":
    logger.info("Starting Dashboard...")
    # Set use_reloader to False if pywinauto has issues with reloading,
    # or if you see errors related to file access during development.
    app.run(debug=True, port=8052, use_reloader=False)
