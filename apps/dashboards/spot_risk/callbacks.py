"""Spot Risk Dashboard Callbacks

This module handles all callback logic for the Spot Risk dashboard.
Follows the Controller layer of MVC pattern - business logic and data flow.
"""

import dash
from dash import Input, Output, State, callback, no_update, dash_table
from dash.exceptions import PreventUpdate
import logging
from typing import List, Dict, Any, Tuple

from lib.monitoring.decorators import monitor
from lib.components.themes.colour_palette import default_theme
from .controller import SpotRiskController
from .views import get_column_definitions

logger = logging.getLogger(__name__)


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
                    'No data loaded',
                    {'display': 'block'},
                    {'display': 'none'},
                    no_update
                )
            
            # Process Greeks
            logger.info("Processing Greeks for loaded data...")
            df_with_greeks = controller.process_greeks()
            
            if df_with_greeks is None:
                logger.error("Failed to process Greeks")
                return (
                    None,
                    'Error processing Greeks',
                    {'display': 'block'},
                    {'display': 'none'},
                    no_update
                )
            
            # Update controller data with processed Greeks
            controller.current_data = df_with_greeks
            
            # Get timestamp
            timestamp = controller.get_timestamp()
            timestamp_text = f'Data from: {timestamp}' if timestamp else 'Data loaded'
            
            # Convert DataFrame to dict for storage
            data_dict = controller.current_data.to_dict('records')
            
            logger.info(f"Loaded {len(data_dict)} rows of spot risk data with Greeks")
            
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
            df_with_greeks = controller.process_greeks()
            
            if df_with_greeks is None:
                logger.error("Failed to process Greeks during auto-refresh")
                # Don't update UI on error during auto-refresh
                raise PreventUpdate
            
            # Update controller data with processed Greeks
            controller.current_data = df_with_greeks
            
            # Get timestamp
            timestamp = controller.get_timestamp()
            timestamp_text = f'Data from: {timestamp} (Auto-refreshed)' if timestamp else 'Data loaded (Auto-refreshed)'
            
            # Convert DataFrame to dict for storage
            data_dict = controller.current_data.to_dict('records')
            
            logger.info(f"Auto-refreshed {len(data_dict)} rows of spot risk data with Greeks")
            
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