"""P&L Dashboard Callbacks

This module contains all callback functions for P&L dashboard interactivity,
now working with TYU5 Excel data.
"""

import logging
from typing import List, Dict, Any, Tuple
from dash import Input, Output, State, callback, html
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from typing import Tuple, List, Dict
import logging
from datetime import datetime

from .app import tyu5_reader, create_summary_card, create_sheet_datatable
from lib.components.themes import default_theme
from lib.components.basic import Tabs
from lib.monitoring.decorators import monitor
from lib.trading.pnl_integration.data_reprocessor import DataReprocessor

logger = logging.getLogger(__name__)


@callback(
    [Output("pnl-summary-cards", "children"),
     Output("pnl-file-timestamp", "children"),
     Output("pnl-tabs", "children"),  # Changed from "tabs" to "children"
     Output("pnl-no-data", "style"),
     Output("pnl-tabs", "style")],
    [Input("pnl-interval-component", "n_intervals"),
     Input("pnl-refresh-button", "n_clicks")],
    prevent_initial_call=False
)
@monitor()
def update_dashboard_data(n_intervals: int, n_clicks: int) -> Tuple[List[html.Div], str, List, Dict, Dict]:
    """Update all dashboard data from TYU5 Excel files.
    
    Args:
        n_intervals: Number of interval updates
        n_clicks: Number of manual refresh clicks
        
    Returns:
        Tuple of (summary cards, file timestamp, tab data)
    """
    try:
        logger.info("Refreshing TYU5 data...")
        
        # Read latest TYU5 data
        sheets_data = tyu5_reader.read_all_sheets()
        summary_data = tyu5_reader.get_summary_data()
        file_timestamp = tyu5_reader.get_file_timestamp()
        
        # Create summary cards
        cards = [
            create_summary_card(
                "Total P&L",
                f"${summary_data.get('total_pnl', 0):,.2f}",
                color=default_theme.success if summary_data.get('total_pnl', 0) >= 0 else default_theme.danger
            ),
            create_summary_card(
                "Daily P&L", 
                f"${summary_data.get('daily_pnl', 0):,.2f}",
                color=default_theme.success if summary_data.get('daily_pnl', 0) >= 0 else default_theme.danger
            ),
            create_summary_card(
                "Realized P&L",
                f"${summary_data.get('realized_pnl', 0):,.2f}",
                color=default_theme.success if summary_data.get('realized_pnl', 0) >= 0 else default_theme.danger
            ),
            create_summary_card(
                "Unrealized P&L",
                f"${summary_data.get('unrealized_pnl', 0):,.2f}",
                color=default_theme.success if summary_data.get('unrealized_pnl', 0) >= 0 else default_theme.danger
            ),
            create_summary_card(
                "Active Positions",
                f"{int(summary_data.get('active_positions', 0))}",
                color=default_theme.text_light
            ),
            create_summary_card(
                "Total Trades",
                f"{int(summary_data.get('total_trades', 0))}",
                color=default_theme.text_light
            )
        ]
        
        # Create tabs for each sheet
        tab_list = []
        sheet_order = ['Positions', 'Trades', 'Risk_Matrix', 'Position_Breakdown']
        
        for sheet_name in sheet_order:
            if sheet_name in sheets_data:
                df = sheets_data[sheet_name]
                tab_label = sheet_name.replace('_', ' ')
                tab_content = create_sheet_datatable(sheet_name, df)
                # Create dbc.Tab component directly
                tab = dbc.Tab(
                    label=tab_label,
                    tab_id=f"pnl-tab-{sheet_name.lower()}",
                    children=tab_content.render()
                )
                tab_list.append(tab)
        
        logger.info(f"Successfully updated dashboard with {len(sheets_data)} sheets")
        
        # Debug logging
        logger.debug(f"Tab list has {len(tab_list)} tabs")
        for i, (label, content) in enumerate(tab_list):
            logger.debug(f"Tab {i}: {label}")
        
        # Show tabs, hide no-data message
        return cards, f"File: {file_timestamp}", tab_list, {'display': 'none'}, {'display': 'block'}
        
    except Exception as e:
        logger.error(f"Error updating dashboard: {e}")
        
        # Return empty state on error
        error_card = create_summary_card(
            "Error",
            "Failed to load data",
            color=default_theme.danger,
            subtitle=str(e)
        )
        
        # Hide tabs, show no-data message
        return [error_card], "Error loading file", [], {'display': 'block'}, {'display': 'none'}


