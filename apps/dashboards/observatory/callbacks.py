"""Simple callbacks for Observatory Dashboard"""

from dash import Input, Output, callback
import pandas as pd
from datetime import datetime

from .models import ObservatoryDataService


def register_callbacks(app):
    """Register simple callbacks for the dashboard"""
    
    # Initialize data service
    data_service = ObservatoryDataService()
    
    @app.callback(
        Output("observatory-table", "data"),
        Input("observatory-refresh-button", "n_clicks"),
        prevent_initial_call=False
    )
    def refresh_table_data(n_clicks):
        """Refresh the table with latest trace data"""
        try:
            # Get trace data directly - it's already in the perfect format!
            df, total_rows = data_service.get_trace_data(
                page=1,
                page_size=100  # Show last 100 entries
            )
            
            if df.empty:
                # Return empty list - no data
                return []
            
            # The data is already in the right format from get_trace_data()
            # Just need to format timestamp and rename columns for display
            formatted_data = []
            for _, row in df.iterrows():
                formatted_data.append({
                    "process": row["process"],
                    "data": row["data"],
                    "data_type": row["data_type"],
                    "data_value": str(row["data_value"])[:200],  # Truncate long values
                    "timestamp": pd.to_datetime(row["timestamp"]).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
                    "status": row["status"],
                    "exception": row.get("exception", "")
                })
            
            return formatted_data
            
        except Exception as e:
            print(f"Error loading trace data: {e}")
            # Return error message as data
            return [{
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "process": "Observatory",
                "data": "error",
                "data_type": "ERROR",
                "data_value": str(e),
                "status": "ERROR",
                "exception": str(e)
            }] 