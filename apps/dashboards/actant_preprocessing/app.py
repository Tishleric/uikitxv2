"""
Actant Preprocessing Dashboard - Bond Future Options Greek Analysis
Phase 2: Interactive parameter inputs with real-time Greek recalculation
"""

import dash
from dash import html, dcc, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
import os
import sys
import numpy as np

# --- Path Setup ---
current_dir = os.path.dirname(os.path.abspath(__file__))
# Go up 3 levels from apps/dashboards/actant_preprocessing to reach project root
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
lib_path = os.path.join(project_root, 'lib')

if project_root not in sys.path:
    sys.path.insert(0, project_root)
if lib_path not in sys.path:
    sys.path.insert(0, lib_path)

# --- Imports ---
from components import Container, Grid, Graph, Button, ComboBox, DataTable, Loading
from components.themes import default_theme
from trading.bond_future_options import (
    BondFutureOption, 
    analyze_bond_future_option_greeks, 
    calculate_all_greeks,
    generate_greek_profiles
)
from trading.bond_future_options.greek_validator import GreekPnLValidator
from trading.bond_future_options.bachelier_greek import generate_greek_profiles_data

# --- Initialize Dash App ---
assets_folder_path = os.path.join(project_root, 'assets')
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    assets_folder=assets_folder_path
)
app.title = "BFO Greek Analysis"

# --- Helper Functions ---
def create_greek_graph(df, greek_col, title, strike_price, current_f=None):
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

def create_comprehensive_greeks_table(current_greeks):
    """Create a comprehensive table showing all Greeks at current market point"""
    # Define the Greeks to display in order
    greek_order = [
        ('delta_F', 'Delta (F-Space)', False),
        ('delta_y', 'Delta (Y-Space)', True),
        ('gamma_F', 'Gamma (F-Space)', False),
        ('gamma_y', 'Gamma (Y-Space)', True),
        ('vega_price', 'Vega (Price)', False),
        ('vega_y', 'Vega (Y-Space)', True),
        ('theta_F', 'Theta (F-Space)', True),
        ('volga_price', 'Volga (Price)', True),
        ('vanna_F_price', 'Vanna (F-Price)', True),
        ('charm_F', 'Charm (F)', True),
        ('speed_F', 'Speed (F)', True),
        ('color_F', 'Color (F)', True),
        ('ultima', 'Ultima', True),
        ('zomma', 'Zomma', True)
    ]
    
    # Create table data
    table_data = []
    for greek_key, greek_name, is_scaled in greek_order:
        if greek_key in current_greeks:
            value = current_greeks[greek_key]
            # Note if the Greek is scaled
            scaled_note = " (×1000)" if is_scaled else ""
            table_data.append({
                'Greek': greek_name + scaled_note,
                'Value': f"{value:.6f}"
            })
    
    return DataTable(
        id="comprehensive-greeks-table",
        data=table_data,
        columns=[
            {"name": "Greek", "id": "Greek"},
            {"name": "Value", "id": "Value"}
        ],
        theme=default_theme,
        style_cell={
            'backgroundColor': default_theme.base_bg,
            'color': default_theme.text_light,
            'textAlign': 'left',
            'padding': '8px',
            'border': f'1px solid {default_theme.secondary}'
        },
        style_header={
            'backgroundColor': default_theme.panel_bg,
            'fontWeight': 'bold',
            'color': default_theme.primary
        },
        style_data_conditional=[
            {
                'if': {'column_id': 'Value'},
                'textAlign': 'right',
                'fontFamily': 'monospace'
            }
        ],
        page_size=20,
        style_table={'height': '400px', 'overflowY': 'auto', 'width': '100%'}
    ).render()

