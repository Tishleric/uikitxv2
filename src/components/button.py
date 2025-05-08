# uikitxv2/src/components/button.py

import dash_bootstrap_components as dbc
from dash import html

# Corrected relative import: Go up one level (..) to src, then down to core
from ..core.base_component import BaseComponent
# Corrected relative import: Go up one level (..) to src, then down to utils
from ..utils.colour_palette import default_theme, get_button_default_style

class Button(BaseComponent):
    """
    A wrapper for dbc.Button that integrates with the theme system.
    """
    def __init__(self, id, label="Button", theme=None, style=None, n_clicks=0, className=""):
        super().__init__(id, theme)
        self.label = label
        self.style = style if style is not None else {}
        self.n_clicks = n_clicks
        self.className = className

    def render(self):
        # Get default styles based on the theme
        default_style = get_button_default_style(self.theme)

        # Merge default styles with instance-specific styles
        final_style = {**default_style, **self.style}

        return dbc.Button(
            self.label,
            id=self.id,
            n_clicks=self.n_clicks,
            style=final_style,
            className=self.className
        )

