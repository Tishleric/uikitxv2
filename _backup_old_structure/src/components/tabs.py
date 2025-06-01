# uikitxv2/src/components/tabs.py

import dash_bootstrap_components as dbc
from dash import html
from dash.development.base_component import Component as DashBaseComponent

# Corrected relative import: Go up one level (..) to src, then down to core
from ..core.base_component import BaseComponent
# Corrected relative import: Go up one level (..) to src, then down to utils
from ..utils.colour_palette import default_theme, get_tabs_default_styles

class Tabs(BaseComponent):
    """
    A wrapper for dbc.Tabs and dbc.Tab with theme integration.
    Expects 'tabs' prop to be a list of tuples: [('Tab Label 1', content1), ('Tab Label 2', content2)]
    Content can be a BaseComponent instance or any Dash-compatible component layout.
    """
    def __init__(
        self,
        id,
        tabs=None,
        active_tab=None,
        theme=None,
        style=None,
        className="",
    ):
        """Instantiate a Tabs component.

        Args:
            id: The unique component identifier.
            tabs: List of ``(label, content)`` tuples defining each tab.
            active_tab: Identifier of the tab that should be active initially.
            theme: Optional theme configuration for styling.
            style: CSS style overrides for the tabs container.
            className: Additional CSS class names for the wrapper.
        """
        super().__init__(id, theme)
        self.tabs_data = tabs if tabs is not None else []
        self.active_tab = active_tab
        self.style = style if style is not None else {}
        self.className = className

    def _create_tabs(self):
        """Creates dbc.Tab components from the tabs_data."""
        dbc_tabs = []
        
        # Get default styles from the centralized styling utility
        default_styles = get_tabs_default_styles(self.theme)
        
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

            dbc_tabs.append(
                dbc.Tab(
                    children=rendered_content,
                    label=label,
                    tab_id=tab_id,
                    # Apply themed styles using the default styles from utility
                    tab_style=default_styles["tab_style"],
                    active_tab_style=default_styles["active_tab_style"],
                    label_style=default_styles["label_style"],
                    active_label_style=default_styles["active_label_style"]
                )
            )
        return dbc_tabs

    def render(self):
        """Render the tabs and their content as a ``dbc.Tabs`` component.

        Returns:
            dbc.Tabs: The Dash Bootstrap tabs component with its child tabs.
        """
        # Determine the default active tab if not specified
        active_tab_id = self.active_tab
        if active_tab_id is None and self.tabs_data:
            active_tab_id = f"{self.id}-tab-0" # Default to the first tab

        # Get default styles for the main tabs container
        default_styles = get_tabs_default_styles(self.theme)
        
        # Merge default main tabs style with custom style
        final_style = {**default_styles["main_tabs_style"], **self.style}

        return dbc.Tabs(
            id=self.id,
            children=self._create_tabs(),
            active_tab=active_tab_id,
            style=final_style, # Use merged styles
            className=f"custom-tabs {self.className}" # Add class for potential CSS targeting
        )

