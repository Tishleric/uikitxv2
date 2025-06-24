"""Simple Observatory Dashboard Application"""

import dash
from dash import html, dcc

from .views import create_observatory_content
from .callbacks import register_callbacks


def create_observatory_app():
    """Create the simple Observatory dashboard Dash app"""
    # Create Dash app
    app = dash.Dash(
        __name__,
        suppress_callback_exceptions=True,
        assets_folder="../../../assets",  # Use main project assets
    )
    
    # Set layout - just the simple DataTable
    app.layout = create_observatory_content()
    
    # Register callbacks
    register_callbacks(app)
    
    return app


# For standalone testing
if __name__ == "__main__":
    app = create_observatory_app()
    app.run(debug=True, port=8052) 