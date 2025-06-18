"""Simple callbacks for Observatory Dashboard"""

from dash import Input, Output, callback
import pandas as pd
from datetime import datetime
import random

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
            # Get recent traces from the database
            df = data_service.get_recent_traces(limit=100)
            
            if df.empty:
                # Return empty list - no mock data
                return []
            
            # Format the dataframe for display - one row per input/output variable
            formatted_data = []
            for _, row in df.iterrows():
                timestamp = pd.to_datetime(row["timestamp"]).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                process = row.get("process", "Unknown")
                status = "ERROR" if row.get("exception") else "OK"
                exception = str(row.get("exception", ""))[:100] if row.get("exception") else ""
                
                # Parse args - show one row per argument
                args_str = row.get("args", "{}")
                try:
                    import json
                    args_dict = json.loads(args_str)
                    for arg_name, arg_value in args_dict.items():
                        formatted_data.append({
                            "process": process,
                            "data": arg_name,
                            "data_type": "input",
                            "data_value": str(arg_value)[:200],  # Truncate long values
                            "timestamp": timestamp,
                            "status": status,
                            "exception": exception
                        })
                except:
                    # If args parsing fails, show raw string
                    if args_str and args_str != "{}":
                        formatted_data.append({
                            "process": process,
                            "data": "args",
                            "data_type": "input",
                            "data_value": args_str[:200],
                            "timestamp": timestamp,
                            "status": status,
                            "exception": exception
                        })
                
                # Parse result - show as output
                result_str = row.get("result", "")
                if result_str:
                    formatted_data.append({
                        "process": process,
                        "data": "result",
                        "data_type": "output",
                        "data_value": str(result_str)[:200],
                        "timestamp": timestamp,
                        "status": status,
                        "exception": exception
                    })
            
            return formatted_data
            
        except Exception as e:
            print(f"Error loading trace data: {e}")
            # Return error message as data
            return [{
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "process": "Observatory",
                "function": "refresh_table_data",
                "duration_ms": 0,
                "status": f"Error: {str(e)}"
            }] 