from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional, cast


from dash import dash_table
from dash.development.base_component import Component

# Correct imports based on your project structure
from core.base_component import BaseComponent
from utils.colour_palette import Theme, default_theme


class DataTable(BaseComponent):
    """
    Dark-theme wrapper around `dash_table.DataTable`.

    Applies styling based on the provided theme object.
    """

    def __init__(
        self,
        *,
        data: Optional[List[Dict[str, Any]]] = None,
        columns: Optional[List[Dict[str, Any]]] = None,
        id: Optional[str] = None,
        theme: Theme = default_theme, # Accept theme object
        page_size: int = 15,
        sort_action: str = "native", # Enable sorting by default
        filter_action: str = "native", # Enable filtering by default
        page_action: str = "native", # Enable pagination by default
        style_as_list_view: bool = True, # Use list view style by default
        **dt_kwargs: Any, # Capture other DataTable arguments
    ) -> None:
        """
        Initializes the DataTable wrapper.

        Args:
            data: Data for the table (list of dicts). Defaults to an empty list.
            columns: Column definitions (list of dicts with 'name' and 'id'). Defaults to an empty list.
            id: Component ID. Auto-generated if None.
            theme: Colour theme object. Defaults to uikitxv2.utils.default_theme.
            page_size: Number of rows per page for pagination. Defaults to 15.
            sort_action: Enables sorting ('native', 'custom', 'none'). Defaults to 'native'.
            filter_action: Enables filtering ('native', 'custom', 'none'). Defaults to 'native'.
            page_action: Enables pagination ('native', 'custom', 'none'). Defaults to 'native'.
            style_as_list_view: Removes vertical grid lines. Defaults to True.
            **dt_kwargs: Additional keyword arguments passed directly to dash_table.DataTable.
                         These will override theme defaults if they conflict (e.g., providing custom style_cell).
        """
        self.data = data if data is not None else []
        self.columns = columns if columns is not None else []
        self.id = id or f"datatable-{uuid.uuid4().hex[:8]}"
        self.theme = theme # Store the theme object
        # Store other defaults
        self.page_size = page_size
        self.sort_action = sort_action
        self.filter_action = filter_action
        self.page_action = page_action
        self.style_as_list_view = style_as_list_view
        # Store user-provided keyword arguments
        self.kwargs = dt_kwargs

    def _get_theme_styling(self) -> Dict[str, Any]:
        """Generates style dictionary based on the self.theme object."""
        # Define base styles using the theme
        styling_args = {
            "style_table": {
                "overflowX": "auto",
                "width": "100%",
                "minWidth": "100%",
            },
            "style_header": {
                "backgroundColor": self.theme.panel_bg, # Use theme
                "color": self.theme.primary,          # Use theme
                "fontWeight": "bold",
                "border": f"1px solid {self.theme.secondary}", # Use theme
                "textAlign": "left",
            },
            "style_cell": { # Default for all cells
                "backgroundColor": self.theme.panel_bg, # Use theme
                "color": self.theme.text_light,       # Use theme
                "border": f"1px solid {self.theme.secondary}", # Use theme
                "padding": "8px",
                "textAlign": "left",
                "whiteSpace": "normal",
                "height": "auto",
                "minWidth": "100px",
                "width": "auto",
                "maxWidth": "300px",
                "overflow": "hidden",
                "textOverflow": "ellipsis",
            },
            "style_data": { # Styles specific to data cells (can override style_cell)
                 # Inherits most from style_cell, add specifics if needed
                 # e.g., 'border': f"1px solid {self.theme.accent}"
            },
             "style_data_conditional": [ # Example: Striped rows using theme colors
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': self.theme.base_bg, # Use theme for alternating rows
                }
            ],
            "style_filter": { # Input fields for filtering
                 "backgroundColor": self.theme.base_bg, # Use theme
                 "color": self.theme.text_light,       # Use theme
                 "border": f"1px solid {self.theme.secondary}", # Use theme
            },
             # Include other defaults passed in __init__
             "page_action": self.page_action,
             "page_size": self.page_size,
             "sort_action": self.sort_action,
             "filter_action": self.filter_action,
             "style_as_list_view": self.style_as_list_view,
        }
        return styling_args

    def render(self) -> Component:
        """Renders the dash_table.DataTable component with theme styles."""
        theme_styling = self._get_theme_styling()

        # Combine theme styles and user kwargs. User kwargs take precedence.
        merged_kwargs = {**theme_styling, **self.kwargs}

        # Ensure required args 'columns' and 'data' are present, using instance attributes if not in kwargs
        if "columns" not in merged_kwargs:
            merged_kwargs["columns"] = self.columns
        if "data" not in merged_kwargs:
            merged_kwargs["data"] = self.data

        # Create the DataTable instance
        dt = dash_table.DataTable(
            id=self.id,
            **merged_kwargs, # Pass the merged arguments
        )
        return cast(Component, dt)