def create_parameter_inputs():
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
        id="parameter-inputs-grid",
        children=[
            # Row 1: Strike, Future Price, Days to Expiry
            (html.Div([
                html.Label("Strike Price", style=label_style),
                dcc.Input(id="strike-input", type="number", value=110.75, step=0.01, style=input_style)
            ]), {"width": 4}),
            (html.Div([
                html.Label("Future Price", style=label_style),
                dcc.Input(id="future-price-input", type="number", value=110.789062, step=0.01, style=input_style)
            ]), {"width": 4}),
            (html.Div([
                html.Label("Days to Expiry", style=label_style),
                dcc.Input(id="days-to-expiry-input", type="number", value=4.7, step=0.1, style=input_style)
            ]), {"width": 4}),
            
            # Row 2: Market Price, DV01, Convexity
            (html.Div([
                html.Label("Market Price (64ths)", style=label_style),
                dcc.Input(id="market-price-input", type="number", value=23, step=1, style=input_style)
            ]), {"width": 4}),
            (html.Div([
                html.Label("Future DV01", style=label_style),
                dcc.Input(id="dv01-input", type="number", value=0.063, step=0.001, style=input_style)
            ]), {"width": 4}),
            (html.Div([
                html.Label("Future Convexity", style=label_style),
                dcc.Input(id="convexity-input", type="number", value=0.002404, step=0.000001, style=input_style)
            ]), {"width": 4}),
            
            # Row 3: Option Type and Implied Vol
            (html.Div([
                html.Label("Option Type", style=label_style),
                ComboBox(
                    id="option-type-selector",
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
                    id="implied-vol-display",
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
                    id="recalculate-button",
                    theme=default_theme,
                    n_clicks=0,
                    style={'width': '100%'}
                ).render()
            ]), {"width": 4}),
            
            # Row 4: Taylor Order Selector and Validation Metrics
            (html.Div([
                html.Label("Taylor Order", style=label_style),
                ComboBox(
                    id="taylor-order-selector",
                    options=[
                        {"label": "1st Order", "value": 1},
                        {"label": "2nd Order", "value": 2},
                        {"label": "3rd Order", "value": 3}
                    ],
                    value=2,
                    theme=default_theme,
                    clearable=False
                ).render()
            ]), {"width": 4}),
            (html.Div([
                html.Label("PnL Validation R²", style=label_style),
                html.Div(
                    id="r-squared-display",
                    style={
                        **input_style,
                        'padding': '7px',
                        'backgroundColor': default_theme.base_bg,
                        'fontWeight': 'bold',
                        'color': default_theme.accent
                    }
                )
            ]), {"width": 4}),
            (html.Div([
                html.Label("RMSE", style=label_style),
                html.Div(
                    id="rmse-display",
                    style={
                        **input_style,
                        'padding': '7px',
                        'backgroundColor': default_theme.base_bg,
                        'fontWeight': 'bold',
                        'color': default_theme.warning
                    }
                )
            ]), {"width": 4})
        ],
        theme=default_theme
    )

def create_greek_table(df, greek_col, title, current_f, strike):
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
        id=f"{greek_col}-table",
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

def create_comprehensive_greeks_table(current_greeks):
    """Create a comprehensive table showing all Greeks at current market point"""
    # Define the Greeks to display in order
    greek_order = [
        ('delta_F', 'Delta (F-Space)', False),
        ('delta_y', 'Delta (Y-Space)', True),
        ('gamma_F', 'Gamma (F-Space)', False),
        ('gamma_y', 'Gamma (Y-Space)', True),
        ('vega_price', 'Vega (Price)', False),
        ('vega_y', 'Vega (Y-Space)', True),
        ('theta_F', 'Theta (F-Space)', True),
        ('volga_price', 'Volga (Price)', True),
        ('vanna_F_price', 'Vanna (F-Price)', True),
        ('charm_F', 'Charm (F)', True),
        ('speed_F', 'Speed (F)', True),
        ('color_F', 'Color (F)', True),
        ('ultima', 'Ultima', True),
        ('zomma', 'Zomma', True)
    ]
    
    # Create table data
    table_data = []
    for greek_key, greek_name, is_scaled in greek_order:
        if greek_key in current_greeks:
            value = current_greeks[greek_key]
            # Note if the Greek is scaled
            scaled_note = " (×1000)" if is_scaled else ""
            table_data.append({
                'Greek': greek_name + scaled_note,
                'Value': f"{value:.6f}"
            })
    
    return DataTable(
        id="comprehensive-greeks-table",
        data=table_data,
        columns=[
            {"name": "Greek", "id": "Greek"},
            {"name": "Value", "id": "Value"}
        ],
        theme=default_theme,
        style_cell={
            'backgroundColor': default_theme.base_bg,
            'color': default_theme.text_light,
            'textAlign': 'left',
            'padding': '8px',
            'border': f'1px solid {default_theme.secondary}'
        },
        style_header={
            'backgroundColor': default_theme.panel_bg,
            'fontWeight': 'bold',
            'color': default_theme.primary
        },
        style_data_conditional=[
            {
                'if': {'column_id': 'Value'},
                'textAlign': 'right',
                'fontFamily': 'monospace'
            }
        ],
        page_size=20,
        style_table={'height': '400px', 'overflowY': 'auto', 'width': '100%'}
    ).render()

