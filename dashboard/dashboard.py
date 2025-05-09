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
    # ComboBox and Graph are already imported from your file.
    from src.components import Tabs, Grid, Button, ComboBox, Container, DataTable, Graph 
    print("Successfully imported uikitxv2 logging, theme, and UI components from 'src'.")
    from src.PricingMonkey.pMoneyAuto import run_pm_automation 
    from src.PricingMonkey.pMoneyMovement import get_market_movement_data_df
    print("Successfully imported PM modules from 'src.PricingMonkey'.")
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
        html.Div([
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
            
            html.Div([
                html.P("Market Movement +/-:", style=text_style),
                dcc.Input(
                    id="analysis-market-movement-input",
                    type="number",
                    placeholder="e.g. 10 for +10bps",
                    style=input_style_dcc
                )
            ], style={'flex': '1', 'marginRight': '15px'}),
            
            html.Div([
                html.P("\u00A0", style=text_style), # Non-breaking space to align button with inputs
                Button(
                    label="Refresh Data",
                    id="analysis-refresh-button",
                    theme=default_theme,
                    n_clicks=0
                ).render()
            ], style={'flex': '0 0 auto', 'alignSelf': 'flex-end', 'marginBottom': '5px'})
        ], style={'display': 'flex', 'marginBottom': '20px', 'alignItems': 'flex-end'}),
        
        # Empty graph area with consistent styling
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
    style={'padding': '15px'}
).render()

main_tabs_rendered = Tabs(
    id="main-dashboard-tabs",
    tabs=[
        ("Pricing Monkey Setup", pricing_monkey_tab_main_container_rendered),
        ("Analysis", analysis_tab_content)
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
    Input("analysis-refresh-button", "n_clicks"),
    Input("analysis-y-axis-selector", "value"),
    State("market-movement-data-store", "data"),
    prevent_initial_call=True
)
def handle_analysis_interactions(refresh_clicks, selected_y_axis, stored_data):
    """Unified callback to handle all Analysis tab interactions"""
    # Determine which input triggered the callback
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
    
    # Default values
    data_json = stored_data
    fig = go.Figure()
    
    # Handle refresh button click
    if trigger_id == "analysis-refresh-button" and refresh_clicks:
        logger.info("Refresh Data button clicked. Fetching market movement data...")
        try:
            # Get market movement data
            df = get_market_movement_data_df()
            
            if df.empty:
                logger.warning("Retrieved empty DataFrame from market movement data")
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
                return None, fig
            
            logger.info(f"Successfully retrieved market data with shape: {df.shape}")
            # Use current y-axis selection or default
            y_axis = selected_y_axis or "Implied Vol (Daily BP)"
            fig = create_analysis_graph(df, y_axis)
            data_json = df.to_json(date_format='iso', orient='split')
            
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
            return None, fig
    
    # Handle y-axis selection change
    elif trigger_id == "analysis-y-axis-selector" and selected_y_axis and stored_data:
        try:
            df = pd.read_json(stored_data, orient='split')
            fig = create_analysis_graph(df, selected_y_axis)
        except Exception as e:
            logger.error(f"Error updating analysis graph: {str(e)}", exc_info=True)
            fig.update_layout(
                title="Error updating graph",
                xaxis_title="Strike",
                yaxis_title=selected_y_axis,
                annotations=[dict(text=f"Error: {str(e)[:100]}...", showarrow=False, xref="paper", yref="paper", x=0.5, y=0.5)],
                paper_bgcolor=default_theme.panel_bg,
                plot_bgcolor=default_theme.base_bg,
                font_color=default_theme.text_light,
                xaxis=dict(showgrid=True, gridcolor=default_theme.secondary),
                yaxis=dict(showgrid=True, gridcolor=default_theme.secondary)
            )
    
    return data_json, fig

def create_analysis_graph(df, y_axis_column):
    """Helper function to create the analysis graph figure"""
    fig = go.Figure()
    
    # Check if both Strike and the selected Y-axis column exist
    if "Strike" in df.columns and y_axis_column in df.columns:
        # Get appropriate label for the y-axis based on predefined options
        y_axis_options = [
            {"label": "Implied Vol", "value": "Implied Vol (Daily BP)"},
            {"label": "Delta (%)", "value": "%Delta"},
            {"label": "Vega", "value": "Vega"},
            {"label": "Gamma", "value": "DV01 Gamma"},
            {"label": "Theta", "value": "Theta"},
        ]
        y_axis_label = next((item["label"] for item in y_axis_options if item["value"] == y_axis_column), y_axis_column)
        
        # Get the data for plotting
        x_data = df["Strike"]
        y_data = df[y_axis_column]
        
        # Add the scatter trace to the figure
        fig.add_trace(go.Scatter(
            x=x_data,
            y=y_data,
            mode='lines+markers',
            marker=dict(color=default_theme.primary, size=8, line=dict(color=default_theme.accent, width=1)),
            line=dict(color=default_theme.accent, width=2)
        ))
        
        # Update layout
        fig.update_layout(
            title=f"{y_axis_label} vs Strike",
            xaxis_title="Strike",
            yaxis_title=y_axis_label,
            paper_bgcolor=default_theme.panel_bg,
            plot_bgcolor=default_theme.base_bg,
            font_color=default_theme.text_light,
            xaxis=dict(showgrid=True, gridcolor=default_theme.secondary),
            yaxis=dict(showgrid=True, gridcolor=default_theme.secondary),
            height=400
        )
    else:
        # Create an empty figure with a message if columns are missing
        missing_cols = []
        if "Strike" not in df.columns:
            missing_cols.append("Strike")
        if y_axis_column not in df.columns:
            missing_cols.append(y_axis_column)
            
        fig.update_layout(
            title=f"Data columns missing: {', '.join(missing_cols)}",
            xaxis_title="Strike",
            yaxis_title=y_axis_column,
            paper_bgcolor=default_theme.panel_bg,
            plot_bgcolor=default_theme.base_bg,
            font_color=default_theme.text_light,
            xaxis=dict(showgrid=True, gridcolor=default_theme.secondary),
            yaxis=dict(showgrid=True, gridcolor=default_theme.secondary),
            height=400
        )
    
    return fig

# --- End Callbacks ---

if __name__ == "__main__":
    logger.info("Starting Dashboard...")
    app.run(debug=True, port=8052, use_reloader=False)
