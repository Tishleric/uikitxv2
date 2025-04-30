# src/components/tabs.py

from __future__ import annotations

import uuid
from typing import Any, List, Sequence, Tuple, cast
import logging
from dash import html # Import html for error handling if needed

import dash_bootstrap_components as dbc
from dash.development.base_component import Component

# Assuming these imports are correct based on your structure
from core.base_component import BaseComponent
from utils.colour_palette import Theme, default_theme


class Tabs(BaseComponent):
    """Dark-theme wrapper around `dbc.Tabs` and `dbc.Tab`."""

    def __init__(
        self,
        tabs: Sequence[Tuple[str, BaseComponent]],  # (label, wrapped component)
        *,
        active_tab_index: int = 0,
        id: str | None = None,
        theme: Theme = default_theme,
        **dbc_kwargs: Any, # Keep kwargs
    ) -> None:
        """
        Initializes the Tabs wrapper.

        Args:
            tabs: Sequence of (label, uikitxv2_component) tuples.
            active_tab_index: Index of the initially active tab. Defaults to 0.
            id: Component ID. Auto-generated if None.
            theme: Colour theme object. Defaults to uikitxv2.utils.default_theme.
            **dbc_kwargs: Additional keyword arguments passed to the underlying dbc.Tabs.
        """
        if not tabs:
            raise ValueError("Tabs wrapper requires at least one tab.")
        if not (0 <= active_tab_index < len(tabs)):
            raise IndexError("active_tab_index out of range.")

        self.tabs = list(tabs)
        self.active_tab_index = active_tab_index
        self.id = id or f"tabs-{uuid.uuid4().hex[:8]}"
        self.theme = theme
        self.kwargs = dbc_kwargs # Store kwargs

    # --------------------------------------------------------------------- #
    # Helpers
    # --------------------------------------------------------------------- #
    def _build_tab_children(self) -> List[dbc.Tab]:
        """Builds the list of dbc.Tab components for the dbc.Tabs."""
        children: list[dbc.Tab] = []
        for idx, (label, wrapped_component) in enumerate(self.tabs):
            tab_id = f"{self.id}-tab-{idx}"
            # Ensure the wrapped component has a render method
            try:
                rendered_content = wrapped_component.render()
            except AttributeError:
                logging.error(f"Component for tab '{label}' does not have a .render() method.")
                rendered_content = html.Div(f"Error: Content for tab '{label}' cannot be rendered.")

            children.append(
                dbc.Tab(
                    rendered_content,          # children (positional)
                    label=label,               # tab label text
                    id=tab_id,                 # unique id for the tab itself
                    tab_id=tab_id,             # id used for switching active tab

                    # Style for the inactive tab *container* (<li>)
                    tab_style={
                        "backgroundColor": self.theme.panel_bg,
                        # "color" removed - use label_style
                        "padding": "0.5rem 1rem", # Basic padding
                        "border": f"1px solid {self.theme.secondary}",
                        "borderBottom": "none",
                        "marginRight": "2px", # Add small space between tabs
                    },
                    # Style for the active tab *container* (<li>)
                    active_tab_style={
                        "backgroundColor": self.theme.panel_bg,
                        # "color" removed - use active_label_style
                        "fontWeight": "bold",
                        "padding": "0.5rem 1rem",
                        "border": f"1px solid {self.theme.primary}",
                        "borderBottom": "none",
                        "marginRight": "2px",
                    },
                    # --- Style specifically for the inactive tab *label* (<a>) ---
                    label_style={
                        "color": self.theme.text_light, # Use light text for inactive label
                    },
                    # --- Style specifically for the active tab *label* (<a>) ---
                    active_label_style={
                        "color": self.theme.primary, # Use primary theme color for active label
                    }
                )
            )
        return children

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    def render(self) -> Component:
        """Renders the underlying dbc.Tabs component."""
        child_tabs = self._build_tab_children()
        # Determine the correct active tab identifier (use tab_id)
        active_tab_identifier = child_tabs[self.active_tab_index].tab_id if child_tabs else None

        # Instantiate the dbc.Tabs component
        tabs_component = dbc.Tabs(
            child_tabs, # Pass the generated list of dbc.Tab components
            id=self.id, # Assign the main ID to the Tabs container
            active_tab=active_tab_identifier, # Set the initially active tab using tab_id
            className="card-header-tabs", # Use Bootstrap class for potential styling integration
            **self.kwargs, # Pass any remaining kwargs
            # Add a border below the tab row for visual separation
            style={
                 "borderBottom": f"1px solid {self.theme.primary}",
                 "marginBottom": "1rem", # Add space below tabs
            }
        )
        # Cast to generic Component type for compatibility
        return cast(Component, tabs_component)
