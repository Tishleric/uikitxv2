# uikitxv2/src/components/graph.py

from dash import dcc
import plotly.graph_objects as go

# Corrected relative import: Go up one level (..) to src, then down to core
from ..core.base_component import BaseComponent
# Corrected relative import: Go up one level (..) to src, then down to utils
from ..utils.colour_palette import default_theme, get_graph_figure_layout_defaults, get_graph_wrapper_default_style

class Graph(BaseComponent):
    """
    A wrapper for dcc.Graph with theme integration for layout.
    """
    def __init__(
        self,
        id,
        figure=None,
        theme=None,
        style=None,
        config=None,
        className="",
    ):
        """Instantiate a Graph component with optional theming.

        Args:
            id: The unique component identifier.
            figure: A Plotly figure object to display.
            theme: Optional theme configuration for styling.
            style: CSS style overrides for the wrapper.
            config: Additional Plotly configuration options.
            className: Additional CSS class names for the wrapper.
        """
        super().__init__(id, theme)
        self.figure = figure if figure is not None else go.Figure()
        self.style = style if style is not None else {'height': '400px'} # Default height
        self.config = config if config is not None else {'displayModeBar': False} # Example config
        self.className = className

        # Apply theme defaults to the figure layout
        self._apply_theme_to_figure()

    def _apply_theme_to_figure(self):
        """Applies theme colors to the figure layout."""
        if self.figure and hasattr(self.figure, 'update_layout'):
            # Get default layout settings from the centralized styling function
            default_layout = get_graph_figure_layout_defaults(self.theme)
            self.figure.update_layout(**default_layout)

    def render(self):
        """Render the graph as a Dash ``dcc.Graph`` component.

        Returns:
            dcc.Graph: The graph component with themed layout and styles.
        """
        # Ensure theme is applied before rendering
        self._apply_theme_to_figure()

        # Get default wrapper style and merge with instance style
        default_wrapper_style = get_graph_wrapper_default_style(self.theme)
        final_style = {**{'height': '400px'}, **default_wrapper_style, **self.style}

        return dcc.Graph(
            id=self.id,
            figure=self.figure,
            style=final_style,
            config=self.config,
            className=self.className
        )

