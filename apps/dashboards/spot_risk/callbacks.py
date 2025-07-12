"""Spot Risk Dashboard Callbacks

This module handles all callback logic for the Spot Risk dashboard.
Follows the Controller layer of MVC pattern - business logic and data flow.
"""

import dash
from dash import Input, Output, State, callback, no_update, dash_table, html
from dash.exceptions import PreventUpdate
import logging
from typing import List, Dict, Any, Tuple
import pandas as pd

from lib.monitoring.decorators import monitor
from lib.components.themes.colour_palette import default_theme
from lib.components.advanced.graph import Graph
from .controller import SpotRiskController
from .views import get_column_definitions

logger = logging.getLogger(__name__)
default_theme = default_theme


def create_greek_profile_graph(greek_name: str, strikes: List[float], values: List[float], 
                               positions: List[Dict], atm_strike: float) -> Dict:
    """Create a Plotly figure for a single Greek profile
    
    Args:
        greek_name: Name of the Greek (e.g., 'delta', 'gamma')
        strikes: List of strike prices for x-axis
        values: List of Greek values for y-axis
        positions: List of position dicts with strike, position size, type
        atm_strike: ATM strike value for vertical marker
        
    Returns:
        Dict: Plotly figure dict
    """
    from plotly import graph_objects as go
    
    # Debug logging
    logger.info(f"Creating graph for {greek_name} with ATM strike: {atm_strike}")
    logger.info(f"[DEBUG GRAPH INPUT] Values range: [{min(values) if values else 'N/A':.6f}, {max(values) if values else 'N/A':.6f}]")
    logger.info(f"[DEBUG GRAPH INPUT] First 5 values: {values[:5] if values else 'No values'}")
    
    # Create figure
    fig = go.Figure()
    
    # Add Greek profile line
    fig.add_trace(go.Scatter(
        x=strikes,
        y=values,
        mode='lines',
        name=f'{greek_name.capitalize()} Profile',
        line=dict(color=default_theme.primary, width=2),
        hovertemplate='Strike: %{x:.2f}<br>%{text}: %{y:.4f}<extra></extra>',
        text=[greek_name.capitalize()] * len(strikes)
    ))
    
    # Add position markers
    if positions:
        position_strikes = []
        position_values = []
        position_sizes = []
        position_texts = []
        
        # Find Greek value at each position strike
        for pos in positions:
            strike = pos['strike']
            # Find closest strike in profile
            closest_idx = min(range(len(strikes)), key=lambda i: abs(strikes[i] - strike))
            if abs(strikes[closest_idx] - strike) < 0.5:  # Within reasonable range
                position_strikes.append(strike)
                position_values.append(values[closest_idx])
                # Scale position size for visibility (minimum size 10)
                position_size = max(10, abs(pos['position']) / 10)
                position_sizes.append(position_size)
                position_texts.append(
                    f"{pos['key']}<br>"
                    f"Type: {pos['type']}<br>"
                    f"Position: {pos['position']:.0f}<br>"
                    f"{greek_name.capitalize()}: {pos['current_greeks'].get(greek_name, 0):.4f}"
                )
        
        if position_strikes:
            # Log position strikes for debugging
            logger.info(f"Position strikes on graph: {position_strikes}")
            fig.add_trace(go.Scatter(
                x=position_strikes,
                y=position_values,
                mode='markers',
                name='Positions',
                marker=dict(
                    size=position_sizes,
                    color=default_theme.accent,
                    symbol='triangle-up',
                    line=dict(width=1, color=default_theme.base_bg)
                ),
                hovertemplate='%{text}<extra></extra>',
                text=position_texts
            ))
    
    # Add ATM strike vertical line
    logger.info(f"Adding ATM vertical line at x={atm_strike}")
    fig.add_vline(
        x=atm_strike,
        line_dash="dash",
        line_color=default_theme.danger,
        annotation_text="ATM",
        annotation_position="top"
    )
    
    # Update layout
    fig.update_layout(
        title=dict(
            text=f'{greek_name.capitalize()} Profile',
            font=dict(size=16, color=default_theme.text_light)
        ),
        xaxis=dict(
            title='Strike Price',
            color=default_theme.text_light,
            gridcolor=default_theme.secondary,
            zeroline=False
        ),
        yaxis=dict(
            title=f'{greek_name.capitalize()} Value',
            color=default_theme.text_light,
            gridcolor=default_theme.secondary,
            zeroline=True,
            zerolinecolor=default_theme.secondary
        ),
        plot_bgcolor=default_theme.base_bg,
        paper_bgcolor=default_theme.panel_bg,
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            x=0.02,
            y=0.98,
            bgcolor='rgba(0,0,0,0)',
            font=dict(color=default_theme.text_light)
        ),
        height=400,
        margin=dict(l=60, r=20, t=60, b=50)
    )
    
    return fig.to_dict()


