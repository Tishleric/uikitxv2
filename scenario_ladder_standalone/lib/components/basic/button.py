# uikitxv2/src/components/button.py

import dash_bootstrap_components as dbc
from dash import html

# Import from parent directories in the new structure
from ..core import BaseComponent
from ..themes import default_theme, get_button_default_style

class Button(BaseComponent):
    """
    A wrapper for dbc.Button that integrates with the theme system.
    
    This component creates a styled button using Dash Bootstrap Components,
    with automatic theming support.
    """
    def __init__(self, id, label="Button", theme=None, style=None, n_clicks=0, className=""):
        """
        Initialize a Button component.
        
        Args:
            id (str): The component's unique identifier.
            label (str, optional): Text to display on the button. Defaults to "Button".
            theme (dict, optional): Theme configuration. Defaults to None.
            style (dict, optional): Additional CSS styles to apply. Defaults to None.
            n_clicks (int, optional): Initial click count. Defaults to 0.
            className (str, optional): Additional CSS class names. Defaults to "".
        """
        super().__init__(id, theme)
        self.label = label
        self.style = style if style is not None else {}
        self.n_clicks = n_clicks
        self.className = className

    def render(self):
        """
        Render the button component.
        
        Returns:
            dash_bootstrap_components.Button: The rendered Dash Bootstrap button component.
        """
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

