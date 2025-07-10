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
         Output('spot-risk-loading', 'children')],
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
                    no_update
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
                    no_update
                )
            
            # Check if any positions were found
            if df_with_greeks.empty:
                logger.info("No positions found in the data")
                return (
                    None,
                    'No positions found',
                    {'display': 'block'},
                    {'display': 'none'},
                    no_update
                )
            
            # Update controller data with processed Greeks
            controller.current_data = df_with_greeks
            
            # Get timestamp
            timestamp = controller.get_timestamp()
            timestamp_text = f'{len(df_with_greeks)} positions from: {timestamp}' if timestamp else f'{len(df_with_greeks)} positions loaded'
            
            # Convert DataFrame to dict for storage
            data_dict = controller.current_data.to_dict('records')
            
            logger.info(f"Loaded {len(data_dict)} positions with Greeks")
            
            return (
                data_dict,
                timestamp_text,
                {'display': 'none'},  # Hide no-data message
                {'display': 'block'},  # Show table
                no_update
            )
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return (
                None,
                f'Error: {str(e)}',
                {'display': 'block'},
                {'display': 'none'},
                no_update
            )
    
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
         Input('spot-risk-cross-greeks', 'value')],
        prevent_initial_call=True
    )
    @monitor()
    def update_table_data(stored_data, expiry_filter, type_filter, strike_range,
                          base_checked, first_checked, second_checked, 
                          third_checked, cross_checked):
        """Update table data based on filters and Greek selections
        
        Returns:
            tuple: (filtered_data, visible_columns)
        """
        if not stored_data:
            return [], []
        
        # Start with all data
        filtered_data = stored_data.copy()
        
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
        
        # Build visible columns based on Greek selections
        column_defs = get_column_definitions()
        visible_columns = []
        
        # Always include base columns
        visible_columns.extend(column_defs['base'])
        
        # Add columns based on checkboxes
        if first_checked and '1st' in first_checked:
            visible_columns.extend(column_defs['1st'])
        
        if second_checked and '2nd' in second_checked:
            visible_columns.extend(column_defs['2nd'])
            
        if third_checked and '3rd' in third_checked:
            visible_columns.extend(column_defs['3rd'])
            
        if cross_checked and 'cross' in cross_checked:
            visible_columns.extend(column_defs['cross'])
        
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
    
    @app.callback(
        Output('spot-risk-export-btn', 'n_clicks'),
        [Input('spot-risk-export-btn', 'n_clicks')],
        [State('spot-risk-data-table', 'data'),
         State('spot-risk-data-table', 'columns')],
        prevent_initial_call=True
    )
    @monitor()
    def export_data(n_clicks, table_data, table_columns):
        """Export visible data to CSV
        
        Note: In a real implementation, this would trigger a download.
        For now, we just log the export request.
        """
        if n_clicks and table_data and table_columns:
            logger.info(f"Export requested: {len(table_data)} rows, {len(table_columns)} columns")
            # In a real app, you would:
            # 1. Convert table_data to DataFrame
            # 2. Generate CSV
            # 3. Return a download link or trigger download
        
        # Reset click count to allow multiple exports
        return 0
    
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
         Input('spot-risk-cross-greeks', 'value')],
        [State('spot-risk-data-store', 'data'),
         State('spot-risk-display-store', 'data')],
        prevent_initial_call=True
    )
    @monitor()
    def update_greek_graphs(table_clicks, graph_clicks, first_order, second_order, 
                            third_order, cross_greeks, stored_data, view_state):
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
        should_generate = False
        
        if triggered_id == 'spot-risk-graph-view-btn':
            logger.info("Switched to graph view, generating graphs")
            should_generate = True
        elif current_view == 'graph' and any(x in triggered_id for x in ['order', 'greeks']):
            logger.info(f"Greek selection changed in graph view: {triggered_id}")
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
            # Convert stored data back to DataFrame for controller
            df = pd.DataFrame(stored_data)
            controller.current_data = df
            
            # Generate profiles for selected Greeks grouped by expiry
            logger.info(f"Generating profiles for {len(selected_greeks)} Greeks by expiry")
            profiles_by_expiry = controller.generate_greek_profiles_by_expiry(selected_greeks)
            
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
            
            # Create summary info text
            info_text = f'{len(profiles_by_expiry)} expiries | {total_positions} total positions'
            
            logger.info(f"Successfully created graphs for {len(profiles_by_expiry)} expiries")
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