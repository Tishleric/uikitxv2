# uikitxv2/src/components/tabs.py

import dash_bootstrap_components as dbc
from dash import html
from dash.development.base_component import Component as DashBaseComponent

# Corrected relative import: Go up one level (..) to src, then down to core
from ..core.base_component import BaseComponent
# Corrected relative import: Go up one level (..) to src, then down to utils
from ..utils.colour_palette import default_theme

class Tabs(BaseComponent):
    """
    A wrapper for dbc.Tabs and dbc.Tab with theme integration.
    Expects 'tabs' prop to be a list of tuples: [('Tab Label 1', content1), ('Tab Label 2', content2)]
    Content can be a BaseComponent instance or any Dash-compatible component layout.
    """
    def __init__(self, id, tabs=None, active_tab=None, theme=None, style=None, className=""):
        super().__init__(id, theme)
        self.tabs_data = tabs if tabs is not None else []
        self.active_tab = active_tab
        self.style = style if style is not None else {}
        self.className = className

    def _create_tabs(self):
        """Creates dbc.Tab components from the tabs_data."""
        dbc_tabs = []
        for i, (label, content) in enumerate(self.tabs_data):
            tab_id = f"{self.id}-tab-{i}"

            rendered_content = None
            # Check if content is one of our custom components or needs rendering
            if isinstance(content, BaseComponent) or \
               (hasattr(content, 'render') and callable(content.render) and \
               not isinstance(content, (DashBaseComponent, dict, str))):
                 rendered_content = content.render()
            else:
                 # Assume content is already a Dash component layout (dict, Dash component, string, etc.)
                 rendered_content = content

            # Define styles based on theme - using existing attributes from default_theme
            tab_style = {
                "backgroundColor": self.theme.panel_bg,
                "padding": "0.5rem 1rem",
                "border": f"1px solid {self.theme.secondary}", # Fixed: Use secondary
                "borderBottom": "none",
                "marginRight": "2px",
                "borderRadius": "4px 4px 0 0",
            }
            active_tab_style = {
                "backgroundColor": self.theme.panel_bg,
                "padding": "0.5rem 1rem",
                "border": f"1px solid {self.theme.primary}", # Use primary for active border
                "borderBottom": f"1px solid {self.theme.panel_bg}", # Make bottom border blend with panel
                "marginRight": "2px",
                "borderRadius": "4px 4px 0 0",
                "position": "relative",
                "zIndex": "1", # Ensure active tab is visually on top
            }
            label_style = {"color": self.theme.text_subtle, "textDecoration": "none"} # Style for inactive label text
            active_label_style = {"color": self.theme.primary, "fontWeight": "bold", "textDecoration": "none"} # Style for active label text

            dbc_tabs.append(
                dbc.Tab(
                    children=rendered_content,
                    label=label,
                    tab_id=tab_id,
                    # Apply themed styles using dbc.Tab specific props
                    tab_style=tab_style,
                    active_tab_style=active_tab_style,
                    label_style=label_style,
                    active_label_style=active_label_style
                )
            )
        return dbc_tabs

    def render(self):
        # Determine the default active tab if not specified
        active_tab_id = self.active_tab
        if active_tab_id is None and self.tabs_data:
            active_tab_id = f"{self.id}-tab-0" # Default to the first tab

        # Apply theme styles to the main Tabs container if desired
        # final_style = {'borderBottom': f'2px solid {self.theme.primary}', **self.style}

        return dbc.Tabs(
            id=self.id,
            children=self._create_tabs(),
            active_tab=active_tab_id,
            style=self.style, # Use self.style directly for the outer container
            className=f"custom-tabs {self.className}" # Add class for potential CSS targeting
        )

