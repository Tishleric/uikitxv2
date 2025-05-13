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
    "get_tabs_default_styles", # Added Tabs styles function
]


@dataclass(frozen=True, slots=True)
class Theme:
    """
    Defines a color theme for UI components.
    
    This frozen dataclass represents a consistent color scheme that can be
    applied across all UI components. It defines colors for backgrounds,
    text, and interactive elements.
    """
    base_bg: str
    """Background color for the main application background."""
    
    panel_bg: str
    """Background color for panels and component containers."""
    
    primary: str
    """Primary brand/accent color for important UI elements."""
    
    secondary: str
    """Secondary color for less prominent UI elements."""
    
    accent: str
    """Accent color for highlighting specific elements."""
    
    text_light: str
    """Light text color for normal content."""
    
    text_subtle: str
    """Subtle/muted text color for less important content."""
    
    danger: str
    """Color for indicating errors or dangerous actions."""
    
    success: str
    """Color for indicating success or completion."""


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

# --- Component Default Style Functions ---

def get_combobox_default_style(theme: Theme) -> dict[str, Any]:
    """
    Get default styling for ComboBox components.
    
    Args:
        theme (Theme): The theme to use for styling.
        
    Returns:
        dict[str, Any]: Dictionary of CSS style properties.
    """
    return {"backgroundColor": theme.panel_bg, "color": theme.text_light, "borderRadius": "4px"}

def get_button_default_style(theme: Theme) -> dict[str, Any]:
    """
    Get default styling for Button components.
    
    Args:
        theme (Theme): The theme to use for styling.
        
    Returns:
        dict[str, Any]: Dictionary of CSS style properties.
    """
    return {"backgroundColor": theme.primary, "borderColor": theme.primary, "color": theme.text_light, "borderRadius": "4px", "fontFamily": "Inter, sans-serif", "fontSize": "15px", "padding": "0.375rem 0.75rem", "borderWidth": "1px", "borderStyle": "solid", "textDecoration": "none", "display": "inline-block", "fontWeight": "400", "lineHeight": "1.5", "textAlign": "center", "verticalAlign": "middle", "cursor": "pointer", "userSelect": "none"}

def get_container_default_style(theme: Theme) -> dict[str, Any]:
    """
    Get default styling for Container components.
    
    Args:
        theme (Theme): The theme to use for styling.
        
    Returns:
        dict[str, Any]: Dictionary of CSS style properties.
    """
    return {
        "backgroundColor": theme.panel_bg,
        "padding": "15px",
        "borderRadius": "4px"
    }

def get_datatable_default_styles(theme: Theme) -> Dict[str, Any]:
    """
    Get default styling for DataTable components.
    
    Args:
        theme (Theme): The theme to use for styling.
        
    Returns:
        Dict[str, Any]: Dictionary containing style settings for different 
        parts of the DataTable (table, header, cells, etc.).
    """
    return {
        "style_table": {"overflowX": "auto", "minWidth": "100%"},
        "style_header": {
            "backgroundColor": theme.panel_bg, 
            "color": theme.text_light, 
            "fontWeight": "bold", 
            "border": f"1px solid {theme.secondary}", 
            "textAlign": "left", 
            "padding": "10px"
        },
        "style_cell": {
            "backgroundColor": theme.base_bg, 
            "color": theme.text_light, 
            "border": f"1px solid {theme.secondary}", 
            "padding": "10px", 
            "textAlign": "left", 
            "fontFamily": "Inter, sans-serif",
            "fontSize": "0.9rem"
        },
        "style_data": {},
        "style_data_conditional": [{'if': {'row_index': 'odd'}, 'backgroundColor': theme.panel_bg}],
        "style_filter": {"backgroundColor": theme.base_bg, "color": theme.text_light, "border": f"1px solid {theme.secondary}", "padding": "5px"},
        "page_action": "native", 
        "page_size": 10, 
        "sort_action": "native", 
        "filter_action": "none",  # Using string 'none' to properly disable filters
        "style_as_list_view": True,
    }

def get_graph_figure_layout_defaults(theme: Theme) -> dict[str, Any]:
    """
    Get default Plotly figure layout settings with theme colors.
    
    Args:
        theme (Theme): The theme to use for styling.
        
    Returns:
        dict[str, Any]: Dictionary of Plotly layout properties.
    """
    return {
        "plot_bgcolor": theme.base_bg,
        "paper_bgcolor": theme.panel_bg,
        "font_color": theme.text_light,
        "xaxis": {
            "gridcolor": theme.secondary,
            "linecolor": theme.secondary,
            "zerolinecolor": theme.secondary
        },
        "yaxis": {
            "gridcolor": theme.secondary,
            "linecolor": theme.secondary,
            "zerolinecolor": theme.secondary
        },
        "legend": {
            "bgcolor": theme.panel_bg,
            "bordercolor": theme.secondary
        }
    }

