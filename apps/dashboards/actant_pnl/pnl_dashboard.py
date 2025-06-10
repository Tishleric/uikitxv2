"""
PnL Analysis Dashboard

Dash application for comparing Actant option pricing with Taylor Series approximations.
Uses wrapped UIKitXv2 components for consistent theming and styling.
"""

import dash
from dash import html, dcc, Input, Output, State, callback_context, no_update
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from pathlib import Path
import os
import sys




# Get the project root
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent

# Add the project root to Python path
sys.path.insert(0, str(PROJECT_ROOT))

from lib.components import (
    Container, Grid, Button, DataTable, Graph, Loading
)
from lib.components.themes import default_theme

# Import our data modules
from lib.trading.actant.pnl.parser import load_latest_data
from lib.trading.actant.pnl.calculations import PnLCalculator
from lib.trading.actant.pnl.formatter import PnLDataFormatter


class PnLDashboard:
    """Main PnL Dashboard application."""
    
    def __init__(self, data_dir: str = None, id_prefix: str = ""):
        """
        Initialize dashboard.
        
        Args:
            data_dir: Directory containing CSV files (defaults to data/input/actant_pnl)
            id_prefix: Prefix for component IDs to avoid conflicts
        """
        if data_dir is None:
            # Default to the project's data directory
            project_root = Path(__file__).parent.parent.parent.parent  # Navigate up to project root
            data_dir = project_root / "data" / "input" / "actant_pnl"
        
        self.data_dir = Path(data_dir).resolve()  # Use absolute path
        self.theme = default_theme
        self.id_prefix = id_prefix  # For unique IDs when embedded
        
        # Load available data
        self.available_expirations = []
        self.all_greeks = {}
        success, message = self._load_available_data()
        if not success:
            print(f"[WARNING] Initial data load failed: {message}")
        
    def _id(self, base_id: str) -> str:
        """Generate prefixed ID to avoid conflicts."""
        return f"{self.id_prefix}{base_id}" if self.id_prefix else base_id
    
    def _load_available_data(self):
        """Load available data on initialization."""
        try:
            print(f"[INFO] Searching for CSV files in: {self.data_dir}")
            
            # List CSV files in the directory for debugging
            csv_files = list(self.data_dir.glob("GE_*.csv"))
            if csv_files:
                print(f"[INFO] Found CSV files: {[f.name for f in csv_files]}")
            else:
                print(f"[WARNING] No CSV files matching pattern 'GE_*.csv' found in {self.data_dir}")
                
            df, all_greeks = load_latest_data(self.data_dir)
            self.all_greeks = all_greeks
            self.available_expirations = list(all_greeks.keys())
            print(f"[SUCCESS] Loaded data for {len(self.available_expirations)} expirations: {self.available_expirations}")
            return True, f"Loaded data for {len(self.available_expirations)} expirations"
        except Exception as e:
            print(f"[ERROR] Error loading data: {e}")
            import traceback
            traceback.print_exc()
            self.available_expirations = []
            self.all_greeks = {}
            return False, f"Error loading data: {str(e)}"
    
    def refresh_data(self):
        """Refresh data from CSV files and return status."""
        return self._load_available_data()
    
    def create_header(self) -> html.Div:
        """Create dashboard header with title and info."""
        return Container(
            id="pnl-header",
            children=[
                html.H2(
                    "Actant PnL Analysis Dashboard",
                    style={
                        "color": self.theme.text_light,
                        "textAlign": "center",
                        "marginBottom": "10px",
                        "fontFamily": "Inter, sans-serif"
                    }
                ),
                html.P(
                    "Compare option pricing methods: Actant vs Taylor Series approximations",
                    style={
                        "color": self.theme.text_subtle,
                        "textAlign": "center",
                        "marginBottom": "20px",
                        "fontSize": "14px"
                    }
                )
            ],
            style={"marginBottom": "20px"}
        ).render()
    
    def create_controls(self) -> html.Div:
        """Create control panel with expiration selector and toggle buttons."""
        # Create expiration options
        expiration_options = [{"label": exp, "value": exp} for exp in self.available_expirations]
        default_expiration = self.available_expirations[0] if self.available_expirations else None
        
        return Container(
            id="pnl-controls",
            children=[
                Grid(
                    id="controls-grid",
                    children=[
                        # Data Refresh Section
                        (Container(
                            id="refresh-container",
                            children=[
                                html.H4("Data Control", style={
                                    "color": self.theme.text_light,
                                    "marginBottom": "10px",
                                    "fontSize": "16px",
                                    "fontWeight": "500"
                                }),
                                Button(
                                    id=self._id("refresh-data-button"),
                                    label="Refresh Data",
                                    theme=self.theme,
                                    n_clicks=0,
                                    style={
                                        "width": "100%",
                                        "marginBottom": "10px"
                                    }
                                ).render(),
                                html.Div(
                                    id=self._id("refresh-status"),
                                    children=f"Loaded: {len(self.available_expirations)} expirations",
                                    style={
                                        "color": self.theme.text_subtle,
                                        "fontSize": "12px",
                                        "textAlign": "center"
                                    }
                                )
                            ],
                            style={
                                "backgroundColor": self.theme.panel_bg,
                                "padding": "15px",
                                "borderRadius": "5px"
                            }
                        ).render(), {"xs": 12, "md": 2}),
                        
                        # Expiration Selection
                        (Container(
                            id="expiration-container",
                            children=[
                                html.H4("Expiration", style={
                                    "color": self.theme.text_light,
                                    "marginBottom": "10px",
                                    "fontSize": "16px",
                                    "fontWeight": "500"
                                }),
                                dcc.Dropdown(
                                    id=self._id("expiration-dropdown"),
                                    options=expiration_options,
                                    value=default_expiration,
                                    style={
                                        "backgroundColor": self.theme.base_bg,
                                        "color": self.theme.text_light,
                                        "border": f"1px solid {self.theme.secondary}",
                                        "borderRadius": "4px"
                                    },
                                    className="custom-dropdown"
                                )
                            ],
                            style={
                                "backgroundColor": self.theme.panel_bg,
                                "padding": "15px",
                                "borderRadius": "5px"
                            }
                        ).render(), {"xs": 12, "md": 3}),
                        
                        # Toggle Controls
                        (Container(
                            id="toggle-controls-container",
                            children=[
                                html.H4("View Options", style={
                                    "color": self.theme.text_light,
                                    "marginBottom": "15px",
                                    "fontSize": "16px",
                                    "fontWeight": "500"
                                }),
                                
                                # Option Type Toggle (Call/Put)
                                html.Div([
                                    html.P("Option Type:", style={
                                        "color": self.theme.text_light,
                                        "marginBottom": "5px",
                                        "fontSize": "14px",
                                        "textAlign": "center"
                                    }),
                                    html.Div([
                                        Button(
                                            id=self._id("btn-option-call"),
                                            label="Call",
                                            theme=self.theme,
                                            n_clicks=1,  # Default selected
                                            style={
                                                'borderTopRightRadius': '0',
                                                'borderBottomRightRadius': '0',
                                                'borderRight': 'none',
                                                'backgroundColor': self.theme.primary
                                            }
                                        ).render(),
                                        Button(
                                            id=self._id("btn-option-put"),
                                            label="Put",
                                            theme=self.theme,
                                            n_clicks=0,
                                            style={
                                                'borderTopLeftRadius': '0',
                                                'borderBottomLeftRadius': '0',
                                                'backgroundColor': self.theme.panel_bg
                                            }
                                        ).render()
                                    ], style={"display": "flex", "justifyContent": "center"})
                                ], style={"marginBottom": "15px"}),
                                
                                # View Type Toggle (Graph/Table)
                                html.Div([
                                    html.P("View:", style={
                                        "color": self.theme.text_light,
                                        "marginBottom": "5px",
                                        "fontSize": "14px",
                                        "textAlign": "center"
                                    }),
                                    html.Div([
                                        Button(
                                            id=self._id("btn-view-graph"),
                                            label="Graph",
                                            theme=self.theme,
                                            n_clicks=1,  # Default selected
                                            style={
                                                'borderTopRightRadius': '0',
                                                'borderBottomRightRadius': '0',
                                                'borderRight': 'none',
                                                'backgroundColor': self.theme.primary
                                            }
                                        ).render(),
                                        Button(
                                            id=self._id("btn-view-table"),
                                            label="Table",
                                            theme=self.theme,
                                            n_clicks=0,
                                            style={
                                                'borderTopLeftRadius': '0',
                                                'borderBottomLeftRadius': '0',
                                                'backgroundColor': self.theme.panel_bg
                                            }
                                        ).render()
                                    ], style={"display": "flex", "justifyContent": "center"})
                                ])
                            ],
                            style={
                                "backgroundColor": self.theme.panel_bg,
                                "padding": "15px",
                                "borderRadius": "5px"
                            }
                        ).render(), {"xs": 12, "md": 4}),
                        
                        # Summary Info
                        (Container(
                            id="summary-info-container",
                            children=[
                                html.H4("Current Data", style={
                                    "color": self.theme.text_light,
                                    "marginBottom": "10px",
                                    "fontSize": "16px",
                                    "fontWeight": "500"
                                }),
                                html.Div(id=self._id("data-summary-info"), children=[
                                    html.P(f"Available: {len(self.available_expirations)} expirations", 
                                          style={"color": self.theme.text_subtle, "fontSize": "14px", "marginBottom": "5px"}),
                                    html.P("Select expiration to view analysis", 
                                          style={"color": self.theme.text_subtle, "fontSize": "14px"})
                                ])
                            ],
                            style={
                                "backgroundColor": self.theme.panel_bg,
                                "padding": "15px",
                                "borderRadius": "5px"
                            }
                        ).render(), {"xs": 12, "md": 3})
                    ]
                ).render()
            ],
            style={"marginBottom": "20px"}
        ).render()
    
    def create_content_area(self) -> html.Div:
        """Create main content area for graphs and tables."""
        return Container(
            id="pnl-content",
            children=[
                Loading(
                    id="content-loading",
                    children=[
                        html.Div(
                            id=self._id("pnl-display-content"),
                            children=[
                                html.Div(
                                    "Select data to view analysis",
                                    style={
                                        "textAlign": "center",
                                        "color": self.theme.text_subtle,
                                        "padding": "40px",
                                        "fontSize": "16px"
                                    }
                                )
                            ]
                        )
                    ]
                ).render()
            ]
        ).render()
    
    def create_layout(self) -> html.Div:
        """Create complete dashboard layout."""
        # Set initial expiration to first available
        initial_expiration = self.available_expirations[0] if self.available_expirations else None
        
        return html.Div([
            # Data storage
            dcc.Store(id=self._id("current-view-state"), data={"view": "graph", "option": "call", "expiration": initial_expiration}),
            
            # Dashboard layout
            self.create_header(),
            self.create_controls(),
            self.create_content_area()
        ], style={
            "backgroundColor": self.theme.base_bg,
            "minHeight": "100vh",
            "padding": "20px"
        })
    
    def register_callbacks(self, app: dash.Dash):
        """Register all dashboard callbacks."""
        print(f"[DEBUG] Registering callbacks for PnLDashboard with prefix: '{self.id_prefix}'")
        print(f"[DEBUG] Available expirations: {self.available_expirations}")
        
        @app.callback(
            Output(self._id("current-view-state"), "data"),
            [Input(self._id("btn-view-graph"), "n_clicks"),
             Input(self._id("btn-view-table"), "n_clicks"),
             Input(self._id("btn-option-call"), "n_clicks"),
             Input(self._id("btn-option-put"), "n_clicks"),
             Input(self._id("expiration-dropdown"), "value")],
            [State(self._id("current-view-state"), "data")],
            prevent_initial_call=False
        )
        def update_view_state(graph_clicks, table_clicks, call_clicks, put_clicks, 
                            selected_expiration, current_state):
            """Update view state based on user interactions."""
            if current_state is None:
                current_state = {"view": "graph", "option": "call", "expiration": selected_expiration}
            
            ctx = callback_context
            if ctx.triggered:
                button_id = ctx.triggered[0]["prop_id"].split(".")[0]
                
                if button_id == self._id("btn-view-graph"):
                    current_state["view"] = "graph"
                elif button_id == self._id("btn-view-table"):
                    current_state["view"] = "table"
                elif button_id == self._id("btn-option-call"):
                    current_state["option"] = "call"
                elif button_id == self._id("btn-option-put"):
                    current_state["option"] = "put"
                elif button_id == self._id("expiration-dropdown"):
                    current_state["expiration"] = selected_expiration
            
            return current_state
        
        @app.callback(
            [Output(self._id("btn-view-graph"), "style"),
             Output(self._id("btn-view-table"), "style"),
             Output(self._id("btn-option-call"), "style"),
             Output(self._id("btn-option-put"), "style")],
            [Input(self._id("current-view-state"), "data")],
            prevent_initial_call=False
        )
        def update_button_styles(view_state):
            """Update button styles based on current view state."""
            if not view_state:
                view_state = {"view": "graph", "option": "call"}
            
            # Base styles for active/inactive buttons
            active_style = {
                'backgroundColor': self.theme.primary,
                'borderColor': self.theme.primary,
                'color': self.theme.text_light
            }
            inactive_style = {
                'backgroundColor': self.theme.panel_bg,
                'borderColor': self.theme.secondary,
                'color': self.theme.text_light
            }
            
            # Apply view toggle styles (connected buttons)
            graph_style = {**active_style, 'borderTopRightRadius': '0', 'borderBottomRightRadius': '0', 'borderRight': 'none'} if view_state.get("view") == "graph" else {**inactive_style, 'borderTopRightRadius': '0', 'borderBottomRightRadius': '0', 'borderRight': 'none'}
            table_style = {**active_style, 'borderTopLeftRadius': '0', 'borderBottomLeftRadius': '0'} if view_state.get("view") == "table" else {**inactive_style, 'borderTopLeftRadius': '0', 'borderBottomLeftRadius': '0'}
            
            # Apply option toggle styles (connected buttons)
            call_style = {**active_style, 'borderTopRightRadius': '0', 'borderBottomRightRadius': '0', 'borderRight': 'none'} if view_state.get("option") == "call" else {**inactive_style, 'borderTopRightRadius': '0', 'borderBottomRightRadius': '0', 'borderRight': 'none'}
            put_style = {**active_style, 'borderTopLeftRadius': '0', 'borderBottomLeftRadius': '0'} if view_state.get("option") == "put" else {**inactive_style, 'borderTopLeftRadius': '0', 'borderBottomLeftRadius': '0'}
            
            return graph_style, table_style, call_style, put_style
        
        @app.callback(
            Output(self._id("pnl-display-content"), "children"),
            [Input(self._id("current-view-state"), "data")],
            prevent_initial_call=False
        )
        def update_display_content(view_state):
            """Update main display content based on current selections."""
            print(f"[DEBUG] update_display_content called with view_state: {view_state}")
            print(f"[DEBUG] Available greeks: {list(self.all_greeks.keys())}")
            
            if not view_state or not view_state.get("expiration"):
                return html.Div(
                    "Select an expiration to view analysis",
                    style={
                        "textAlign": "center",
                        "color": self.theme.text_subtle,
                        "padding": "40px",
                        "fontSize": "16px"
                    }
                )
            
            expiration = view_state.get("expiration")
            if expiration not in self.all_greeks:
                return html.Div(
                    f"No data available for expiration: {expiration}",
                    style={
                        "textAlign": "center",
                        "color": self.theme.text_subtle,
                        "padding": "40px",
                        "fontSize": "16px"
                    }
                )
            
            view_type = view_state.get("view", "graph")
            option_type = view_state.get("option", "call")
            
            # Get the OptionGreeks for selected expiration
            greeks = self.all_greeks[expiration]
            
            if view_type == "graph":
                return self.create_pnl_graph(greeks, option_type)
            else:
                return self.create_pnl_table(greeks, option_type)
        
        @app.callback(
            Output(self._id("data-summary-info"), "children"),
            [Input(self._id("current-view-state"), "data")],
            prevent_initial_call=False
        )
        def update_data_summary(view_state):
            """Update data summary information."""
            if not view_state or not view_state.get("expiration"):
                return [
                    html.P(f"Available: {len(self.available_expirations)} expirations", 
                          style={"color": self.theme.text_subtle, "fontSize": "14px", "marginBottom": "5px"}),
                    html.P("Select expiration to view analysis", 
                          style={"color": self.theme.text_subtle, "fontSize": "14px"})
                ]
            
            expiration = view_state.get("expiration")
            if expiration in self.all_greeks:
                greeks = self.all_greeks[expiration]
                return [
                    html.P(f"Expiration: {expiration}", 
                          style={"color": self.theme.text_light, "fontSize": "14px", "fontWeight": "500", "marginBottom": "5px"}),
                    html.P(f"Underlying: ${greeks.underlying_price:.3f}", 
                          style={"color": self.theme.text_subtle, "fontSize": "14px", "marginBottom": "5px"}),
                    html.P(f"Time to expiry: {greeks.time_to_expiry:.3f} days", 
                          style={"color": self.theme.text_subtle, "fontSize": "14px"})
                ]
            else:
                return [
                    html.P(f"Expiration: {expiration}", 
                          style={"color": self.theme.text_light, "fontSize": "14px", "fontWeight": "500", "marginBottom": "5px"}),
                    html.P("No data available", 
                          style={"color": self.theme.error, "fontSize": "14px"})
                ]
        
        @app.callback(
            [Output(self._id("expiration-dropdown"), "options"),
             Output(self._id("expiration-dropdown"), "value"),
             Output(self._id("refresh-status"), "children"),
             Output(self._id("refresh-status"), "style")],
            [Input(self._id("refresh-data-button"), "n_clicks")],
            prevent_initial_call=True
        )
        def refresh_data_callback(n_clicks):
            """Handle refresh data button click."""
            if n_clicks is None or n_clicks == 0:
                return no_update, no_update, no_update, no_update
            
            # Refresh the data
            success, message = self.refresh_data()
            
            # Create new expiration options
            expiration_options = [{"label": exp, "value": exp} for exp in self.available_expirations]
            
            # Set default expiration (first available or None)
            default_expiration = self.available_expirations[0] if self.available_expirations else None
            
            # Update status message and styling
            if success:
                status_style = {
                    "color": self.theme.success,
                    "fontSize": "12px",
                    "textAlign": "center"
                }
                status_message = f"✓ {message}"
            else:
                status_style = {
                    "color": self.theme.error if hasattr(self.theme, 'error') else "#ff6b6b",
                    "fontSize": "12px",
                    "textAlign": "center"
                }
                status_message = f"✗ {message}"
            
            print(f"[INFO] Data refresh completed: {message}")
            return expiration_options, default_expiration, status_message, status_style
    
    def create_pnl_graph(self, greeks, option_type: str) -> html.Div:
        """Create both price and PnL comparison graphs using real data."""
        # Calculate PnL data using real calculations
        pnl_df = PnLCalculator.calculate_all_pnls(greeks, option_type)
        
        # Create container for both graphs side-by-side
        return html.Div(
            id="graphs-container",
            children=[
                # Side-by-side container
                html.Div([
                    # Price comparison graph (left)
                    html.Div([
                        html.H4(f"{option_type.title()} Price: Actant vs Taylor Series", style={
                            "color": self.theme.text_light,
                            "textAlign": "center",
                            "marginBottom": "10px",
                            "fontSize": "16px",
                            "fontWeight": "500"
                        }),
                        self._create_price_graph(pnl_df, option_type)
                    ], style={
                        "width": "49%",
                        "display": "inline-block",
                        "verticalAlign": "top",
                        "paddingRight": "1%"
                    }),
                    
                    # PnL comparison graph (right)
                    html.Div([
                        html.H4(f"{option_type.title()} PnL: Actant vs Taylor Series", style={
                            "color": self.theme.text_light,
                            "textAlign": "center",
                            "marginBottom": "10px",
                            "fontSize": "16px",
                            "fontWeight": "500"
                        }),
                        self._create_pnl_only_graph(pnl_df, option_type)
                    ], style={
                        "width": "49%",
                        "display": "inline-block",
                        "verticalAlign": "top",
                        "paddingLeft": "1%"
                    })
                ], style={
                    "width": "100%",
                    "backgroundColor": self.theme.panel_bg,
                    "padding": "15px",
                    "borderRadius": "8px",
                    "marginBottom": "20px"
                })
            ]
        )
    
    def _create_price_graph(self, pnl_df: pd.DataFrame, option_type: str):
        """Create price comparison graph."""
        fig = go.Figure()
        
        # Add traces for price comparison
        fig.add_trace(go.Scatter(
            x=pnl_df['shock_bp'],
            y=pnl_df['actant_price'],
            mode='lines+markers',
            name='Actant',
            line=dict(color=self.theme.primary, width=3),
            marker=dict(size=6)
        ))
        
        fig.add_trace(go.Scatter(
            x=pnl_df['shock_bp'],
            y=pnl_df['ts0_price'],
            mode='lines+markers',
            name='TS from ATM',
            line=dict(color=self.theme.accent, width=3),
            marker=dict(size=6)
        ))
        
        fig.add_trace(go.Scatter(
            x=pnl_df['shock_bp'],
            y=pnl_df['ts_neighbor_price'],
            mode='lines+markers',
            name='TS from Neighbor',
            line=dict(color=self.theme.success, width=3),
            marker=dict(size=6)
        ))
        
        # Update layout
        fig.update_layout(
            xaxis_title="Shift in bp",
            yaxis_title=f"{option_type.title()} Price ($)",
            hovermode='x unified',
            plot_bgcolor=self.theme.panel_bg,
            paper_bgcolor=self.theme.panel_bg,
            font={'color': self.theme.text_light},
            legend=dict(
                bgcolor=self.theme.panel_bg,
                bordercolor=self.theme.secondary,
                borderwidth=1
            ),
            xaxis=dict(
                gridcolor=self.theme.secondary,
                zerolinecolor=self.theme.text_subtle
            ),
            yaxis=dict(
                gridcolor=self.theme.secondary,
                zerolinecolor=self.theme.text_subtle
            ),
            margin=dict(t=10, b=40),
            autosize=False,
            width=600,
            height=400
        )
        
        return Graph(
            id="price-graph",
            figure=fig,
            theme=self.theme,
            style={"height": "400px"}
        ).render()
    
    def _create_pnl_only_graph(self, pnl_df: pd.DataFrame, option_type: str):
        """Create PnL comparison graph."""
        fig = go.Figure()
        
        # Add traces for PnL comparison
        fig.add_trace(go.Scatter(
            x=pnl_df['shock_bp'],
            y=pnl_df['actant_pnl'],
            mode='lines+markers',
            name='Actant',
            line=dict(color=self.theme.primary, width=3),
            marker=dict(size=6)
        ))
        
        fig.add_trace(go.Scatter(
            x=pnl_df['shock_bp'],
            y=pnl_df['ts0_pnl'],
            mode='lines+markers',
            name='TS from ATM',
            line=dict(color=self.theme.accent, width=3),
            marker=dict(size=6)
        ))
        
        fig.add_trace(go.Scatter(
            x=pnl_df['shock_bp'],
            y=pnl_df['ts_neighbor_pnl'],
            mode='lines+markers',
            name='TS from Neighbor',
            line=dict(color=self.theme.success, width=3),
            marker=dict(size=6)
        ))
        
        # Update layout
        fig.update_layout(
            xaxis_title="Shift in bp",
            yaxis_title="PnL ($)",
            hovermode='x unified',
            plot_bgcolor=self.theme.panel_bg,
            paper_bgcolor=self.theme.panel_bg,
            font={'color': self.theme.text_light},
            legend=dict(
                bgcolor=self.theme.panel_bg,
                bordercolor=self.theme.secondary,
                borderwidth=1
            ),
            xaxis=dict(
                gridcolor=self.theme.secondary,
                zerolinecolor=self.theme.text_subtle
            ),
            yaxis=dict(
                gridcolor=self.theme.secondary,
                zerolinecolor=self.theme.text_subtle
            ),
            margin=dict(t=10, b=40),
            autosize=False,
            width=600,
            height=400
        )
        
        return Graph(
            id="pnl-graph",
            figure=fig,
            theme=self.theme,
            style={"height": "400px"}
        ).render()
    
    def create_pnl_table(self, greeks, option_type: str) -> html.Div:
        """Create both price and PnL comparison tables using real data."""
        # Calculate PnL data using real calculations
        pnl_df = PnLCalculator.calculate_all_pnls(greeks, option_type)
        
        # Create container for both tables side-by-side
        return html.Div(
            id="tables-container",
            children=[
                # Side-by-side container
                html.Div([
                    # Price comparison table (left)
                    html.Div([
                        html.H4(f"{option_type.title()} Price Comparison", style={
                            "color": self.theme.text_light,
                            "textAlign": "center",
                            "marginBottom": "10px",
                            "fontSize": "16px",
                            "fontWeight": "500"
                        }),
                        self._create_price_table(pnl_df)
                    ], style={
                        "width": "49%",
                        "display": "inline-block",
                        "verticalAlign": "top",
                        "paddingRight": "1%"
                    }),
                    
                    # PnL comparison table (right)
                    html.Div([
                        html.H4(f"{option_type.title()} PnL Comparison", style={
                            "color": self.theme.text_light,
                            "textAlign": "center",
                            "marginBottom": "10px",
                            "fontSize": "16px",
                            "fontWeight": "500"
                        }),
                        self._create_pnl_only_table(pnl_df)
                    ], style={
                        "width": "49%",
                        "display": "inline-block",
                        "verticalAlign": "top",
                        "paddingLeft": "1%"
                    })
                ], style={
                    "width": "100%",
                    "backgroundColor": self.theme.panel_bg,
                    "padding": "15px",
                    "borderRadius": "8px",
                    "marginBottom": "20px"
                })
            ]
        )
    
    def _create_price_table(self, pnl_df: pd.DataFrame):
        """Create price comparison table."""
        # Format data for display with shift in the middle
        table_data = []
        for _, row in pnl_df.iterrows():
            ts0_diff = row['ts0_price'] - row['actant_price']
            ts_neighbor_diff = row['ts_neighbor_price'] - row['actant_price']
            
            table_data.append({
                "Actant": f"${row['actant_price']:.2f}",
                "TS from ATM": f"${row['ts0_price']:.2f}",
                "TS from Neighbor": f"${row['ts_neighbor_price']:.2f}",
                "Shift (bp)": f"{row['shock_bp']:.0f}",
                "TS0 vs Actant": f"${ts0_diff:.2f}",
                "TS-0.25 vs Actant": f"${ts_neighbor_diff:.2f}",
                "_ts0_diff_raw": ts0_diff,  # Hidden column for conditional formatting
                "_ts_neighbor_diff_raw": ts_neighbor_diff  # Hidden column for conditional formatting
            })
        
        # Define columns - prices on left, shift in middle, differences on right
        columns = [
            {"name": "Actant", "id": "Actant", "type": "text"},
            {"name": "TS from ATM", "id": "TS from ATM", "type": "text"},
            {"name": "TS from Neighbor", "id": "TS from Neighbor", "type": "text"},
            {"name": "Shift (bp)", "id": "Shift (bp)", "type": "text"},
            {"name": "TS0 vs Actant", "id": "TS0 vs Actant", "type": "text"},
            {"name": "TS-0.25 vs Actant", "id": "TS-0.25 vs Actant", "type": "text"}
        ]
        
        # Build conditional styling
        style_data_conditional = [
            {
                'if': {'column_id': 'Shift (bp)'},
                'backgroundColor': self.theme.secondary,
                'color': self.theme.text_light,
                'fontWeight': 'bold'
            }
        ]
        
        # Add conditional formatting for difference columns
        for i, row in enumerate(table_data):
            if row['_ts0_diff_raw'] < 0:
                style_data_conditional.append({
                    'if': {'row_index': i, 'column_id': 'TS0 vs Actant'},
                    'color': '#ff4444'  # Red for negative
                })
            else:
                style_data_conditional.append({
                    'if': {'row_index': i, 'column_id': 'TS0 vs Actant'},
                    'color': '#44ff44'  # Green for positive
                })
                
            if row['_ts_neighbor_diff_raw'] < 0:
                style_data_conditional.append({
                    'if': {'row_index': i, 'column_id': 'TS-0.25 vs Actant'},
                    'color': '#ff4444'  # Red for negative
                })
            else:
                style_data_conditional.append({
                    'if': {'row_index': i, 'column_id': 'TS-0.25 vs Actant'},
                    'color': '#44ff44'  # Green for positive
                })
        
        return DataTable(
            id="price-table",
            data=table_data,
            columns=columns,
            theme=self.theme,
            page_size=25,
            style_table={"overflowX": "auto"},
            style_cell={
                'textAlign': 'center',
                'padding': '8px',
                'fontFamily': 'monospace'
            },
            style_data_conditional=style_data_conditional
        ).render()
    
    def _create_pnl_only_table(self, pnl_df: pd.DataFrame):
        """Create PnL comparison table."""
        # Format data for display with shift in the middle
        table_data = []
        for _, row in pnl_df.iterrows():
            table_data.append({
                "Actant PnL": f"${row['actant_pnl']:.2f}",
                "TS from ATM": f"${row['ts0_pnl']:.2f}",
                "TS from Neighbor": f"${row['ts_neighbor_pnl']:.2f}",
                "Shift (bp)": f"{row['shock_bp']:.0f}",
                "TS0 Error": f"${row['ts0_diff']:.2f}",
                "TS-0.25 Error": f"${row['ts_neighbor_diff']:.2f}",
                # Hidden columns for conditional formatting of error columns only
                "_ts0_diff_raw": row['ts0_diff'],
                "_ts_neighbor_diff_raw": row['ts_neighbor_diff']
            })
        
        # Define columns - PnL on left, shift in middle, errors on right
        columns = [
            {"name": "Actant PnL", "id": "Actant PnL", "type": "text"},
            {"name": "TS from ATM", "id": "TS from ATM", "type": "text"},
            {"name": "TS from Neighbor", "id": "TS from Neighbor", "type": "text"},
            {"name": "Shift (bp)", "id": "Shift (bp)", "type": "text"},
            {"name": "TS0 Error", "id": "TS0 Error", "type": "text"},
            {"name": "TS-0.25 Error", "id": "TS-0.25 Error", "type": "text"}
        ]
        
        # Build conditional styling
        style_data_conditional = [
            {
                'if': {'column_id': 'Shift (bp)'},
                'backgroundColor': self.theme.secondary,
                'color': self.theme.text_light,
                'fontWeight': 'bold'
            }
        ]
        
        # Add conditional formatting ONLY for error columns
        for i, row in enumerate(table_data):
            # TS0 Error
            if row['_ts0_diff_raw'] < 0:
                style_data_conditional.append({
                    'if': {'row_index': i, 'column_id': 'TS0 Error'},
                    'color': '#ff4444'  # Red for negative
                })
            else:
                style_data_conditional.append({
                    'if': {'row_index': i, 'column_id': 'TS0 Error'},
                    'color': '#44ff44'  # Green for positive
                })
            
            # TS-0.25 Error
            if row['_ts_neighbor_diff_raw'] < 0:
                style_data_conditional.append({
                    'if': {'row_index': i, 'column_id': 'TS-0.25 Error'},
                    'color': '#ff4444'  # Red for negative
                })
            else:
                style_data_conditional.append({
                    'if': {'row_index': i, 'column_id': 'TS-0.25 Error'},
                    'color': '#44ff44'  # Green for positive
                })
        
        return DataTable(
            id="pnl-table",
            data=table_data,
            columns=columns,
            theme=self.theme,
            page_size=25,
            style_table={"overflowX": "auto"},
            style_cell={
                'textAlign': 'center',
                'padding': '8px',
                'fontFamily': 'monospace'
            },
            style_data_conditional=style_data_conditional
        ).render()


