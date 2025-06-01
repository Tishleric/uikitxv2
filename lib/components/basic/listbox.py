# uikitxv2/src/components/listbox.py

from dash import dcc

# Corrected relative import: Go up one level (..) to src, then down to core
from ..core import BaseComponent
# Corrected relative import: Go up one level (..) to src, then down to utils
# Import the correct style function for ListBox
from ..themes import default_theme, get_listbox_default_styles

class ListBox(BaseComponent):
    """
    A wrapper for dcc.Dropdown styled as a ListBox (multi-select often implied).
    """
    def __init__(
        self,
        id,
        options=None,
        value=None,
        theme=None,
        style=None,
        multi=True,
        className="",
    ):
        """Instantiate a ListBox component.

        Args:
            id: The unique component identifier.
            options: List of option dicts or strings.
            value: The selected value list for multi-select.
            theme: Optional theme configuration for styling.
            style: Custom CSS style overrides.
            multi: Allow multiple selections if ``True``.
            className: Additional CSS classes for the wrapper.
        """
        super().__init__(id, theme)
        self.options = options if options is not None else []
        self.value = value if value is not None else [] # Default to empty list for multi
        self.style = style if style is not None else {}
        self.multi = multi
        self.className = className
        # Ensure options are in the correct format {'label': ..., 'value': ...}
        if self.options and isinstance(self.options[0], str):
             self.options = [{'label': opt, 'value': opt} for opt in self.options]

    def render(self):
        """Render the ListBox as a Dash ``dcc.Dropdown`` component.

        Returns:
            dcc.Dropdown: The configured dropdown with list box styling.
        """
        # Get default styles using the correct function from colour_palette
        # This function returns a dict containing potentially 'style', 'inputStyle', 'labelStyle'
        default_styles_dict = get_listbox_default_styles(self.theme)

        # Merge instance-specific style with the default 'style' from the dict
        final_outer_style = {**default_styles_dict.get('style', {}), **self.style}

        # Use other styles if provided by the function (e.g., inputStyle, labelStyle)
        # Note: dcc.Dropdown doesn't directly use inputStyle/labelStyle like dcc.Checklist might.
        # We apply the main 'style' to the dcc.Dropdown container.
        # If specific styling for options is needed, CSS might be required.

        return dcc.Dropdown(
            id=self.id,
            options=self.options,
            value=self.value,
            multi=self.multi,
            clearable=False,
            searchable=False,
            style=final_outer_style, # Apply merged style to the outer container
            className=f"custom-listbox {self.className}"
        )

