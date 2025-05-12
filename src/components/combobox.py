# uikitxv2/src/components/combobox.py

from dash import dcc
import uuid

# Corrected relative import: Go up one level (..) to src, then down to core
from ..core.base_component import BaseComponent
# Corrected relative import: Go up one level (..) to src, then down to utils
# Import the correct style function for ComboBox
from ..utils.colour_palette import default_theme, get_combobox_default_style

class ComboBox(BaseComponent):
    """
    A wrapper for dcc.Dropdown styled as a ComboBox, integrated with the theme system.
    """
    def __init__(self, id, options=None, value=None, placeholder=None, theme=None, style=None, clearable=True, searchable=True, multi=False, className=""):
        """
        Initialize a ComboBox component.

        Args:
            id (str): The component's ID, required for Dash callbacks.
            options (list, optional): List of options to display. Defaults to None.
            value (Any, optional): Currently selected value. Defaults to None.
            placeholder (str, optional): Placeholder text. Defaults to None.
            theme (Any, optional): Theme object for styling. Defaults to None.
            style (dict, optional): Additional CSS styles to apply. Defaults to None.
            clearable (bool, optional): Whether values can be cleared. Defaults to True.
            searchable (bool, optional): Whether options can be searched. Defaults to True.
            multi (bool, optional): Whether multiple selections are allowed. Defaults to False.
            className (str, optional): Additional CSS classes. Defaults to "".
        """
        super().__init__(id, theme)
        self.options = options if options is not None else []
        self.value = value
        self.placeholder = placeholder
        self.style = style if style is not None else {}
        self.clearable = clearable
        self.searchable = searchable
        self.multi = multi
        self.className = className
        # Ensure options are in the correct format {'label': ..., 'value': ...}
        if self.options and isinstance(self.options[0], str):
             self.options = [{'label': opt, 'value': opt} for opt in self.options]


    def render(self):
        """
        Render the ComboBox component.

        Returns:
            dcc.Dropdown: A Dash Core Component dropdown with applied styling.
        """
        # Get default styles using the correct function from colour_palette
        default_style = get_combobox_default_style(self.theme)

        # Merge default styles with instance-specific styles
        # Note: The style returned by get_combobox_default_style might apply
        # directly to the dcc.Dropdown's style prop or might need adjustment
        # depending on how dcc.Dropdown applies styles vs its container.
        # Assuming it applies to the container for now.
        final_style = {**default_style, **self.style}

        return dcc.Dropdown(
            id=self.id,
            options=self.options,
            value=self.value,
            placeholder=self.placeholder,
            clearable=self.clearable,
            searchable=self.searchable,
            multi=self.multi,
            style=final_style, # Apply merged style to the outer div
            className=f"custom-combobox {self.className}"
        )
