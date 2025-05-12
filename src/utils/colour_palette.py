# src/utils/colour_palette.py

from __future__ import annotations
from typing import Any, List, Dict
from dataclasses import dataclass

__all__ = [
    "Theme",
    "default_theme",
    "get_combobox_default_style",
    "get_button_default_style",
    "get_container_default_style",
    "get_datatable_default_styles",
    "get_graph_figure_layout_defaults",
    "get_graph_wrapper_default_style",
    "get_grid_default_style",
    "get_listbox_default_styles",
    "get_radiobutton_default_styles",
    "get_tabs_default_styles",
]


@dataclass(frozen=True, slots=True)
class Theme:
    """
    Defines the color palette and theme values for UI components.
    
    Attributes:
        base_bg (str): Base background color
        panel_bg (str): Panel/secondary background color
        primary (str): Primary accent color
        secondary (str): Secondary color for borders and subtle elements
        accent (str): Highlight accent color
        text_light (str): Main text color
        text_subtle (str): Subdued text color
        danger (str): Color for error/danger states
        success (str): Color for success states
    """
    base_bg: str
    panel_bg: str
    primary: str
    secondary: str
    accent: str
    text_light: str
    text_subtle: str
    danger: str
    success: str


# "Black Cat Dark" palette
default_theme = Theme(
    base_bg="#000000",
    panel_bg="#121212",
    primary="#18F0C3",
    secondary="#8F8F8F",
    accent="#F01899",
    text_light="#E5E5E5",
    text_subtle="#9A9A9A",
    danger="#FF5555",
    success="#4CE675",
)

def get_combobox_default_style(theme: Theme) -> dict[str, Any]:
    """
    Get default styles for ComboBox components.
    
    Args:
        theme (Theme): Theme object to use for styling
        
    Returns:
        dict: Dictionary of CSS styles
    """
    return {"backgroundColor": theme.panel_bg, "color": theme.text_light, "borderRadius": "4px"}

def get_button_default_style(theme: Theme) -> dict[str, Any]:
    """
    Get default styles for Button components.
    
    Args:
        theme (Theme): Theme object to use for styling
        
    Returns:
        dict: Dictionary of CSS styles
    """
    return {"backgroundColor": theme.primary, "borderColor": theme.primary, "color": theme.text_light, "borderRadius": "4px", "fontFamily": "Inter, sans-serif", "fontSize": "15px", "padding": "0.375rem 0.75rem", "borderWidth": "1px", "borderStyle": "solid", "textDecoration": "none", "display": "inline-block", "fontWeight": "400", "lineHeight": "1.5", "textAlign": "center", "verticalAlign": "middle", "cursor": "pointer", "userSelect": "none"}

def get_container_default_style(theme: Theme) -> dict[str, Any]:
    """
    Get default styles for Container components.
    
    Args:
        theme (Theme): Theme object to use for styling
        
    Returns:
        dict: Dictionary of CSS styles
    """
    return {}

def get_datatable_default_styles(theme: Theme) -> Dict[str, Any]:
    """
    Get default styles for DataTable components.
    
    Args:
        theme (Theme): Theme object to use for styling
        
    Returns:
        dict: Dictionary of CSS styles for different DataTable elements
    """
    return {
        "style_table": {"overflowX": "auto", "width": "100%", "minWidth": "100%"},
        "style_header": {"backgroundColor": theme.panel_bg, "color": theme.primary, "fontWeight": "bold", "border": f"1px solid {theme.secondary}", "textAlign": "left", "padding": "10px"},
        "style_cell": {"backgroundColor": theme.panel_bg, "color": theme.text_light, "border": f"1px solid {theme.secondary}", "padding": "8px", "textAlign": "left", "whiteSpace": "normal", "height": "auto", "minWidth": "100px", "width": "auto", "maxWidth": "300px", "overflow": "hidden", "textOverflow": "ellipsis", "fontFamily": "Inter, sans-serif"},
        "style_data": {},
        "style_data_conditional": [{'if': {'row_index': 'odd'}, 'backgroundColor': theme.base_bg}],
        "style_filter": {"backgroundColor": theme.base_bg, "color": theme.text_light, "border": f"1px solid {theme.secondary}", "padding": "5px"},
        "page_action": "native", "page_size": 15, "sort_action": "native", "filter_action": "native", "style_as_list_view": True,
    }

