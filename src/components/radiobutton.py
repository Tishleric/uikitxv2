# uikitxv2/src/components/radiobutton.py

from dash import dcc
import dash_bootstrap_components as dbc

# Corrected relative import: Go up one level (..) to src, then down to core
from ..core.base_component import BaseComponent
# Corrected relative import: Go up one level (..) to src, then down to utils
from ..utils.colour_palette import default_theme # Only default_theme seems used here

class RadioButton(BaseComponent):
    """
    A wrapper for dcc.RadioItems with theme integration.
    """
    def __init__(self, id, options=None, value=None, theme=None, style=None, inline=False, labelStyle=None, inputStyle=None, className=""):
        """
        Initialize a RadioButton component.
        
        Args:
            id (str): The component's ID, required for Dash callbacks.
            options (list, optional): List of options to display. Defaults to None.
            value (Any, optional): Currently selected value. Defaults to None.
            theme (Any, optional): Theme object for styling. Defaults to None.
            style (dict, optional): Additional CSS styles for the container. Defaults to None.
            inline (bool, optional): Whether to display options horizontally. Defaults to False.
            labelStyle (dict, optional): Styles to apply to option labels. Defaults to None.
            inputStyle (dict, optional): Styles to apply to radio inputs. Defaults to None.
            className (str, optional): Additional CSS classes. Defaults to "".
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
        """
        Render the RadioButton component.
        
        Returns:
            dcc.RadioItems: A Dash Core Component radio group with applied styling.
        """
        # Define default styles based on theme
        default_label_style = {'color': self.theme.text_light, 'paddingRight': '10px', 'display': 'inline-block', **self.labelStyle}
        default_input_style = {'marginRight': '5px', **self.inputStyle} # Style for the radio input itself
        default_container_style = {**self.style} # Style for the overall div

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

