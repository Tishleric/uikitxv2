"""
Toggle component for UIKit v2.

A wrapper around Dash DAQ's ToggleSwitch that provides consistent theming
and styling across the application.
"""

from typing import Dict, Any, Optional
import dash_daq as daq
from dash import html
from ..themes import Theme


class Toggle:
    """
    A themed toggle switch component wrapper for daq.ToggleSwitch.
    
    Provides consistent styling and theming for toggle switches across the application.
    """
    
    def __init__(
        self,
        id: str,
        value: bool = False,
        label: Optional[str] = None,
        labelPosition: str = "right",
        theme: Optional[Theme] = None,
        disabled: bool = False,
        size: int = 30,
        style: Optional[Dict[str, Any]] = None,
        className: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize toggle component.
        
        Args:
            id: Unique identifier for the component
            value: Initial toggle state (True/False)
            label: Text label for the toggle
            labelPosition: Position of label ("top", "bottom", "left", "right")
            theme: Theme protocol instance for styling
            disabled: Whether the toggle is disabled
            size: Size of the toggle switch
            style: Additional CSS styles
            className: CSS class name
            **kwargs: Additional props for daq.ToggleSwitch
        """
        self.id = id
        self.value = value
        self.label = label
        self.labelPosition = labelPosition
        self.theme = theme
        self.disabled = disabled
        self.size = size
        self.style = style or {}
        self.className = className
        self.kwargs = kwargs
    
    def _get_default_styles(self) -> Dict[str, Any]:
        """Get default styles based on theme."""
        if not self.theme:
            return {}
        
        return {
            "display": "flex",
            "alignItems": "center",
            "gap": "10px",
            "color": self.theme.text_light,
            "fontFamily": "Inter, sans-serif",
            "fontSize": "14px",
            "fontWeight": "400"
        }
    
    def _get_toggle_theme(self) -> Dict[str, str]:
        """Get theme colors for the toggle switch."""
        if not self.theme:
            return {
                "primary": "#007BFF",
                "secondary": "#6C757D"
            }
        
        return {
            "primary": self.theme.primary,
            "secondary": self.theme.secondary
        }
    
    def render(self) -> html.Div:
        """
        Render the toggle component.
        
        Returns:
            html.Div containing the configured daq.ToggleSwitch with optional label
        """
        default_styles = self._get_default_styles()
        container_style = {**default_styles, **self.style}
        
        toggle_theme = self._get_toggle_theme()
        
        toggle_switch = daq.ToggleSwitch(
            id=self.id,
            value=self.value,
            disabled=self.disabled,
            size=self.size,
            color=toggle_theme["primary"],
            **self.kwargs
        )
        
        # If no label, return just the toggle
        if not self.label:
            return html.Div(
                children=[toggle_switch],
                style=container_style,
                className=self.className
            )
        
        # Create label element
        label_element = html.Label(
            self.label,
            style={
                "color": self.theme.text_light if self.theme else "#333",
                "fontSize": "14px",
                "fontWeight": "400",
                "margin": "0"
            }
        )
        
        # Arrange label and toggle based on position
        if self.labelPosition in ["left", "top"]:
            children = [label_element, toggle_switch]
            flex_direction = "column" if self.labelPosition == "top" else "row"
        else:  # right or bottom
            children = [toggle_switch, label_element]
            flex_direction = "column" if self.labelPosition == "bottom" else "row"
        
        container_style["flexDirection"] = flex_direction
        
        return html.Div(
            children=children,
            style=container_style,
            className=self.className
        ) 