def get_graph_figure_layout_defaults(theme: Theme) -> dict[str, Any]:
    """
    Get default layout settings for Graph figure components.
    
    Args:
        theme (Theme): Theme object to use for styling
        
    Returns:
        dict: Dictionary of Plotly figure layout properties
    """
    return {"paper_bgcolor": theme.panel_bg, "plot_bgcolor": theme.panel_bg, "font": {"color": theme.text_light, "family": "Inter, sans-serif"}}

def get_graph_wrapper_default_style(theme: Theme) -> dict[str, Any]:
    """
    Get default styles for Graph wrapper components.
    
    Args:
        theme (Theme): Theme object to use for styling
        
    Returns:
        dict: Dictionary of CSS styles
    """
    return {}

def get_grid_default_style(theme: Theme) -> dict[str, Any]:
    """
    Get default styles for Grid components.
    
    Args:
        theme (Theme): Theme object to use for styling
        
    Returns:
        dict: Dictionary of CSS styles
    """
    return {"backgroundColor": theme.panel_bg}

def get_listbox_default_styles(theme: Theme, height_px: int = 160) -> dict[str, Any]:
    """
    Get default styles for ListBox components.
    
    Args:
        theme (Theme): Theme object to use for styling
        height_px (int, optional): Height of the listbox in pixels. Defaults to 160.
        
    Returns:
        dict: Dictionary containing style dictionaries for different ListBox elements
    """
    return {
        "style": {"backgroundColor": theme.panel_bg, "color": theme.text_light, "borderRadius": "4px", "border": f"1px solid {theme.secondary}", "overflowY": "auto", "height": f"{height_px}px", "padding": "4px", "fontFamily": "Inter, sans-serif"},
        "inputStyle": {"marginRight": "8px", "cursor": "pointer"},
        "labelStyle": {"display": "block", "cursor": "pointer", "padding": "2px 0", "color": theme.text_light}
    }

def get_radiobutton_default_styles(theme: Theme) -> dict[str, Any]:
    """
    Get default styles for RadioButton components.
    
    Args:
        theme (Theme): Theme object to use for styling
        
    Returns:
        dict: Dictionary containing style dictionaries for different RadioButton elements
    """
    return {
        "style": {"color": theme.text_light, "fontFamily": "Inter, sans-serif"},
        "input_checked_style": {"backgroundColor": theme.primary, "borderColor": theme.primary},
        "label_checked_style": {"color": theme.primary, "fontWeight": "bold"},
        "inputStyle": {"marginRight": "5px", "cursor": "pointer"},
        "labelStyle": {"marginRight": "15px", "cursor": "pointer"}
    }

def get_tabs_default_styles(theme: Theme) -> dict[str, Any]:
    """
    Returns a dictionary containing default style properties for Tabs (dbc.Tabs and dbc.Tab).
    
    Args:
        theme (Theme): Theme object to use for styling
        
    Returns:
        dict: Dictionary containing style dictionaries for different Tabs elements
    """
    return {
        "main_tabs_style": {
            "borderBottom": f"1px solid {theme.primary}",
            "marginBottom": "1rem",
            "fontFamily": "Inter, sans-serif",
        },
        "tab_style": {
            "backgroundColor": theme.panel_bg,
            "padding": "0.5rem 1rem",
            "border": f"1px solid {theme.secondary}",
            "borderBottom": "none",
            "marginRight": "2px",
            "borderRadius": "4px 4px 0 0",
        },
        "active_tab_style": {
            "backgroundColor": theme.panel_bg,
            "fontWeight": "bold",
            "padding": "0.5rem 1rem",
            "border": f"1px solid {theme.primary}",
            "borderBottom": f"1px solid {theme.panel_bg}",
            "marginRight": "2px",
            "borderRadius": "4px 4px 0 0",
            "position": "relative",
            "zIndex": "1",
        },
        "label_style": {
            "color": theme.text_subtle,
            "textDecoration": "none",
        },
        "active_label_style": {
            "color": theme.primary,
            "fontWeight": "bold",
            "textDecoration": "none",
        },
    }