def create_app(data_dir: str = None) -> dash.Dash:
    """Create and configure the Dash application."""
    # Find project root and assets folder
    project_root = Path(__file__).parent.parent.parent.parent  # Navigate up to project root
    assets_folder_path = str(project_root / "assets")
    
    # Create app with assets folder for CSS styling
    # Note: Using __name__ is crucial for assets to work properly with different runners
    app = dash.Dash(
        __name__,
        assets_folder=assets_folder_path,
        assets_url_path='/assets/'  # Explicitly set the URL path
    )
    
    # Log the assets folder path for debugging
    print(f"[INFO] Assets folder path: {assets_folder_path}")
    if os.path.exists(assets_folder_path):
        print(f"[INFO] Assets folder exists with files: {os.listdir(assets_folder_path)}")
    else:
        print(f"[WARNING] Assets folder not found at: {assets_folder_path}")
    
    # Create dashboard
    dashboard = PnLDashboard(data_dir)
    
    # Set layout
    app.layout = dashboard.create_layout()
    
    # Register callbacks
    dashboard.register_callbacks(app)
    
    return app


# Integration functions for main dashboard
# Create a shared instance for integration
_shared_dashboard_instance = None

def get_shared_dashboard():
    """Get or create the shared dashboard instance."""
    global _shared_dashboard_instance
    if _shared_dashboard_instance is None:
        # Use Z:\RiskCSVs as the data directory
        _shared_dashboard_instance = PnLDashboard(
            data_dir=r"Z:\RiskCSVs",
            id_prefix="actant-pnl-"
        )
    return _shared_dashboard_instance


def create_dashboard_content():
    """
    Create dashboard content for integration into main app.
    This returns the layout without creating a separate app.
    """
    dashboard = get_shared_dashboard()
    return dashboard.create_layout()


def register_callbacks(app):
    """
    Register callbacks with the main app instance.
    This allows the dashboard to work within the unified app.
    """
    dashboard = get_shared_dashboard()
    dashboard.register_callbacks(app)


# Standalone mode for testing
if __name__ == "__main__":
    # Get the script directory for standalone mode
    SCRIPT_DIR = Path(__file__).parent.resolve()
    
    # Use default data directory
    project_root = SCRIPT_DIR.parent.parent.parent  # Navigate up to project root
    data_dir = str(project_root / "data" / "input" / "actant_pnl")
    
    app = create_app(data_dir)
    print("Starting PnL Dashboard...")
    print(f"Looking for CSV files in: {data_dir}")
    print("Open http://localhost:8050 in your browser")
    app.run(debug=True, host="0.0.0.0", port=8050) 