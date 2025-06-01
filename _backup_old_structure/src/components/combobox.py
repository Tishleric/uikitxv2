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
    def __init__(
        self,
        id,
        options=None,
        value=None,
        placeholder=None,
        theme=None,
        style=None,
        clearable=True,
        searchable=True,
        multi=False,
        className="",
    ):
        """Instantiate a ComboBox component.

        Args:
            id: The unique component identifier.
            options: List of option dicts or strings to populate the dropdown.
            value: Currently selected value(s).
            placeholder: Placeholder text when no value is selected.
            theme: Optional theme configuration for styling.
            style: Custom CSS style overrides.
            clearable: Whether the selection can be cleared by the user.
            searchable: Whether the dropdown includes a search box.
            multi: Enable multi-select mode if ``True``.
            className: Additional CSS class names for the wrapper.
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
        """Render the ComboBox as a Dash ``dcc.Dropdown`` component.

        Returns:
            dcc.Dropdown: The Dash dropdown element with merged theme styles.
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
