# uikitxv2/src/components/radiobutton.py

from dash import dcc
import dash_bootstrap_components as dbc

# Corrected relative import: Go up one level (..) to src, then down to core
from ..core import BaseComponent
# Corrected relative import: Go up one level (..) to src, then down to utils
from ..themes import default_theme, get_radiobutton_default_styles

class RadioButton(BaseComponent):
    """
    A wrapper for dcc.RadioItems with theme integration.
    """
    def __init__(
        self,
        id,
        options=None,
        value=None,
        theme=None,
        style=None,
        inline=False,
        labelStyle=None,
        inputStyle=None,
        className="",
    ):
        """Instantiate a RadioButton component.

        Args:
            id: The unique component identifier.
            options: List of options as dicts or strings.
            value: Currently selected value.
            theme: Optional theme configuration for styling.
            style: CSS styles for the outer container.
            inline: Display radio items inline when ``True``.
            labelStyle: Style overrides for the label elements.
            inputStyle: Style overrides for the input elements.
            className: Additional CSS classes for the wrapper.
        """
        super().__init__(id, theme)
        self.options = options if options is not None else []
        self.value = value
        self.style = style if style is not None else {} # Style for the outer container
        self.inline = inline
        self.labelStyle = labelStyle if labelStyle is not None else {}
        self.inputStyle = inputStyle if inputStyle is not None else {}
        self.className = className
        # Ensure options are in the correct format {'label': ..., 'value': ...}
        if self.options and isinstance(self.options[0], str):
             self.options = [{'label': opt, 'value': opt} for opt in self.options]

    def render(self):
        """Render the radio buttons as a Dash ``dcc.RadioItems`` component.

        Returns:
            dcc.RadioItems: The configured set of radio buttons.
        """
        # Get default styles from the centralized styling function
        default_styles = get_radiobutton_default_styles(self.theme)
        
        # Merge default styles with instance-specific styles
        default_container_style = {**default_styles.get('style', {}), **self.style}
        default_label_style = {**default_styles.get('labelStyle', {}), **self.labelStyle}
        default_input_style = {**default_styles.get('inputStyle', {}), **self.inputStyle}

        return dcc.RadioItems(
            id=self.id,
            options=self.options,
            value=self.value,
            style=default_container_style,
            inputStyle=default_input_style,
            labelStyle=default_label_style,
            inline=self.inline,
            className=self.className
            # persistence=True, persistence_type='local' # Optional persistence
        )

