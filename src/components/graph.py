# uikitxv2/src/components/graph.py

from dash import dcc
import plotly.graph_objects as go

# Corrected relative import: Go up one level (..) to src, then down to core
from ..core.base_component import BaseComponent
# Corrected relative import: Go up one level (..) to src, then down to utils
from ..utils.colour_palette import default_theme

class Graph(BaseComponent):
    """
    A wrapper for dcc.Graph with theme integration for layout.
    """
    def __init__(self, id, figure=None, theme=None, style=None, config=None, className=""):
        """
        Initialize a Graph component.

        Args:
            id (str): The component's ID, required for Dash callbacks.
            figure (plotly.graph_objects.Figure, optional): Plotly figure object. Defaults to None.
            theme (Any, optional): Theme object for styling. Defaults to None.
            style (dict, optional): Additional CSS styles to apply. Defaults to None.
            config (dict, optional): Plotly configuration options. Defaults to None.
            className (str, optional): Additional CSS classes. Defaults to "".
        """
        super().__init__(id, theme)
        self.figure = figure if figure is not None else go.Figure()
        self.style = style if style is not None else {'height': '400px'} # Default height
        self.config = config if config is not None else {'displayModeBar': False} # Example config
        self.className = className

        # Apply theme defaults to the figure layout
        self._apply_theme_to_figure()

    def _apply_theme_to_figure(self):
        """
        Applies theme colors to the figure layout.
        
        This method applies the current theme's colors to various elements of the plotly figure,
        including background colors, grid lines, and text.
        """
        if self.figure and hasattr(self.figure, 'update_layout'):
            self.figure.update_layout(
                plot_bgcolor=self.theme.base_bg,
                paper_bgcolor=self.theme.panel_bg,
                font_color=self.theme.text_light,
                xaxis=dict(
                    gridcolor=self.theme.secondary, # Fixed: Use secondary
                    linecolor=self.theme.secondary, # Fixed: Use secondary
                    zerolinecolor=self.theme.secondary # Fixed: Use secondary
                ),
                yaxis=dict(
                    gridcolor=self.theme.secondary, # Fixed: Use secondary
                    linecolor=self.theme.secondary, # Fixed: Use secondary
                    zerolinecolor=self.theme.secondary # Fixed: Use secondary
                ),
                 legend=dict(
                    bgcolor=self.theme.panel_bg,
                    bordercolor=self.theme.secondary # Fixed: Use secondary
                )
            )

    def render(self):
        """
        Render the Graph component.

        Returns:
            dcc.Graph: A Dash Core Component graph with applied theming.
        """
        # Ensure theme is applied before rendering
        self._apply_theme_to_figure()

        return dcc.Graph(
            id=self.id,
            figure=self.figure,
            style=self.style,
            config=self.config,
            className=self.className
        )