@callback(
    [Output("pnl-reprocess-status", "children"),
     Output("pnl-reprocess-status", "style"),
     Output("pnl-reprocess-button", "disabled"),
     Output("pnl-reprocess-button", "n_clicks")],
    [Input("pnl-reprocess-button", "n_clicks")],
    [State("pnl-reprocess-button", "n_clicks_timestamp")],
    prevent_initial_call=True
)
@monitor()
def handle_reprocess_button(n_clicks: int, last_click_timestamp: int) -> Tuple:
    """Handle reprocess button clicks with double-click protection.
    
    Args:
        n_clicks: Number of button clicks
        last_click_timestamp: Timestamp of last click
        
    Returns:
        Tuple of (status message, status style, button disabled state, reset clicks)
    """
    if not n_clicks:
        raise PreventUpdate
    
    # Require double-click within 5 seconds
    import time
    current_time = time.time() * 1000  # Convert to milliseconds
    
    # First click - show warning
    if n_clicks == 1:
        warning_msg = html.Div([
            html.Strong("⚠️ WARNING: ", style={'color': default_theme.danger}),
            "This will drop all tables and reprocess from scratch. ",
            html.Strong("Click again within 5 seconds to confirm.")
        ])
        
        style = {
            'marginTop': '10px',
            'padding': '10px',
            'backgroundColor': default_theme.panel_bg,
            'borderRadius': '4px',
            'fontSize': '14px',
            'border': f'1px solid {default_theme.danger}',
            'display': 'block'
        }
        
        return warning_msg, style, False, n_clicks
    
    # Check if this is a valid double-click
    if last_click_timestamp and (current_time - last_click_timestamp) > 5000:
        # Too long between clicks, reset
        return "", {'display': 'none'}, False, 0
    
    # Valid double-click - proceed with reprocessing
    try:
        logger.info("Starting full data reprocessing...")
        
        # Show initial status
        status_msg = html.Div([
            html.Strong("🔄 Reprocessing Started", style={'color': '#FFA500'}),
            html.Br(),
            "Step 1/4: Dropping tables..."
        ])
        
        style = {
            'marginTop': '10px',
            'padding': '10px',
            'backgroundColor': default_theme.panel_bg,
            'borderRadius': '4px',
            'fontSize': '14px',
            'border': f'1px solid #FFA500',
            'display': 'block'
        }
        
        # Run reprocessing
        reprocessor = DataReprocessor()
        results = reprocessor.orchestrate_full_reprocess()
        
        # Build result message
        if results['overall_success']:
            status_msg = html.Div([
                html.Strong("✅ Reprocessing Complete!", style={'color': default_theme.success}),
                html.Br(),
                f"Time: {results['elapsed_time']:.1f} seconds",
                html.Br(),
                f"Futures: {results['summary']['futures_records']} records",
                html.Br(),
                f"Options: {results['summary']['options_records']} records",
                html.Br(),
                f"Trades: {results['summary']['trades_processed']} processed",
                html.Br(),
                html.Small("TYU5 calculation triggered automatically.", 
                          style={'color': default_theme.text_subtle})
            ])
            
            style['border'] = f'1px solid {default_theme.success}'
        else:
            error_count = results['summary'].get('total_errors', 0)
            status_msg = html.Div([
                html.Strong("❌ Reprocessing Failed", style={'color': default_theme.danger}),
                html.Br(),
                f"Errors encountered: {error_count}",
                html.Br(),
                "Check logs for details."
            ])
            
            style['border'] = f'1px solid {default_theme.danger}'
        
        # Reset button and return status
        return status_msg, style, False, 0
        
    except Exception as e:
        logger.error(f"Reprocessing failed: {e}")
        
        error_msg = html.Div([
            html.Strong("❌ Error:", style={'color': default_theme.danger}),
            html.Br(),
            str(e)
        ])
        
        style = {
            'marginTop': '10px',
            'padding': '10px',
            'backgroundColor': default_theme.panel_bg,
            'borderRadius': '4px',
                    'fontSize': '14px',
            'border': f'1px solid {default_theme.danger}',
            'display': 'block'
        }
        
        return error_msg, style, False, 0


# Register callbacks function for main app integration
def register_callbacks(app):
    """Register all callbacks with the Dash app.
    
    This function is called by the main app to register callbacks.
    Since we use the @callback decorator, callbacks are automatically
    registered when this module is imported.
    
    Args:
        app: The Dash app instance
    """
    logger.info("P&L tracking callbacks registered")
    # Callbacks are already registered via @callback decorator
    pass 