# --- Layout Definition ---
app.layout = html.Div([
    # Header
    html.H1(
        "Bond Future Options - Greek Analysis",
        style={
            "textAlign": "center",
            "color": default_theme.primary,
            "padding": "20px 0",
            "marginBottom": "20px"
        }
    ),
    
    # Store for Greek profiles data
    dcc.Store(id="greek-profiles-store"),
    # Store for validation metrics
    dcc.Store(id="validation-metrics-store"),
    
    # Main Container
    Container(
        id="main-container",
        children=[
            # Parameters Section
            html.Div([
                html.H4("Option Parameters", style={"color": default_theme.primary, "marginBottom": "20px"}),
                create_parameter_inputs().render()
            ], style={"marginBottom": "30px"}),
            
            # Comprehensive Greeks Table Section
            html.Div([
                html.H4("Current Greeks at Market Point", style={"color": default_theme.primary, "marginBottom": "20px"}),
                html.Div(id="comprehensive-greeks-container", style={"marginBottom": "20px"})
            ], style={"marginBottom": "30px"}),
            
            # Toggle Buttons (Graph/Table view)
            html.Div([
                html.Div([
                    Button(
                        label="Graph View",
                        id="view-mode-graph-btn",
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
                        id="view-mode-table-btn",
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
            
            # Graph View Container
            html.Div(
                id="graph-view-container",
                children=[
                    Loading(
                        id="graph-loading",
                        children=[
                            Grid(
                                id="greek-graphs-grid",
                                children=[
                                    # Graphs will be updated by callback
                                    (html.Div(id="delta-graph-container"), {"width": 6}),
                                    (html.Div(id="gamma-graph-container"), {"width": 6}),
                                    (html.Div(id="vega-graph-container"), {"width": 6}),
                                    (html.Div(id="theta-graph-container"), {"width": 6}),
                                    (html.Div(id="ultima-graph-container"), {"width": 6}),
                                    (html.Div(id="zomma-graph-container"), {"width": 6})
                                ],
                                theme=default_theme
                            ).render()
                        ],
                        type="circle",
                        theme=default_theme
                    ).render()
                ],
                style={"display": "block"}
            ),
            
            # Table View Container
            html.Div(
                id="table-view-container",
                children=[
                    Loading(
                        id="table-loading",
                        children=[
                            html.Div(id="greek-table-container")
                        ],
                        type="circle",
                        theme=default_theme
                    ).render()
                ],
                style={"display": "none"}
            ),
            
            # Greek Profile Analysis Section
            html.Div([
                html.Hr(style={"borderColor": default_theme.secondary, "margin": "30px 0"}),
                html.H4("Greek Profile Analysis", style={"color": default_theme.primary, "marginBottom": "20px"}),
                html.P("Analytical Greek profiles across future price scenarios", 
                       style={"color": default_theme.text_subtle, "marginBottom": "20px"}),
                
                # Profile graphs container
                Loading(
                    id="profile-loading",
                    children=[
                        Grid(
                            id="greek-profiles-grid",
                            children=[
                                # Delta and Gamma profiles
                                (html.Div(id="profile-delta-container"), {"width": 6}),
                                (html.Div(id="profile-gamma-container"), {"width": 6}),
                                # Vega and Theta profiles
                                (html.Div(id="profile-vega-container"), {"width": 6}),
                                (html.Div(id="profile-theta-container"), {"width": 6}),
                                # Volga and Speed profiles (optional row)
                                (html.Div(id="profile-volga-container"), {"width": 6}),
                                (html.Div(id="profile-speed-container"), {"width": 6})
                            ],
                            theme=default_theme
                        ).render()
                    ],
                    type="circle",
                    theme=default_theme
                ).render()
            ], style={"marginTop": "30px"})
        ],
        theme=default_theme
    ).render()
], style={"backgroundColor": default_theme.base_bg, "minHeight": "100vh"})

# --- Callbacks ---
@app.callback(
    [Output("greek-profiles-store", "data"),
     Output("implied-vol-display", "children"),
     Output("delta-graph-container", "children"),
     Output("gamma-graph-container", "children"),
     Output("vega-graph-container", "children"),
     Output("theta-graph-container", "children"),
     Output("ultima-graph-container", "children"),
     Output("zomma-graph-container", "children"),
     Output("greek-table-container", "children"),
     Output("comprehensive-greeks-container", "children"),
     Output("validation-metrics-store", "data"),
     Output("r-squared-display", "children"),
     Output("rmse-display", "children"),
     # Add outputs for Greek profile graphs
     Output("profile-delta-container", "children"),
     Output("profile-gamma-container", "children"),
     Output("profile-vega-container", "children"),
     Output("profile-theta-container", "children"),
     Output("profile-volga-container", "children"),
     Output("profile-speed-container", "children")],
    [Input("recalculate-button", "n_clicks"),
     Input("taylor-order-selector", "value")],
    [State("strike-input", "value"),
     State("future-price-input", "value"),
     State("days-to-expiry-input", "value"),
     State("market-price-input", "value"),
     State("dv01-input", "value"),
     State("convexity-input", "value"),
     State("option-type-selector", "value")]
)
def update_greek_analysis(n_clicks, taylor_order, strike, future_price, days_to_expiry, market_price_64ths,
                         dv01, convexity, option_type):
    """Recalculate Greeks based on input parameters"""
    
    # Convert market price from 64ths to decimal
    market_price = market_price_64ths / 64.0
    
    # Convert days to expiry to years
    T = days_to_expiry / 252.0
    
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
    
    # Create the graphs
    delta_graph = Graph(
        id="delta-graph",
        figure=create_greek_graph(df_profiles, 'delta_y', 'Delta Profile (Y-Space)', strike, future_price),
        theme=default_theme
    ).render()
    
    gamma_graph = Graph(
        id="gamma-graph",
        figure=create_greek_graph(df_profiles, 'gamma_y', 'Gamma Profile (Y-Space)', strike, future_price),
        theme=default_theme
    ).render()
    
    vega_graph = Graph(
        id="vega-graph",
        figure=create_greek_graph(df_profiles, 'vega_y', 'Vega Profile (Y-Space)', strike, future_price),
        theme=default_theme
    ).render()
    
    theta_graph = Graph(
        id="theta-graph",
        figure=create_greek_graph(df_profiles, 'theta_F', 'Theta Profile (F-Space)', strike, future_price),
        theme=default_theme
    ).render()
    
    ultima_graph = Graph(
        id="ultima-graph",
        figure=create_greek_graph(df_profiles, 'ultima', 'Ultima Profile (∂³V/∂σ³)', strike, future_price),
        theme=default_theme
    ).render()
    
    zomma_graph = Graph(
        id="zomma-graph",
        figure=create_greek_graph(df_profiles, 'zomma', 'Zomma Profile (∂³V/∂F²∂σ)', strike, future_price),
        theme=default_theme
    ).render()
    
    # Create the table view with 3x2 grid of Greek tables (now including ultima and zomma)
    greek_tables_grid = Grid(
        id="greek-tables-grid",
        children=[
            # Row 1: Delta and Gamma tables
            (create_greek_table(df_profiles, 'delta_y', 'Delta Profile (Y-Space)', future_price, strike), {"width": 6}),
            (create_greek_table(df_profiles, 'gamma_y', 'Gamma Profile (Y-Space)', future_price, strike), {"width": 6}),
            # Row 2: Vega and Theta tables
            (create_greek_table(df_profiles, 'vega_y', 'Vega Profile (Y-Space)', future_price, strike), {"width": 6}),
            (create_greek_table(df_profiles, 'theta_F', 'Theta Profile (F-Space)', future_price, strike), {"width": 6}),
            # Row 3: Ultima and Zomma tables
            (create_greek_table(df_profiles, 'ultima', 'Ultima Profile', future_price, strike), {"width": 6}),
            (create_greek_table(df_profiles, 'zomma', 'Zomma Profile', future_price, strike), {"width": 6})
        ],
        theme=default_theme
    ).render()
    
    # Create comprehensive Greeks table
    comprehensive_greeks_table = create_comprehensive_greeks_table(current_greeks)
    
    # Calculate validation metrics using GreekPnLValidator
    validator = GreekPnLValidator(results['model'])
    validation_results = validator.run_validation(
        F=future_price,
        K=strike,
        t=T,  # Note: parameter is lowercase 't'
        sigma=implied_vol,
        option_type=option_type,
        n_samples=100  # Quick validation for dashboard
    )
    
    # Extract metrics for the selected Taylor order
    if taylor_order == 1:
        metrics = validation_results['stats_by_order'][1]
    elif taylor_order == 2:
        metrics = validation_results['stats_by_order'][2]
    else:  # taylor_order == 3
        metrics = validation_results['stats_by_order'][3]
    
    r_squared_display = f"{metrics['r_squared']:.3f}"
    rmse_display = f"{metrics['rmse']:.4f}"
    
    # Store validation data
    validation_data = {
        'stats_by_order': validation_results['stats_by_order'],
        'current_order': taylor_order,
        'contributions': validation_results['contributions']
    }
    
    # Generate Greek profiles using bachelier_greek.py
    profile_data = generate_greek_profiles_data(
        K=strike,
        sigma=implied_vol,
        tau=T,
        F_range=(future_price - 10, future_price + 10),
        num_points=100
    )
    
    # Create profile graphs
    def create_profile_graph(greek_name, title):
        """Create a Greek profile graph from bachelier_greek data"""
        fig = go.Figure()
        
        # Add the analytical Greek profile
        fig.add_trace(go.Scatter(
            x=profile_data['F_vals'],
            y=profile_data['greeks_ana'][greek_name],
            mode='lines',
            name='Analytical',
            line=dict(color=default_theme.primary, width=2)
        ))
        
        # Add vertical lines for current price and strike
        fig.add_vline(x=future_price, line_dash="dash", line_color=default_theme.success,
                      annotation_text="Current", annotation_position="top")
        fig.add_vline(x=strike, line_dash="dot", line_color=default_theme.danger,
                      annotation_text="Strike", annotation_position="top")
        
        # Update layout
        fig.update_layout(
            title=title,
            xaxis_title="Future Price",
            yaxis_title="Greek Value",
            template="plotly_dark",
            paper_bgcolor=default_theme.base_bg,
            plot_bgcolor=default_theme.panel_bg,
            font=dict(color=default_theme.text_light),
            showlegend=False
        )
        
        return fig
    
    # Create profile graphs for each Greek
    profile_delta = Graph(
        id="profile-delta-graph",
        figure=create_profile_graph('delta', 'Delta Profile'),
        theme=default_theme
    ).render()
    
    profile_gamma = Graph(
        id="profile-gamma-graph",
        figure=create_profile_graph('gamma', 'Gamma Profile'),
        theme=default_theme
    ).render()
    
    profile_vega = Graph(
        id="profile-vega-graph",
        figure=create_profile_graph('vega', 'Vega Profile'),
        theme=default_theme
    ).render()
    
    profile_theta = Graph(
        id="profile-theta-graph",
        figure=create_profile_graph('theta', 'Theta Profile'),
        theme=default_theme
    ).render()
    
    profile_volga = Graph(
        id="profile-volga-graph",
        figure=create_profile_graph('volga', 'Volga Profile'),
        theme=default_theme
    ).render()
    
    profile_speed = Graph(
        id="profile-speed-graph",
        figure=create_profile_graph('speed', 'Speed Profile'),
        theme=default_theme
    ).render()
    
    # Store data for potential export
    store_data = {
        'profiles': df_profiles.to_dict('records'),
        'current_greeks': current_greeks,
        'parameters': {
            'strike': strike,
            'future_price': future_price,
            'days_to_expiry': days_to_expiry,
            'option_type': option_type,
            'implied_vol': implied_vol
        }
    }
    
    return (store_data, vol_display, delta_graph, gamma_graph, vega_graph, theta_graph, 
            ultima_graph, zomma_graph, greek_tables_grid, comprehensive_greeks_table,
            validation_data, r_squared_display, rmse_display,
            # Greek profile graphs
            profile_delta, profile_gamma, profile_vega, profile_theta, profile_volga, profile_speed)

@app.callback(
    [Output("graph-view-container", "style"),
     Output("table-view-container", "style"),
     Output("view-mode-graph-btn", "style"),
     Output("view-mode-table-btn", "style")],
    [Input("view-mode-graph-btn", "n_clicks"),
     Input("view-mode-table-btn", "n_clicks")],
    prevent_initial_call=True
)
def toggle_view_mode(graph_clicks, table_clicks):
    """Toggle between graph and table views"""
    ctx = callback_context
    if not ctx.triggered:
        # Default to graph view
        return (
            {"display": "block"}, {"display": "none"},
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
    
    if triggered_id == "view-mode-graph-btn":
        # Show graph view
        return (
            {"display": "block"}, {"display": "none"},
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
        # Show table view
        return (
            {"display": "none"}, {"display": "block"},
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

# Trigger initial calculation on load
@app.callback(
    Output("recalculate-button", "n_clicks"),
    Input("main-container", "id"),
    prevent_initial_call=False
)
def trigger_initial_calculation(container_id):
    """Trigger calculation on page load"""
    return 1

if __name__ == "__main__":
    app.run(debug=True, port=8053) 