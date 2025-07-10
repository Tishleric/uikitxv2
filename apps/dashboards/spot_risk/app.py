"""Spot Risk Dashboard Application

This module provides the main entry point for the Spot Risk dashboard.
It can be run standalone or integrated into the main application.
"""

import logging
import os
import sys

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

# Use conditional imports for module vs standalone
try:
    from .views import create_spot_risk_content
    from .callbacks import register_callbacks
    from .controller import SpotRiskController
except ImportError:
    from views import create_spot_risk_content
    from callbacks import register_callbacks
    from controller import SpotRiskController


def create_app() -> dash.Dash:
    """Create and configure the Spot Risk Dash app
    
    Returns:
        dash.Dash: Configured Dash application instance
    """
    # Initialize controller
    controller = SpotRiskController()
    
    # Load the latest CSV data
    controller.load_csv_data()

    # Create Dash app
    app = dash.Dash(
        __name__, 
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        suppress_callback_exceptions=True
    )

    # Set layout
    app.layout = create_spot_risk_content(controller=controller)
    
    # Register callbacks
    register_callbacks(app)

    # Run the app
    if __name__ == '__main__':
        PORT = 8055 # Assuming a default port for standalone testing
        print(f"Starting Spot Risk Dashboard on http://localhost:{PORT}")
        app.run_server(debug=True, port=PORT)
    
    return app


# For standalone testing and development
if __name__ == "__main__":
    app = create_app()
    print("Starting Spot Risk Dashboard on http://localhost:8055")
    app.run(debug=True, port=8055) 