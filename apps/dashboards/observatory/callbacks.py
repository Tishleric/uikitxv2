"""Simple callbacks for Observatory Dashboard"""

from dash import Input, Output, callback, State, html, ALL, ctx as dash_ctx
import pandas as pd
from datetime import datetime
import json

from .models import ObservatoryDataService
from lib.monitoring.decorators import monitor
from lib.components import Button
from lib.components.themes import default_theme


def register_callbacks(app):
    """Register simple callbacks for the dashboard"""
    
    # Initialize data service
    data_service = ObservatoryDataService()
    
    @app.callback(
        Output("observatory-filter-button-container", "children"),
        [Input("observatory-refresh-button", "n_clicks")],
        State("observatory-filter-state", "data"),
        prevent_initial_call=False
    )
    def update_filter_buttons(n_clicks, current_filter):
        """Dynamically create filter buttons based on available process groups"""
        try:
            # Get unique process groups
            process_groups = data_service.get_unique_process_groups()
            
            # Default to 'all' if current filter is not set
            if not current_filter:
                current_filter = "all"
            
            # Create buttons
            buttons = []
            
            # Always add "All" button first
            all_style = {
                "marginRight": "5px",
                "marginBottom": "5px",
                "backgroundColor": default_theme.primary if current_filter == "all" else default_theme.panel_bg,
                "color": default_theme.text_light,
                "border": f"1px solid {default_theme.secondary}"
            }
            buttons.append(
                Button(
                    id={"type": "filter-btn", "group": "all"},
                    label="All",
                    style=all_style,
                    n_clicks=0
                ).render()
            )
            
            # Add buttons for each process group
            for group in process_groups:
                style = {
                    "marginRight": "5px",
                    "marginBottom": "5px",
                    "backgroundColor": default_theme.primary if current_filter == group else default_theme.panel_bg,
                    "color": default_theme.text_light,
                    "border": f"1px solid {default_theme.secondary}"
                }
                buttons.append(
                    Button(
                        id={"type": "filter-btn", "group": group},
                        label=group,
                        style=style,
                        n_clicks=0
                    ).render()
                )
            
            return buttons
        except Exception as e:
            print(f"Error updating filter buttons: {e}")
            # Return at least the "All" button on error
            return [
                Button(
                    id={"type": "filter-btn", "group": "all"},
                    label="All",
                    style={
                        "marginRight": "5px",
                        "marginBottom": "5px",
                        "backgroundColor": default_theme.primary,
                        "color": default_theme.text_light,
                        "border": f"1px solid {default_theme.secondary}"
                    },
                    n_clicks=0
                ).render()
            ]
    
    @app.callback(
        [Output("observatory-filter-state", "data"),
         Output({"type": "filter-btn", "group": ALL}, "style")],
        Input({"type": "filter-btn", "group": ALL}, "n_clicks"),
        State({"type": "filter-btn", "group": ALL}, "id"),
        prevent_initial_call=True
    )
    def handle_filter_button_click(n_clicks_list, id_list):
        """Handle filter button clicks and update styles"""
        # Find which button was clicked
        ctx = dash_ctx
        if not ctx.triggered:
            return "all", []
        
        # Extract the group from the triggered button
        triggered_id = ctx.triggered[0]["prop_id"]
        # Parse the ID to get the group
        try:
            # Extract the ID part from the prop_id
            id_part = triggered_id.split(".")[0]
            # Parse the JSON ID
            id_dict = json.loads(id_part)
            selected_group = id_dict.get("group", "all")
        except:
            selected_group = "all"
        
        # Update button styles
        styles = []
        for btn_id in id_list:
            if btn_id["group"] == selected_group:
                # Active button
                styles.append({
                    "backgroundColor": default_theme.primary,
                    "color": default_theme.base_bg,
                    "border": f"1px solid {default_theme.primary}"
                })
            else:
                # Inactive button
                styles.append({
                    "backgroundColor": default_theme.panel_bg,
                    "color": default_theme.text_light,
                    "border": f"1px solid {default_theme.secondary}"
                })
        
        return selected_group, styles
    
    @app.callback(
        [Output("observatory-table", "data"),
         Output("observatory-last-refresh", "children")],
        [Input("observatory-refresh-button", "n_clicks"),
         Input("observatory-auto-refresh", "n_intervals"),
         Input("observatory-filter-state", "data")],
        prevent_initial_call=False
    )
    def refresh_table(n_clicks, n_intervals, current_filter):
        """Refresh the main data table"""
        try:
            print(f"[DEBUG] refresh_table called with filter: {current_filter}")
            
            # Get filtered data based on current filter
            if current_filter and current_filter != "all":
                df = data_service.filter_by_group(current_filter)
            else:
                df = data_service.get_trace_data(page=1, page_size=1000)
            
            if df.empty:
                return [], "Last refresh: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Get current timestamp
            timestamp = "Last refresh: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            return df.to_dict('records'), timestamp
        except Exception as e:
            print(f"Error refreshing table: {e}")
            return [], "Last refresh: Error occurred"
    
    @app.callback(
        Output("observatory-test-exception-button", "n_clicks"),
        Input("observatory-test-exception-button", "n_clicks"),
        prevent_initial_call=True
    )
    def test_exception_button(n_clicks):
        """Test button that intentionally fails to generate exception traces"""
        
        @monitor()
        def intentional_failure_for_testing(test_param="test_value", numeric_param=42):
            """Function that will intentionally fail and be tracked by monitor"""
            # This will be tracked as inputs
            error_message = "This is an intentional test exception!"
            
            # Simulate some processing
            result = test_param.upper()
            calculation = numeric_param * 2
            
            # Now intentionally fail
            raise ValueError(f"{error_message} Processed: {result}, Calculated: {calculation}")
        
        # Call the monitored function which will fail
        intentional_failure_for_testing("demo_input", 123)
        
        # This line won't be reached due to the exception
        return n_clicks 

    @app.callback(
        Output("observatory-exception-table", "data"),
        [Input("observatory-refresh-button", "n_clicks"),
         Input("observatory-auto-refresh", "n_intervals"),
         Input("observatory-filter-state", "data")],
        prevent_initial_call=False
    )
    def refresh_exception_table(n_clicks, n_intervals, current_filter):
        """Refresh the exception table"""
        try:
            # Get filtered data based on current filter
            if current_filter and current_filter != "all":
                df = data_service.filter_by_group(current_filter)
            else:
                df = data_service.get_trace_data(page=1, page_size=1000)
            
            if df.empty:
                return []
            
            # Filter for rows with error status (since we don't have exception column in JOIN)
            exception_df = df[df['status'] != 'OK']
            
            return exception_df.to_dict('records')
        except Exception as e:
            print(f"Error refreshing exception table: {e}")
            return [] 