def create_aggregate_greek_graph(greek_name: str, profiles_by_expiry: Dict[str, Dict[str, Any]], 
                                 greek_space: str = 'F') -> Dict:
    """Create a Plotly figure showing all expiries for a single Greek
    
    Args:
        greek_name: Name of the Greek (e.g., 'delta', 'gamma')
        profiles_by_expiry: Dict with expiry as key containing strikes, greeks, positions, etc.
        greek_space: Greek space ('F' or 'y') for display
        
    Returns:
        Dict: Plotly figure dict
    """
    from plotly import graph_objects as go
    
    logger.info(f"Creating aggregate graph for {greek_name} with {len(profiles_by_expiry)} expiries")
    
    # Create figure
    fig = go.Figure()
    
    # Color palette for different expiries
    color_palette = [
        default_theme.primary,      # Blue
        default_theme.accent,       # Teal/Green
        default_theme.danger,       # Red
        '#FF8C00',                  # Dark Orange
        '#9370DB',                  # Medium Purple
        '#20B2AA',                  # Light Sea Green
        '#FF1493',                  # Deep Pink
        '#32CD32',                  # Lime Green
        '#4169E1',                  # Royal Blue
        '#FFD700',                  # Gold
    ]
    
    # Sort expiries for consistent display
    sorted_expiries = sorted(profiles_by_expiry.keys())
    
    # Track global ATM (should be same for all expiries)
    global_atm = None
    
    # Plot each expiry's profile
    for idx, expiry in enumerate(sorted_expiries):
        profile_data = profiles_by_expiry[expiry]
        
        # Get color for this expiry (cycle if more expiries than colors)
        color = color_palette[idx % len(color_palette)]
        
        # Extract data
        strikes = profile_data['strikes']
        if greek_name not in profile_data['greeks']:
            logger.warning(f"Greek {greek_name} not found for expiry {expiry}")
            continue
            
        values = profile_data['greeks'][greek_name]
        positions = profile_data['positions']
        atm_strike = profile_data['atm_strike']
        
        # Set global ATM from first expiry
        if global_atm is None:
            global_atm = atm_strike
        
        # Determine Greek display name with space suffix
        greek_column_map = {
            'delta': f'delta_{greek_space}',
            'gamma': f'gamma_{greek_space}',
            'vega': 'vega_price' if greek_space == 'F' else f'vega_{greek_space}',
            'theta': f'theta_{greek_space}',
            'volga': 'volga_price',
            'vanna': f'vanna_{greek_space}_price',
            'charm': f'charm_{greek_space}',
            'speed': f'speed_{greek_space}',
            'color': f'color_{greek_space}',
            'ultima': 'ultima',
            'zomma': 'zomma'
        }
        
        # Get display suffix
        actual_column = greek_column_map.get(greek_name, greek_name)
        display_suffix = ''
        if '_F' in actual_column:
            display_suffix = '_F'
        elif '_y' in actual_column:
            display_suffix = '_y'
        elif actual_column == 'vega_price':
            display_suffix = '_price'
        
        greek_display_name = f'{greek_name}{display_suffix}'
        
        # Add Greek profile line for this expiry
        fig.add_trace(go.Scatter(
            x=strikes,
            y=values,
            mode='lines',
            name=f'{expiry}',
            line=dict(color=color, width=2),
            hovertemplate=f'{expiry}<br>Strike: %{{x:.2f}}<br>{greek_display_name}: %{{y:.4f}}<extra></extra>',
            legendgroup=expiry
        ))
        
        # Add position markers for this expiry
        if positions:
            position_strikes = []
            position_values = []
            position_sizes = []
            position_texts = []
            
            # Find Greek value at each position strike
            for pos in positions:
                strike = pos['strike']
                # Find closest strike in profile
                closest_idx = min(range(len(strikes)), key=lambda i: abs(strikes[i] - strike))
                if abs(strikes[closest_idx] - strike) < 0.5:  # Within reasonable range
                    position_strikes.append(strike)
                    position_values.append(values[closest_idx])
                    # Scale position size for visibility (minimum size 10)
                    position_size = max(10, abs(pos['position']) / 10)
                    position_sizes.append(position_size)
                    position_texts.append(
                        f"{expiry}<br>"
                        f"{pos['key']}<br>"
                        f"Type: {pos['type']}<br>"
                        f"Position: {pos['position']:.0f}<br>"
                        f"{greek_display_name}: {pos['current_greeks'].get(greek_name, 0):.4f}"
                    )
            
            if position_strikes:
                fig.add_trace(go.Scatter(
                    x=position_strikes,
                    y=position_values,
                    mode='markers',
                    name=f'{expiry} Positions',
                    marker=dict(
                        size=position_sizes,
                        color=color,
                        symbol='triangle-up',
                        line=dict(width=1, color=default_theme.base_bg)
                    ),
                    hovertemplate='%{text}<extra></extra>',
                    text=position_texts,
                    showlegend=False,  # Don't clutter legend with position entries
                    legendgroup=expiry
                ))
    
    # Add global ATM strike vertical line
    if global_atm is not None:
        logger.info(f"Adding global ATM vertical line at x={global_atm}")
        fig.add_vline(
            x=global_atm,
            line_dash="dash",
            line_color=default_theme.danger,
            annotation_text="ATM",
            annotation_position="top"
        )
    
    # Update layout
    fig.update_layout(
        title=dict(
            text=f'{greek_display_name} Aggregate Profile - All Expiries',
            font=dict(size=16, color=default_theme.text_light)
        ),
        xaxis=dict(
            title='Strike Price',
            color=default_theme.text_light,
            gridcolor=default_theme.secondary,
            zeroline=False
        ),
        yaxis=dict(
            title=f'{greek_display_name} Value',
            color=default_theme.text_light,
            gridcolor=default_theme.secondary,
            zeroline=True,
            zerolinecolor=default_theme.secondary
        ),
        plot_bgcolor=default_theme.base_bg,
        paper_bgcolor=default_theme.panel_bg,
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            x=1.02,
            y=0.98,
            xanchor='left',
            yanchor='top',
            bgcolor='rgba(0,0,0,0)',
            font=dict(color=default_theme.text_light)
        ),
        height=500,  # Slightly taller for aggregate view
        margin=dict(l=60, r=150, t=60, b=50)  # More right margin for legend
    )
    
    return fig.to_dict()


def apply_spot_risk_filters(data: List[Dict], expiry_filter: str, type_filter: str, strike_range: List[float]) -> List[Dict]:
    """Apply filters to spot risk data - reusable for table and graph views
    
    Args:
        data: List of data rows
        expiry_filter: Expiry date filter value ('ALL' or specific date)
        type_filter: Option type filter ('ALL', 'C', 'P', 'F')
        strike_range: [min, max] strike range
        
    Returns:
        Filtered list of data rows
    """
    if not data:
        return []
    
    # Start with all data
    filtered_data = data.copy()
    
    # Apply expiry filter
    if expiry_filter and expiry_filter != 'ALL':
        filtered_data = [row for row in filtered_data 
                       if row.get('expiry_date') == expiry_filter]
    
    # Apply type filter
    if type_filter and type_filter != 'ALL':
        filtered_data = [row for row in filtered_data 
                       if row.get('itype') == type_filter]
    
    # Apply strike range filter
    if strike_range and len(strike_range) == 2:
        min_strike, max_strike = strike_range
        strike_filtered_data = []
        for row in filtered_data:
            strike_value = row.get('strike')
            # Skip rows with no valid strike (futures, invalid data)
            if strike_value is None or strike_value == 'INVALID':
                # Include futures and invalid strikes regardless of filter
                strike_filtered_data.append(row)
            else:
                try:
                    strike_float = float(strike_value)
                    if min_strike <= strike_float <= max_strike:
                        strike_filtered_data.append(row)
                except (ValueError, TypeError):
                    # Include rows where strike can't be converted
                    strike_filtered_data.append(row)
                    logger.warning(f"Could not convert strike to float: {strike_value}")
        filtered_data = strike_filtered_data
    
    return filtered_data


def apply_spot_risk_filters_with_greek_space(data: List[Dict], expiry_filter: str, type_filter: str, 
                                            strike_range: List[float], greek_space: str = 'F') -> List[Dict]:
    """Apply filters to spot risk data including Greek space filtering for NET rows
    
    Args:
        data: List of data rows
        expiry_filter: Expiry date filter value ('ALL' or specific date)
        type_filter: Option type filter ('ALL', 'C', 'P', 'F')
        strike_range: [min, max] strike range
        greek_space: Greek space selection ('F' or 'y')
        
    Returns:
        Filtered list of data rows
    """
    # First apply standard filters
    filtered_data = apply_spot_risk_filters(data, expiry_filter, type_filter, strike_range)
    
    # Then filter NET_OPTIONS rows based on Greek space
    final_data = []
    for row in filtered_data:
        key = row.get('key', row.get('instrument_key', ''))
        
        # Filter NET_OPTIONS rows based on Greek space
        if key == 'NET_OPTIONS_F' and greek_space != 'F':
            continue  # Skip F-space NET_OPTIONS when in Y-space
        elif key == 'NET_OPTIONS_Y' and greek_space != 'y':
            continue  # Skip Y-space NET_OPTIONS when in F-space
        else:
            final_data.append(row)
    
    return final_data