def get_graph_wrapper_default_style(theme: Theme) -> dict[str, Any]:
    """
    Get default styling for the Graph component wrapper.
    
    Args:
        theme (Theme): The theme to use for styling.
        
    Returns:
        dict[str, Any]: Dictionary of CSS style properties.
    """
    return {}

def get_grid_default_style(theme: Theme) -> dict[str, Any]:
    """
    Get default styling for Grid components.
    
    Args:
        theme (Theme): The theme to use for styling.
        
    Returns:
        dict[str, Any]: Dictionary of CSS style properties.
    """
    return {"backgroundColor": theme.panel_bg}

def get_listbox_default_styles(theme: Theme, height_px: int = 160) -> dict[str, Any]:
    """
    Get default styling for ListBox components.
    
    Args:
        theme (Theme): The theme to use for styling.
        height_px (int, optional): Height of the listbox in pixels. Defaults to 160.
        
    Returns:
        dict[str, Any]: Dictionary containing style settings for different
        parts of the ListBox (container, inputs, labels).
    """
    return {
        "style": {"backgroundColor": theme.panel_bg, "color": theme.text_light, "borderRadius": "4px", "border": f"1px solid {theme.secondary}", "overflowY": "auto", "height": f"{height_px}px", "padding": "4px", "fontFamily": "Inter, sans-serif"},
        "inputStyle": {"marginRight": "8px", "cursor": "pointer"},
        "labelStyle": {"display": "block", "cursor": "pointer", "padding": "2px 0", "color": theme.text_light}
    }

def get_radiobutton_default_styles(theme: Theme) -> dict[str, Any]:
    """
    Get default styling for RadioButton components.
    
    Args:
        theme (Theme): The theme to use for styling.
        
    Returns:
        dict[str, Any]: Dictionary containing style settings for different
        parts of the RadioButton (container, inputs, labels).
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
    Get default styling for Tabs components.
    
    Returns a dictionary containing default style properties for Tabs 
    (dbc.Tabs and dbc.Tab) with theme-based colors.
    
    Args:
        theme (Theme): The theme to use for styling.
        
    Returns:
        dict[str, Any]: Dictionary containing style settings for different
        parts of the Tabs component (container, active tab, labels).
    """
    return {
        # Styles for the main dbc.Tabs container
        "main_tabs_style": {
            "borderBottom": f"1px solid {theme.primary}",
            "marginBottom": "1rem", # Space below the row of tabs
            "fontFamily": "Inter, sans-serif",
        },
        # Styles for individual dbc.Tab components
        "tab_style": { # Style for the inactive tab *container* (<li>)
            "backgroundColor": theme.panel_bg,
            "padding": "0.5rem 1rem",
            "border": f"1px solid {theme.secondary}",
            "borderBottom": "none", # Critical for tab appearance
            "marginRight": "2px",
            "borderRadius": "4px 4px 0 0", # Rounded top corners
        },
        "active_tab_style": { # Style for the active tab *container* (<li>)
            "backgroundColor": theme.panel_bg, # Often same as inactive, or slightly lighter/different
            "fontWeight": "bold", # Handled by active_label_style for text, but can be here too
            "padding": "0.5rem 1rem",
            "border": f"1px solid {theme.primary}", # Highlight with primary color
            "borderBottom": f"1px solid {theme.panel_bg}", # Make bottom border match panel to "connect"
            "marginRight": "2px",
            "borderRadius": "4px 4px 0 0",
            "position": "relative", # For z-index or pseudo-elements if needed
            "zIndex": "1", # Ensure active tab is "on top" of the bottom border
        },
        "label_style": { # Style specifically for the inactive tab *label* (<a> link inside <li>)
            "color": theme.text_subtle, # More subtle color for inactive tabs
            "textDecoration": "none",
        },
        "active_label_style": { # Style specifically for the active tab *label* (<a> link inside <li>)
            "color": theme.primary, # Primary theme color for active label text
            "fontWeight": "bold",
            "textDecoration": "none",
        },
        # Style for the content area of the active tab (the panel below the tabs)
        # Note: dbc.Tab content is styled by the component placed inside it,
        # but if dbc.Tabs itself adds a wrapper for content, this could be useful.
        # Often, the content area takes its background from the page or a surrounding container.
        # "content_style": {
        #     "padding": "1rem",
        #     "border": f"1px solid {theme.primary}",
        #     "borderTop": "none",
        #     "backgroundColor": theme.panel_bg,
        # }
    }
