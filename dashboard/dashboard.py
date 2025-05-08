# uikitxv2/dashboard/dashboard.py

import dash
from dash import html, dcc, Input, Output, State # type: ignore
from dash.exceptions import PreventUpdate # type: ignore
import dash_bootstrap_components as dbc # type: ignore
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
logger_root = logging.getLogger()
if not logger_root.handlers: 
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
    external_stylesheets=[dbc.themes.BOOTSTRAP], # dbc.themes.DARKLY or another theme
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

RESULT_TABLE_COLUMNS = [
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

# This area will be populated by the callback with dbc.Row and dbc.Col for side-by-side tables
results_display_area_content = html.Div(id="results-display-area-content", children=[
    # Placeholder for initial empty state or a message
    html.P("Results will appear here.", style={'textAlign': 'center', 'color': default_theme.text_light, 'marginTop': '20px'})
])

results_grid_rendered = Grid( # This Grid is essentially a styled html.Div
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

    output_children = []
    for i in range(3): 
        option_block_container_obj = create_option_input_block(i) 
        display_style = {'display': 'block'} if i < num_active_options else {'display': 'none'}
        wrapper_div = html.Div(children=option_block_container_obj.render(), id=f"option-{i}-wrapper", style=display_style)
        output_children.append(wrapper_div)
    return output_children


@app.callback(
    Output("results-display-area-content", "children"), # MODIFIED: Output to the inner Div
    Input("update-sheet-button", "n_clicks"),
    [State(f"option-{i}-{field}", "value") for i in range(3) for field in ["desc-prefix", "desc-strike", "desc-type", "qty", "phase"]] +
    [State("num-options-selector", "value")],
    prevent_initial_call=True
)
def handle_update_sheet_button_click(n_clicks: int | None, *args: any):
    if n_clicks is None or n_clicks == 0: raise PreventUpdate

    num_options_str = args[-1]
    all_option_field_values = args[:-1]

    logger.info(f"'Run Automation' clicked. Processing inputs...")
    try: num_active_options = int(str(num_options_str))
    except (ValueError, TypeError):
        logger.error(f"Invalid num options: {num_options_str}."); return [html.P("Invalid number of options.", style={'color': 'red'})]

    ui_options_data = [] 
    fields_per_option = 5
    for i in range(num_active_options):
        start_idx = i * fields_per_option
        prefix, strike, opt_type, qty_str, phase_str = all_option_field_values[start_idx : start_idx + fields_per_option]
        if not all([prefix, strike, opt_type, qty_str is not None, phase_str]):
            logger.warning(f"Opt {i+1} missing fields."); continue
        try:
            qty_val, phase_val = int(str(qty_str)), int(str(phase_str))
            if qty_val <= 0: logger.warning(f"Opt {i+1} non-positive qty."); continue
        except (ValueError, TypeError): logger.error(f"Invalid qty/phase for Opt {i+1}."); continue
        ui_options_data.append({'desc': f"{prefix} 10y note {strike} out {opt_type}", 'qty': qty_val, 'phase': phase_val, 'id': i})

    if not ui_options_data:
        logger.warning("No valid option data."); return [html.P("No valid option data.", style=text_style)]

    list_of_option_dfs_from_pm = None 
    try:
        logger.info(f"Calling run_pm_automation with: {ui_options_data}")
        list_of_option_dfs_from_pm = run_pm_automation(ui_options_data) 
    except Exception as e:
        logger.error(f"Error in run_pm_automation: {e}", exc_info=True)
        return [html.P(f"Error during automation: {str(e)[:200]}...", style={'color': 'red'})]

    if not list_of_option_dfs_from_pm or not isinstance(list_of_option_dfs_from_pm, list):
        logger.warning("No list of DFs from PM automation or incorrect type.")
        return [html.P("No results from automation or an error (see logs).", style=text_style)]

    # --- MODIFIED: Display logic for multiple side-by-side tables ---
    all_option_display_blocks = []
    col_width = 12 // len(ui_options_data) if ui_options_data else 12 # Calculate column width for side-by-side

    for i, option_input in enumerate(ui_options_data):
        if i >= len(list_of_option_dfs_from_pm):
            logger.warning(f"Missing DataFrame for option index {i}. Skipping display for this option.")
            all_option_display_blocks.append(dbc.Col([html.P(f"No data for Option {i+1}", style=text_style)], width=col_width))
            continue

        current_option_df = list_of_option_dfs_from_pm[i]
        if not isinstance(current_option_df, pd.DataFrame):
            logger.warning(f"Item at index {i} is not a DataFrame. Skipping display for this option.")
            all_option_display_blocks.append(dbc.Col([html.P(f"Invalid data for Option {i+1}", style=text_style)], width=col_width))
            continue


        option_display_elements = []
        
        desc_to_display = option_input['desc']
        user_trade_amount_for_scaling = option_input['qty']

        desc_html = html.H4(f"Trade Description: {desc_to_display}", style={"color": default_theme.text_light, "marginTop": "0px", "marginBottom": "5px", "fontSize":"0.9rem"})
        amount_html = html.H5(f"Trade Amount: {user_trade_amount_for_scaling}", style={"color": default_theme.text_light, "marginBottom": "15px", "fontSize":"0.8rem"})
        option_display_elements.extend([desc_html, amount_html])

        if current_option_df.empty:
            logger.info(f"Data for Option {i+1} (Desc: {desc_to_display}) is empty. Displaying no data message.")
            option_display_elements.append(html.P("No detailed results for this option.", style=text_style))
        else:
            logger.info(f"Processing Option {i+1} (Desc: {desc_to_display}), DF shape: {current_option_df.shape}")
            
            # Scale Greek values for THIS option's DataFrame
            if user_trade_amount_for_scaling > 0:
                multiplier = user_trade_amount_for_scaling / 1000.0
                logger.info(f"Scaling Option {i+1} Greeks by {multiplier}")
                for col_name in ['DV01 Gamma', 'Theta', 'Vega']:
                    if col_name in current_option_df.columns:
                        original_col = current_option_df[col_name].copy()
                        numeric_col = pd.to_numeric(current_option_df[col_name], errors='coerce')
                        scaled_col = numeric_col * multiplier
                        current_option_df[col_name] = scaled_col.fillna(original_col)
            else:
                logger.warning(f"User trade amount for Option {i+1} is 0. Greeks not scaled.")

            # Ensure all RESULT_TABLE_COLUMNS are present
            for col_info in RESULT_TABLE_COLUMNS: 
                if col_info['id'] not in current_option_df.columns:
                    current_option_df[col_info['id']] = "N/A"
            
            # Format numerical columns (Greeks) for display
            for col_name in ['DV01 Gamma', 'Theta', 'Vega']: 
                if col_name in current_option_df.columns:
                    current_option_df[col_name] = current_option_df[col_name].apply(
                        lambda x: f"{x:.2f}" if pd.notna(x) and isinstance(x, (int, float)) else ("N/A" if pd.isna(x) else str(x))
                    )
            
            ordered_column_ids = [col['id'] for col in RESULT_TABLE_COLUMNS]
            current_option_df_for_ui = current_option_df[ordered_column_ids]

            table_for_option = DataTable(
                id=f"results-datatable-option-{i}", # Unique ID for each table
                data=current_option_df_for_ui.to_dict('records'), 
                columns=RESULT_TABLE_COLUMNS, 
                theme=default_theme, 
                page_size=10, # Or adjust as needed, maybe more if side-by-side and short
                style_table={'minWidth': '100%', 'marginTop': '10px'}, 
                style_header={'backgroundColor': default_theme.panel_bg, 'fontWeight': 'bold', 'color': default_theme.text_light, 'fontSize':'0.75rem'}, 
                style_cell={'backgroundColor': default_theme.base_bg, 'color': default_theme.text_light, 'textAlign': 'left', 'padding': '8px', 'fontSize':'0.7rem'},
            ).render()
            option_display_elements.append(table_for_option)
        
        # Add this option's block (desc, amount, table) to a Bootstrap column
        # CORRECTED: Changed default_theme.secondary_alt to default_theme.secondary
        all_option_display_blocks.append(dbc.Col(option_display_elements, width=col_width, style={'padding':'10px', 'border':f'1px solid {default_theme.secondary}', 'borderRadius':'5px', 'margin':'5px'}))

    if not all_option_display_blocks: # Should not happen if ui_options_data was populated
        return [html.P("No data to display.", style=text_style)]

    return [dbc.Row(all_option_display_blocks)] # Return a list containing one dbc.Row
    # --- END MODIFIED DISPLAY LOGIC ---

# --- End Callbacks ---

if __name__ == "__main__":
    logger.info("Starting Dashboard...")
    app.run(debug=True, port=8052, use_reloader=False)