def register_callbacks(app):
    """Register all callbacks for the Spot Risk dashboard
    
    Args:
        app: Dash application instance
    """
    
    # Initialize controller
    controller = SpotRiskController()
    
    @app.callback(
        [Output('spot-risk-data-store', 'data'),
         Output('spot-risk-timestamp', 'children'),
         Output('spot-risk-no-data', 'style'),
         Output('spot-risk-table-wrapper', 'style'),
         Output('spot-risk-loading', 'children'),
         Output('spot-risk-last-processed-time', 'data')],  # Added output
        [Input('spot-risk-refresh-btn', 'n_clicks')],
        [State('spot-risk-data-store', 'data')],
        prevent_initial_call=False
    )
    @monitor()
    def refresh_data(n_clicks, stored_data):
        """Load or refresh spot risk data from CSV
        
        Returns:
            tuple: (data_store, timestamp, no_data_style, table_style, loading_children)
        """
        try:
            # Load data
            controller.load_csv_data()
            
            if controller.current_data is None or controller.current_data.empty:
                logger.warning("No data loaded from CSV")
                return (
                    None,
                    'No CSV data available',
                    {'display': 'block'},
                    {'display': 'none'},
                    no_update,
                    None # Added None for last_processed_time
                )
            
            # Process Greeks
            logger.info("Processing Greeks for loaded data...")
            df_with_greeks = controller.process_greeks(filter_positions=True)
            
            if df_with_greeks is None:
                logger.error("Failed to process Greeks")
                return (
                    None,
                    'Error processing Greeks',
                    {'display': 'block'},
                    {'display': 'none'},
                    no_update,
                    None # Added None for last_processed_time
                )
            
            # Check if any positions were found
            if df_with_greeks.empty:
                logger.info("No positions found in the data")
                return (
                    None,
                    'No positions found',
                    {'display': 'block'},
                    {'display': 'none'},
                    no_update,
                    None # Added None for last_processed_time
                )
            
            # Update controller data with processed Greeks
            controller.current_data = df_with_greeks
            
            # Get timestamp
            timestamp = controller.get_timestamp()
            timestamp_text = f'{len(df_with_greeks)} positions from: {timestamp}' if timestamp else f'{len(df_with_greeks)} positions loaded'
            
            # Convert DataFrame to dict for storage
            data_dict = controller.current_data.to_dict('records')
            
            logger.info(f"Loaded {len(data_dict)} positions with Greeks")
            
            # Get latest processed timestamp from state file
            latest_processed_time = None
            try:
                import json
                from pathlib import Path
                project_root = Path(__file__).parent.parent.parent.parent
                state_file = project_root / "data" / "output" / "spot_risk" / ".file_watcher_state.json"
                
                if state_file.exists():
                    with open(state_file, 'r') as f:
                        state = json.load(f)
                    
                    # Find the most recent processed_at timestamp
                    for file_info in state.values():
                        if 'processed_at' in file_info:
                            if latest_processed_time is None or file_info['processed_at'] > latest_processed_time:
                                latest_processed_time = file_info['processed_at']
            except Exception as e:
                logger.error(f"Error reading file watcher state: {e}")
            
            return (
                data_dict,
                timestamp_text,
                {'display': 'none'},  # Hide no-data message
                {'display': 'block'},  # Show table
                no_update,
                latest_processed_time  # Return the latest processed timestamp
            )
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return (
                None,
                f'Error: {str(e)}',
                {'display': 'block'},
                {'display': 'none'},
                no_update,
                None # Added None for last_processed_time
            )
    
    @app.callback(
        Output('spot-risk-model-params-content', 'children'),
        [Input('spot-risk-data-store', 'data')],
        prevent_initial_call=False
    )
    @monitor()
    def update_model_parameters(stored_data):
        """Update model parameters display based on loaded data
        
        Returns:
            list: HTML elements displaying model parameters
        """
        if not stored_data:
            return 'No data loaded'
        
        try:
            # Convert stored data to DataFrame for easier processing
            df = pd.DataFrame(stored_data)
            
            # Extract future price from futures row
            future_price = None
            futures_mask = df['itype'].str.upper() == 'F'
            if futures_mask.any():
                future_row = df[futures_mask].iloc[0]
                future_price = future_row.get('midpoint_price', None)
            
            # Get DV01 and convexity from calculator
            dv01 = controller.calculator.dv01  # This is 63.0
            convexity = controller.calculator.convexity  # This is 0.0042
            
            # Group implied vol by expiry (average for options)
            expiry_implied_vol = {}
            for expiry in df['expiry_date'].unique():
                if pd.notna(expiry):
                    # Filter for options (C or P) with positions in this expiry
                    mask = (df['expiry_date'] == expiry) & (df['itype'].isin(['C', 'P'])) & (df['pos.position'] != 0)
                    expiry_options = df[mask]
                    
                    if len(expiry_options) > 0 and 'implied_vol' in expiry_options.columns:
                        # Calculate average implied vol for this expiry
                        avg_vol = expiry_options['implied_vol'].mean()
                        if pd.notna(avg_vol):
                            expiry_implied_vol[expiry] = avg_vol
            
            # Format display elements
            params_elements = []
            
            # Add bullet separator function
            def add_bullet():
                return html.Span(' • ', style={'color': default_theme.text_subtle})
            
            # Future Price
            if future_price is not None:
                params_elements.append(html.Span('Future Price: ', style={'fontWeight': '500'}))
                params_elements.append(html.Span(f'{float(future_price):.4f}'))
                params_elements.append(add_bullet())
            
            # DV01
            params_elements.append(html.Span('DV01: ', style={'fontWeight': '500'}))
            params_elements.append(html.Span(f'{dv01:.1f}'))
            params_elements.append(add_bullet())
            
            # Convexity
            params_elements.append(html.Span('Convexity: ', style={'fontWeight': '500'}))
            params_elements.append(html.Span(f'{convexity:.4f}'))
            
            # Implied Vol (if we have expiries)
            if expiry_implied_vol:
                params_elements.append(add_bullet())
                params_elements.append(html.Span('Avg Implied Vol: ', style={'fontWeight': '500'}))
                
                # Sort expiries
                sorted_expiries = sorted(expiry_implied_vol.items())
                
                # Create inline display for implied vol
                vol_parts = []
                for i, (expiry, vol) in enumerate(sorted_expiries):
                    if i > 0:
                        vol_parts.append(html.Span(', ', style={'color': default_theme.text_subtle}))
                    # Display as decimal with 4 decimal places (same as table)
                    vol_parts.append(html.Span(f'{expiry}: {vol:.4f}'))
                
                params_elements.extend(vol_parts)
            
            return params_elements
            
        except Exception as e:
            logger.error(f"Error updating model parameters: {e}")
            return f'Error loading parameters: {str(e)}'
    
    @app.callback(
        [Output('spot-risk-data-table', 'data'),
         Output('spot-risk-data-table', 'columns')],
        [Input('spot-risk-data-store', 'data'),
         Input('spot-risk-expiry-filter', 'value'),
         Input('spot-risk-type-filter', 'value'),
         Input('spot-risk-strike-filter', 'value'),
         Input('spot-risk-base-info', 'value'),
         Input('spot-risk-1st-order', 'value'),
         Input('spot-risk-2nd-order', 'value'),
         Input('spot-risk-3rd-order', 'value'),
         Input('spot-risk-cross-greeks', 'value'),
         Input('spot-risk-greek-space-store', 'data')],
        prevent_initial_call=True
    )
    @monitor()
    def update_table_data(stored_data, expiry_filter, type_filter, strike_range,
                          base_checked, first_checked, second_checked, 
                          third_checked, cross_checked, greek_space):
        """Update table data based on filters and Greek selections
        
        Returns:
            tuple: (filtered_data, visible_columns)
        """
        if not stored_data:
            return [], []
        
        # Apply filters using the reusable function
        filtered_data = apply_spot_risk_filters_with_greek_space(
            stored_data, expiry_filter, type_filter, strike_range, greek_space
        )
        
        # Build visible columns based on Greek selections and Greek space filter
        column_defs = get_column_definitions()
        visible_columns = []
        
        # Always include base columns
        visible_columns.extend(column_defs['base'])
        
        # Helper function to filter columns by Greek space
        def filter_by_greek_space(columns, space):
            """Filter Greek columns based on selected space (F or y)"""
            filtered = []
            for col in columns:
                col_id = col['id']
                # Keep columns that match the selected space or have no space suffix
                if f'_{space}' in col_id:
                    filtered.append(col)
                elif not ('_F' in col_id or '_y' in col_id):
                    # Keep columns that don't have F/y suffix (like vega_price, volga_price)
                    filtered.append(col)
            return filtered
        
        # Add columns based on checkboxes, filtered by Greek space
        if first_checked and '1st' in first_checked:
            cols = filter_by_greek_space(column_defs['1st'], greek_space)
            visible_columns.extend(cols)
        
        if second_checked and '2nd' in second_checked:
            cols = filter_by_greek_space(column_defs['2nd'], greek_space)
            visible_columns.extend(cols)
            
        if third_checked and '3rd' in third_checked:
            cols = filter_by_greek_space(column_defs['3rd'], greek_space)
            visible_columns.extend(cols)
            
        if cross_checked and 'cross' in cross_checked:
            cols = filter_by_greek_space(column_defs['cross'], greek_space)
            visible_columns.extend(cols)
        
        # Always add other columns (implied vol, status, etc.)
        visible_columns.extend(column_defs['other'])
        
        logger.info(f"Filtered to {len(filtered_data)} rows with {len(visible_columns)} columns")
        
        return filtered_data, visible_columns
    
    @app.callback(
        [Output('spot-risk-table-container', 'style'),
         Output('spot-risk-graph-container', 'style'),
         Output('spot-risk-table-view-btn', 'style'),
         Output('spot-risk-graph-view-btn', 'style')],
        [Input('spot-risk-table-view-btn', 'n_clicks'),
         Input('spot-risk-graph-view-btn', 'n_clicks')],
        prevent_initial_call=False
    )
    @monitor()
    def toggle_view_mode(table_clicks, graph_clicks):
        """Toggle between table and graph views
        
        Returns:
            tuple: (table_style, graph_style, table_btn_style, graph_btn_style)
        """
        # Determine which button was clicked last
        ctx = dash.callback_context
        
        # Default to table view
        if not ctx.triggered:
            show_table = True
        else:
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]
            show_table = button_id == 'spot-risk-table-view-btn'
        
        # Base button styles
        active_btn_style = {
            'backgroundColor': default_theme.primary,
            'color': default_theme.base_bg,
            'border': f'1px solid {default_theme.primary}',
            'padding': '8px 20px',
            'fontSize': '14px',
            'fontWeight': 'bold',
            'cursor': 'pointer',
            'minWidth': '80px'
        }
        
        inactive_btn_style = {
            'backgroundColor': default_theme.panel_bg,
            'color': default_theme.text_light,
            'border': f'1px solid {default_theme.secondary}',
            'padding': '8px 20px',
            'fontSize': '14px',
            'fontWeight': 'normal',
            'cursor': 'pointer',
            'minWidth': '80px'
        }
        
        if show_table:
            return (
                {'display': 'block'},  # Show table
                {'display': 'none'},   # Hide graph
                {**active_btn_style, 'borderRadius': '4px 0 0 4px'},
                {**inactive_btn_style, 'borderRadius': '0 4px 4px 0', 'borderLeft': 'none'}
            )
        else:
            return (
                {'display': 'none'},   # Hide table
                {'display': 'block'},  # Show graph
                {**inactive_btn_style, 'borderRadius': '4px 0 0 4px'},
                {**active_btn_style, 'borderRadius': '0 4px 4px 0', 'borderLeft': 'none'}
            )
    
    @app.callback(
        Output('spot-risk-strike-range-display', 'children'),
        [Input('spot-risk-strike-filter', 'value')],
        prevent_initial_call=False
    )
    @monitor()
    def update_strike_range_display(strike_range):
        """Update the strike range display text
        
        Returns:
            str: Formatted strike range text
        """
        if strike_range and len(strike_range) == 2:
            # Check that both values are not None
            if strike_range[0] is not None and strike_range[1] is not None:
                return f'Selected: {strike_range[0]:.2f} - {strike_range[1]:.2f}'
        return 'No valid strike range available'
    
    @app.callback(
        [Output('spot-risk-refresh-interval', 'interval'),
         Output('spot-risk-refresh-interval', 'disabled')],
        [Input('spot-risk-auto-refresh-toggle', 'value'),
         Input('spot-risk-refresh-interval-input', 'value')],
        prevent_initial_call=False
    )
    @monitor()
    def update_auto_refresh(auto_refresh_enabled, interval_minutes):
        """Update auto-refresh settings
        
        Returns:
            tuple: (interval_ms, disabled)
        """
        if auto_refresh_enabled and interval_minutes:
            # Convert minutes to milliseconds
            interval_ms = int(interval_minutes) * 60 * 1000
            return interval_ms, False
        else:
            # Keep default interval but disable
            return 5 * 60 * 1000, True
    
    # Export functionality is implemented below using dcc.Download component
    
    @app.callback(
        Output('spot-risk-download-csv', 'data'),
        [Input('spot-risk-export-btn', 'n_clicks')],
        [State('spot-risk-data-table', 'data'),
         State('spot-risk-data-table', 'columns'),
         State('spot-risk-timestamp', 'children')],
        prevent_initial_call=True
    )
    @monitor()
    def export_data(n_clicks, table_data, table_columns, timestamp_text):
        """Export visible data to CSV
        
        Returns:
            dict: Download data for dcc.Download component
        """
        if not n_clicks or not table_data or not table_columns:
            raise PreventUpdate
            
        try:
            # Convert table data to DataFrame
            df = pd.DataFrame(table_data)
            
            # Extract only the columns that are visible in the table
            visible_column_ids = [col['id'] for col in table_columns]
            df_export = df[visible_column_ids]
            
            # Generate filename with timestamp
            from datetime import datetime
            current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'spot_risk_export_{current_time}.csv'
            
            # Convert DataFrame to CSV string
            csv_string = df_export.to_csv(index=False)
            
            logger.info(f"Exporting {len(df_export)} rows, {len(df_export.columns)} columns to {filename}")
            
            # Return download data
            return dict(content=csv_string, filename=filename)
            
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            raise PreventUpdate
    
    @app.callback(
        [Output('spot-risk-data-store', 'data', allow_duplicate=True),
         Output('spot-risk-timestamp', 'children', allow_duplicate=True),
         Output('spot-risk-no-data', 'style', allow_duplicate=True),
         Output('spot-risk-table-wrapper', 'style', allow_duplicate=True)],
        [Input('spot-risk-refresh-interval', 'n_intervals')],
        [State('spot-risk-auto-refresh-toggle', 'value'),
         State('spot-risk-data-store', 'data')],
        prevent_initial_call=True
    )
    @monitor()
    def auto_refresh_data(n_intervals, auto_refresh_enabled, stored_data):
        """Auto-refresh data based on interval
        
        Returns:
            tuple: (data_store, timestamp, no_data_style, table_style)
        """
        if not auto_refresh_enabled:
            raise PreventUpdate
        
        try:
            # Load data
            controller.load_csv_data()
            
            if controller.current_data is None or controller.current_data.empty:
                logger.warning("No data loaded from CSV during auto-refresh")
                return (
                    None,
                    'No data loaded',
                    {'display': 'block'},
                    {'display': 'none'}
                )
            
            # Process Greeks
            logger.info("Processing Greeks for auto-refreshed data...")
            df_with_greeks = controller.process_greeks(filter_positions=True)
            
            if df_with_greeks is None:
                logger.error("Failed to process Greeks during auto-refresh")
                # Don't update UI on error during auto-refresh
                raise PreventUpdate
            
            # Check if any positions were found
            if df_with_greeks.empty:
                logger.info("No positions found in the data during auto-refresh")
                return (
                    None,
                    'No positions found',
                    {'display': 'block'},
                    {'display': 'none'}
                )
            
            # Update controller data with processed Greeks
            controller.current_data = df_with_greeks
            
            # Get timestamp
            timestamp = controller.get_timestamp()
            timestamp_text = f'{len(df_with_greeks)} positions from: {timestamp} (Auto-refreshed)' if timestamp else f'{len(df_with_greeks)} positions loaded (Auto-refreshed)'
            
            # Convert DataFrame to dict for storage
            data_dict = controller.current_data.to_dict('records')
            
            logger.info(f"Auto-refreshed {len(data_dict)} positions with Greeks")
            
            return (
                data_dict,
                timestamp_text,
                {'display': 'none'},  # Hide no-data message
                {'display': 'block'}  # Show table
            )
            
        except Exception as e:
            logger.error(f"Error during auto-refresh: {e}")
            # Don't update UI on error during auto-refresh
            raise PreventUpdate
    
    @app.callback(
        [Output('spot-risk-strike-filter', 'min'),
         Output('spot-risk-strike-filter', 'max'),
         Output('spot-risk-strike-filter', 'value'),
         Output('spot-risk-strike-filter', 'marks')],
        [Input('spot-risk-data-store', 'data')],
        prevent_initial_call=False
    )
    @monitor()
    def update_strike_range_slider(stored_data):
        """Update strike range slider with actual data ranges
        
        Returns:
            tuple: (min, max, value, marks)
        """
        # Default values for ZN futures
        default_min, default_max = 100.0, 120.0
        
        if not stored_data:
            # No data yet, use defaults
            return (
                default_min,
                default_max,
                [default_min, default_max],
                {default_min: f'{default_min:.2f}', default_max: f'{default_max:.2f}'}
            )
        
        # Extract valid strikes from data
        valid_strikes = []
        for row in stored_data:
            strike_value = row.get('strike')
            if strike_value is not None and strike_value != 'INVALID':
                try:
                    strike_float = float(strike_value)
                    valid_strikes.append(strike_float)
                except (ValueError, TypeError):
                    continue
        
        if valid_strikes:
            # Use actual data range
            min_strike = min(valid_strikes)
            max_strike = max(valid_strikes)
            
            # Add a small buffer to the range
            strike_buffer = (max_strike - min_strike) * 0.1
            min_strike = max(0, min_strike - strike_buffer)
            max_strike = max_strike + strike_buffer
            
            # Round to nearest 0.25
            min_strike = round(min_strike * 4) / 4
            max_strike = round(max_strike * 4) / 4
        else:
            # No valid strikes found, use defaults
            min_strike, max_strike = default_min, default_max
        
        return (
            min_strike,
            max_strike,
            [min_strike, max_strike],
            {min_strike: f'{min_strike:.2f}', max_strike: f'{max_strike:.2f}'}
        )
    
    # Log successful registration
    logger.info("Spot Risk callbacks registered successfully") 
    
    # Add view state tracking callback
    @app.callback(
        Output('spot-risk-display-store', 'data'),
        [Input('spot-risk-table-view-btn', 'n_clicks'),
         Input('spot-risk-graph-view-btn', 'n_clicks')],
        [State('spot-risk-display-store', 'data')],
        prevent_initial_call=False
    )
    @monitor()
    def track_view_state(table_clicks, graph_clicks, current_state):
        """Track current view state
        
        Returns:
            dict: View state information
        """
        table_clicks = table_clicks or 0
        graph_clicks = graph_clicks or 0
        
        # Initialize state if needed
        if not current_state:
            current_state = {
                'view_mode': 'table',
                'last_table_clicks': 0,
                'last_graph_clicks': 0
            }
        
        # Determine which view is active based on click counts
        if table_clicks > current_state.get('last_table_clicks', 0):
            view_mode = 'table'
        elif graph_clicks > current_state.get('last_graph_clicks', 0):
            view_mode = 'graph'
        else:
            view_mode = current_state.get('view_mode', 'table')
        
        logger.info(f"View state: mode={view_mode}, table_clicks={table_clicks}, graph_clicks={graph_clicks}")
        
        return {
            'view_mode': view_mode,
            'last_table_clicks': table_clicks,
            'last_graph_clicks': graph_clicks
        }

    @app.callback(
        [Output('spot-risk-graphs-grid', 'children'),
         Output('spot-risk-graph-info', 'children')],
        [Input('spot-risk-table-view-btn', 'n_clicks'),
         Input('spot-risk-graph-view-btn', 'n_clicks'),
         Input('spot-risk-1st-order', 'value'),
         Input('spot-risk-2nd-order', 'value'),
         Input('spot-risk-3rd-order', 'value'),
         Input('spot-risk-cross-greeks', 'value'),
         Input('spot-risk-greek-space-store', 'data'),
         # Add filter inputs
         Input('spot-risk-expiry-filter', 'value'),
         Input('spot-risk-type-filter', 'value'),
         Input('spot-risk-strike-filter', 'value')],
        [State('spot-risk-data-store', 'data'),
         State('spot-risk-display-store', 'data')],
        prevent_initial_call=True
    )
    @monitor()
    def update_greek_graphs(table_clicks, graph_clicks, first_order, second_order, 
                            third_order, cross_greeks, greek_space,
                            expiry_filter, type_filter, strike_range,  # New parameters
                            stored_data, view_state):
        """Generate Greek profile graphs based on selected Greeks
        
        Returns:
            tuple: (graph_children, info_text)
        """
        # Determine which button was clicked and current view
        ctx = dash.callback_context
        if not ctx.triggered:
            return [], ''
        
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
        logger.info(f"Greek graphs callback triggered by: {triggered_id}")
        
        # Use view state to determine current view
        current_view = view_state.get('view_mode', 'table') if view_state else 'table'
        
        # If switching to table view, clear graphs
        if triggered_id == 'spot-risk-table-view-btn':
            logger.info("Switched to table view, clearing graphs")
            return [], ''
        
        # Only generate graphs if:
        # 1. Graph button was clicked (switching to graph view)
        # 2. We're in graph view and Greek selections changed
        # 3. We're in graph view and filters changed
        should_generate = False
        
        if triggered_id == 'spot-risk-graph-view-btn':
            logger.info("Switched to graph view, generating graphs")
            should_generate = True
        elif current_view == 'graph' and any(x in triggered_id for x in ['order', 'greeks', 'greek-space']):
            logger.info(f"Greek selection changed in graph view: {triggered_id}")
            should_generate = True
        elif current_view == 'graph' and any(x in triggered_id for x in ['filter', 'strike']):
            logger.info(f"Filter changed in graph view: {triggered_id}")
            should_generate = True
        else:
            logger.info(f"Not generating graphs: triggered_id={triggered_id}, current_view={current_view}")
            return dash.no_update, dash.no_update
        
        if not should_generate:
            return dash.no_update, dash.no_update
        
        # Check if we have data
        if not stored_data:
            logger.warning("No data available for graphs")
            return [html.P('No data available for graphs', 
                          style={'color': default_theme.text_subtle, 'textAlign': 'center'})], ''
        
        # Collect selected Greeks
        selected_greeks = []
        
        # Map checkbox values to Greek names
        greek_mapping = {
            '1st': ['delta', 'vega', 'theta'],
            '2nd': ['gamma', 'volga', 'vanna', 'charm'],
            '3rd': ['speed', 'color', 'ultima', 'zomma'],
            'cross': ['vanna', 'charm', 'veta']  # Cross Greeks overlap with 2nd order
        }
        
        # Handle checkbox values (could be None, empty list, or list with values)
        if first_order and isinstance(first_order, list) and '1st' in first_order:
            selected_greeks.extend(greek_mapping['1st'])
        if second_order and isinstance(second_order, list) and '2nd' in second_order:
            selected_greeks.extend(greek_mapping['2nd'])
        if third_order and isinstance(third_order, list) and '3rd' in third_order:
            selected_greeks.extend(greek_mapping['3rd'])
        if cross_greeks and isinstance(cross_greeks, list) and 'cross' in cross_greeks:
            # Add cross Greeks that aren't already included
            for greek in greek_mapping['cross']:
                if greek not in selected_greeks:
                    selected_greeks.append(greek)
        
        logger.info(f"Selected Greeks from checkboxes: {selected_greeks}")
        logger.info(f"Checkbox values - 1st: {first_order}, 2nd: {second_order}, 3rd: {third_order}, cross: {cross_greeks}")
        
        if not selected_greeks:
            # If no Greeks selected but we're switching to graph view, show message
            return [html.P('Please select Greek groups to display', 
                          style={'color': default_theme.text_light, 'textAlign': 'center'})], ''
        
        # Generate Greek profiles
        try:
            # Apply filters to data before generating profiles
            filtered_data = apply_spot_risk_filters_with_greek_space(
                stored_data, expiry_filter, type_filter, strike_range, greek_space
            )
            
            if not filtered_data:
                logger.info("No data after applying filters")
                return [html.P('No data matches the current filters', 
                              style={'color': default_theme.text_subtle, 'textAlign': 'center'})], ''
            
            # Convert filtered data to DataFrame for controller
            df = pd.DataFrame(filtered_data)
            controller.current_data = df
            
            # Generate profiles for selected Greeks grouped by expiry
            logger.info(f"Generating profiles for {len(selected_greeks)} Greeks by expiry with {len(filtered_data)} filtered rows")
            logger.info(f"[DEBUG GRAPH CALLBACK] Greek space parameter: {greek_space}")
            profiles_by_expiry = controller.generate_greek_profiles_by_expiry(selected_greeks, greek_space)
            
            if not profiles_by_expiry:
                logger.error("Failed to generate Greek profiles - no expiry data returned")
                return [html.P('Failed to generate Greek profiles - no expiry data found', 
                              style={'color': default_theme.text_subtle, 'textAlign': 'center'})], ''
            
            logger.info(f"Generated profiles for {len(profiles_by_expiry)} expiries")
            
            # Create graph components organized by expiry
            all_graph_children = []
            total_positions = 0
            
            # Sort expiries for consistent display
            sorted_expiries = sorted(profiles_by_expiry.keys())
            
            # ====== AGGREGATE VIEWS SECTION ======
            # Create aggregate views header
            aggregate_header = html.Div(
                style={
                    'backgroundColor': default_theme.primary,
                    'padding': '12px 20px',
                    'borderRadius': '8px',
                    'marginBottom': '20px',
                    'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
                },
                children=[
                    html.H3(
                        'Aggregate Views - All Expiries',
                        style={
                            'color': default_theme.base_bg,
                            'margin': '0',
                            'fontSize': '24px',
                            'fontWeight': '700'
                        }
                    ),
                    html.P(
                        f'Showing {len(sorted_expiries)} expiries on single graphs',
                        style={
                            'color': default_theme.base_bg,
                            'margin': '8px 0 0 0',
                            'fontSize': '14px',
                            'opacity': '0.9'
                        }
                    )
                ]
            )
            all_graph_children.append(aggregate_header)
            
            # Generate aggregate graphs for each selected Greek
            aggregate_graph_children = []
            
            for greek in selected_greeks:
                # Check if this Greek exists in any expiry
                greek_exists = any(greek in profile_data.get('greeks', {}) 
                                 for profile_data in profiles_by_expiry.values())
                
                if not greek_exists:
                    logger.warning(f"Greek '{greek}' not found in any expiry data")
                    continue
                
                # Create aggregate graph for this Greek
                try:
                    # Debug log aggregate graph data
                    logger.info(f"[DEBUG AGGREGATE GRAPH] Creating aggregate graph for {greek} in {greek_space}-space")
                    for exp, prof in profiles_by_expiry.items():
                        if greek in prof.get('greeks', {}):
                            vals = prof['greeks'][greek]
                            logger.info(f"[DEBUG AGGREGATE GRAPH] - {exp}: range [{min(vals):.6f}, {max(vals):.6f}]")
                    
                    aggregate_fig_dict = create_aggregate_greek_graph(
                        greek_name=greek,
                        profiles_by_expiry=profiles_by_expiry,
                        greek_space=greek_space
                    )
                    
                    # Create graph container
                    aggregate_graph_container = html.Div(
                        style={
                            'backgroundColor': default_theme.panel_bg,
                            'borderRadius': '8px',
                            'padding': '10px',
                            'border': f'2px solid {default_theme.primary}',
                            'boxShadow': '0 2px 6px rgba(0,0,0,0.1)'
                        },
                        children=[
                            Graph(
                                id=f'spot-risk-aggregate-graph-{greek}',
                                figure=aggregate_fig_dict,
                                style={'height': '500px'},
                                config={'displayModeBar': True, 'displaylogo': False}
                            ).render()
                        ]
                    )
                    
                    aggregate_graph_children.append(aggregate_graph_container)
                    
                except Exception as e:
                    logger.error(f"Error creating aggregate graph for {greek}: {e}")
                    continue
            
            if aggregate_graph_children:
                # Create aggregate graphs grid
                aggregate_graphs_grid = html.Div(
                    style={
                        'display': 'grid',
                        'gridTemplateColumns': 'repeat(auto-fit, minmax(600px, 1fr))',
                        'gap': '20px',
                        'marginBottom': '40px'
                    },
                    children=aggregate_graph_children
                )
                all_graph_children.append(aggregate_graphs_grid)
            
            # ====== INDIVIDUAL EXPIRY VIEWS SECTION ======
            # Create individual views header
            individual_header = html.Div(
                style={
                    'backgroundColor': default_theme.accent,
                    'padding': '12px 20px',
                    'borderRadius': '8px',
                    'marginBottom': '20px',
                    'marginTop': '40px',
                    'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
                },
                children=[
                    html.H3(
                        'Individual Expiry Views',
                        style={
                            'color': default_theme.base_bg,
                            'margin': '0',
                            'fontSize': '24px',
                            'fontWeight': '700'
                        }
                    ),
                    html.P(
                        'Detailed Greek profiles for each expiry date',
                        style={
                            'color': default_theme.base_bg,
                            'margin': '8px 0 0 0',
                            'fontSize': '14px',
                            'opacity': '0.9'
                        }
                    )
                ]
            )
            all_graph_children.append(individual_header)
            
            # Continue with existing per-expiry logic
            for expiry in sorted_expiries:
                profile_data = profiles_by_expiry[expiry]
                
                # Create expiry section header
                expiry_header = html.Div(
                    style={
                        'backgroundColor': default_theme.secondary,
                        'padding': '10px 15px',
                        'borderRadius': '8px',
                        'marginBottom': '10px',
                        'marginTop': '20px' if all_graph_children else '0'
                    },
                    children=[
                        html.H4(
                            f'Expiry: {expiry}',
                            style={
                                'color': default_theme.text_light,
                                'margin': '0',
                                'fontSize': '20px',
                                'fontWeight': '600'
                            }
                        ),
                        html.P(
                            f'{len(profile_data["positions"])} positions | '
                            f'Net: {profile_data["total_position"]:.0f} | '
                            f'ATM: {profile_data["atm_strike"]:.2f}',
                            style={
                                'color': default_theme.text_light,  # Changed from text_subtle to text_light
                                'margin': '5px 0 0 0',
                                'fontSize': '14px'
                            }
                        )
                    ]
                )
                # Debug logging for ATM in header
                logger.info(f"Expiry {expiry} header - ATM displayed: {profile_data['atm_strike']:.2f}")
                all_graph_children.append(expiry_header)
                
                # Build graphs for this expiry
                expiry_graph_children = []
                
                # Generate graph for each selected Greek
                for greek in selected_greeks:
                    if greek in profile_data['greeks']:
                        greek_values = profile_data['greeks'][greek]
                        
                        # Validate we have data
                        if not greek_values or all(v == 0 for v in greek_values):
                            logger.warning(f"Greek '{greek}' has no data for expiry {expiry}")
                            continue
                        
                        # Create figure for this Greek
                        # Get the actual column name used for this Greek
                        greek_columns_used = profile_data.get('greek_columns_used', {})
                        actual_column = greek_columns_used.get(greek, greek)
                        
                        # Extract the suffix (F or y) from column name for display
                        display_suffix = ''
                        if '_F' in actual_column:
                            display_suffix = '_F'
                        elif '_y' in actual_column:
                            display_suffix = '_y'
                        elif actual_column == 'vega_price':
                            display_suffix = '_price'
                        
                        # Create display name with suffix
                        greek_display_name = f'{greek}{display_suffix}'
                        
                        # Debug log the values being passed to the graph
                        greek_values_to_plot = profile_data['greeks'][greek]
                        logger.info(f"[DEBUG GRAPH VALUES] Plotting {greek} for {expiry} in {greek_space}-space:")
                        logger.info(f"[DEBUG GRAPH VALUES] - Value range: [{min(greek_values_to_plot):.6f}, {max(greek_values_to_plot):.6f}]")
                        logger.info(f"[DEBUG GRAPH VALUES] - First 5 values: {greek_values_to_plot[:5]}")
                        logger.info(f"[DEBUG GRAPH VALUES] - Display name: {greek_display_name}")
                        
                        fig_dict = create_greek_profile_graph(
                            greek_name=f'{greek_display_name} ({expiry})',  # Include suffix and expiry
                            strikes=profile_data['strikes'],
                            values=profile_data['greeks'][greek],
                            positions=profile_data['positions'],
                            atm_strike=profile_data['atm_strike']
                        )
                        
                        # Create graph container
                        graph_container = html.Div(
                            style={
                                'backgroundColor': default_theme.panel_bg,
                                'borderRadius': '8px',
                                'padding': '10px',
                                'border': f'1px solid {default_theme.secondary}'
                            },
                            children=[
                                Graph(
                                    id=f'spot-risk-graph-{expiry}-{greek}',
                                    figure=fig_dict,
                                    style={'height': '400px'},
                                    config={'displayModeBar': True, 'displaylogo': False}
                                ).render()
                            ]
                        )
                        
                        expiry_graph_children.append(graph_container)
                
                if expiry_graph_children:
                    # Create the expiry graphs container
                    expiry_graphs = html.Div(
                        style={
                            'display': 'grid',
                            'gridTemplateColumns': 'repeat(auto-fit, minmax(500px, 1fr))',
                            'gap': '20px',
                            'marginBottom': '20px'
                        },
                        children=expiry_graph_children
                    )
                    all_graph_children.append(expiry_graphs)
                    total_positions += len(profile_data['positions'])
                else:
                    logger.warning(f"No valid Greek graphs for expiry {expiry}")
            
            if not all_graph_children:
                logger.warning("No valid Greek graphs could be generated for any expiry")
                return [html.P('No valid Greek data to display', 
                              style={'color': default_theme.text_subtle, 'textAlign': 'center'})], ''
            
            # Create summary info text with filter status
            filter_parts = []
            if expiry_filter and expiry_filter != 'ALL':
                filter_parts.append(f'Expiry: {expiry_filter}')
            if type_filter and type_filter != 'ALL':
                type_map = {'C': 'Calls', 'P': 'Puts', 'F': 'Futures'}
                filter_parts.append(f'Type: {type_map.get(type_filter, type_filter)}')
            if strike_range and len(strike_range) == 2:
                filter_parts.append(f'Strikes: {strike_range[0]:.2f}-{strike_range[1]:.2f}')
            
            filter_text = ' | '.join(filter_parts) if filter_parts else 'All data'
            info_text = f'{len(profiles_by_expiry)} expiries | {total_positions} total positions | {filter_text}'
            
            logger.info(f"Successfully created graphs for {len(profiles_by_expiry)} expiries with filters: {filter_text}")
            return all_graph_children, info_text
            
        except Exception as e:
            logger.error(f"Error generating Greek profiles: {e}", exc_info=True)
            # Fall back to placeholder on error
            logger.info("Falling back to placeholder graph due to error")
            
            import plotly.graph_objects as go
            
            # Create a simple placeholder figure
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=[0, 1, 2, 3, 4],
                y=[0, 1, 4, 9, 16],
                mode='lines+markers',
                name='Error - Using Test Data'
            ))
            
            fig.update_layout(
                title=f'Placeholder Graph - Error: {str(e)}',
                xaxis_title='X Axis',
                yaxis_title='Y Axis',
                plot_bgcolor=default_theme.base_bg,
                paper_bgcolor=default_theme.panel_bg,
                font_color=default_theme.text_light,
                height=400
            )
            
            # Create a simple graph container
            placeholder_graph = html.Div(
                style={
                    'backgroundColor': default_theme.panel_bg,
                    'borderRadius': '8px',
                    'padding': '10px',
                    'border': f'1px solid {default_theme.secondary}'
                },
                children=[
                    Graph(
                        id='spot-risk-placeholder-graph',
                        figure=fig,
                        style={'height': '400px'},
                        config={'displayModeBar': True, 'displaylogo': False}
                    ).render()
                ]
            )
            
            return [placeholder_graph], f'Error: {str(e)}' 

    # Greek space toggle callback
    @app.callback(
        [Output('spot-risk-greek-space-store', 'data'),
         Output('spot-risk-f-space-btn', 'style'),
         Output('spot-risk-y-space-btn', 'style')],
        [Input('spot-risk-f-space-btn', 'n_clicks'),
         Input('spot-risk-y-space-btn', 'n_clicks')],
        [State('spot-risk-greek-space-store', 'data')],
        prevent_initial_call=False
    )
    @monitor()
    def toggle_greek_space(f_clicks, y_clicks, current_space):
        """Toggle between F-space and Y-space Greek display
        
        Returns:
            tuple: (greek_space, f_btn_style, y_btn_style)
        """
        ctx = dash.callback_context
        
        # Default styles
        active_style = {
            'backgroundColor': default_theme.primary,
            'color': default_theme.base_bg,
            'border': f'1px solid {default_theme.primary}',
            'padding': '8px 20px',
            'fontSize': '14px',
            'fontWeight': 'bold',
            'cursor': 'pointer',
            'minWidth': '80px'
        }
        
        inactive_style = {
            'backgroundColor': default_theme.panel_bg,
            'color': default_theme.text_light,
            'border': f'1px solid {default_theme.secondary}',
            'padding': '8px 20px',
            'fontSize': '14px',
            'fontWeight': 'normal',
            'cursor': 'pointer',
            'minWidth': '80px'
        }
        
        # Determine which button was clicked
        if ctx.triggered and ctx.triggered[0]['prop_id'].startswith('spot-risk-f-space-btn'):
            greek_space = 'F'
        elif ctx.triggered and ctx.triggered[0]['prop_id'].startswith('spot-risk-y-space-btn'):
            greek_space = 'y'
        else:
            # Initial load or no trigger, use current state
            greek_space = current_space or 'F'
        
        # Update button styles based on selection
        if greek_space == 'F':
            f_style = {**active_style, 'borderRadius': '4px 0 0 4px'}
            y_style = {**inactive_style, 'borderRadius': '0 4px 4px 0', 'borderLeft': 'none'}
        else:
            f_style = {**inactive_style, 'borderRadius': '4px 0 0 4px'}
            y_style = {**active_style, 'borderRadius': '0 4px 4px 0', 'borderLeft': 'none'}
        
        logger.info(f"Greek space toggled to: {greek_space}")
        
        return greek_space, f_style, y_style 

    @app.callback(
        [Output('spot-risk-file-completion-store', 'data'),
         Output('spot-risk-data-store', 'data', allow_duplicate=True),
         Output('spot-risk-timestamp', 'children', allow_duplicate=True),
         Output('spot-risk-no-data', 'style', allow_duplicate=True),
         Output('spot-risk-table-wrapper', 'style', allow_duplicate=True)],
        [Input('spot-risk-file-watcher-interval', 'n_intervals')],
        [State('spot-risk-last-processed-time', 'data'),
         State('spot-risk-data-store', 'data')],
        prevent_initial_call=True
    )
    # @monitor()  # Commented out to reduce queue load - this runs every second
    def check_file_completion(n_intervals, last_processed_time, current_data):
        """Check if file watcher has completed processing new files
        
        Returns updated data if new files were processed, otherwise no_update
        """
        import json
        from pathlib import Path
        
        try:
            # Get the state file path
            project_root = Path(__file__).parent.parent.parent.parent
            state_file = project_root / "data" / "output" / "spot_risk" / ".file_watcher_state.json"
            
            if not state_file.exists():
                raise PreventUpdate
            
            # Read the state file
            with open(state_file, 'r') as f:
                state = json.load(f)
            
            if not state:
                raise PreventUpdate
            
            # Find the most recent processed_at timestamp
            latest_processed = None
            for file_info in state.values():
                if 'processed_at' in file_info:
                    if latest_processed is None or file_info['processed_at'] > latest_processed:
                        latest_processed = file_info['processed_at']
            
            # Check if we have a new file processed
            if latest_processed and latest_processed != last_processed_time:
                logger.info(f"New file processed at {latest_processed}, triggering refresh")
                
                # Reload data using the same logic as refresh_data
                controller.load_csv_data()
                
                if controller.current_data is None or controller.current_data.empty:
                    logger.warning("No data loaded from CSV")
                    return (
                        latest_processed,
                        None,
                        'No CSV data available',
                        {'display': 'block'},
                        {'display': 'none'}
                    )
                
                # Process Greeks
                logger.info("Processing Greeks for loaded data...")
                df_with_greeks = controller.process_greeks(filter_positions=True)
                
                if df_with_greeks is None:
                    logger.error("Failed to process Greeks")
                    return (
                        latest_processed,
                        None,
                        'Error processing Greeks',
                        {'display': 'block'},
                        {'display': 'none'}
                    )
                
                # Check if any positions were found
                if df_with_greeks.empty:
                    logger.info("No positions found in the data")
                    return (
                        latest_processed,
                        None,
                        'No positions found',
                        {'display': 'block'},
                        {'display': 'none'}
                    )
                
                # Update controller data with processed Greeks
                controller.current_data = df_with_greeks
                
                # Get timestamp
                timestamp = controller.get_timestamp()
                timestamp_text = f'{len(df_with_greeks)} positions from: {timestamp}' if timestamp else f'{len(df_with_greeks)} positions loaded'
                
                # Convert DataFrame to dict for storage
                data_dict = controller.current_data.to_dict('records')
                
                logger.info(f"Auto-loaded {len(data_dict)} positions with Greeks after file completion")
                
                return (
                    latest_processed,
                    data_dict,
                    timestamp_text,
                    {'display': 'none'},
                    {'display': 'block'}
                )
            
        except Exception as e:
            logger.error(f"Error checking file completion: {e}")
        
        raise PreventUpdate 