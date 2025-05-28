"""
Checkbox component for UIKit v2.

A wrapper around Dash Core Components' Checklist that provides consistent theming
and styling across the application.
"""

from typing import List, Dict, Any, Optional, Union
from dash import dcc, html
from ..utils.colour_palette import Theme


class Checkbox:
    """
    A themed checkbox component wrapper for dcc.Checklist.
    
    Provides consistent styling and theming for checkbox lists across the application.
    """
    
    def __init__(
        self,
        id: str,
        options: List[Dict[str, Any]],
        value: Optional[List[Union[str, int]]] = None,
        theme: Optional[Theme] = None,
        inline: bool = False,
        style: Optional[Dict[str, Any]] = None,
        className: Optional[str] = None,
        labelStyle: Optional[Dict[str, Any]] = None,
        inputStyle: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """
        Initialize checkbox component.
        
        Args:
            id: Unique identifier for the component
            options: List of option dictionaries with 'label' and 'value' keys
            value: List of selected values
            theme: Theme protocol instance for styling
            inline: Whether to display options inline
            style: Additional CSS styles for the container
            className: CSS class name
            labelStyle: CSS styles for labels
            inputStyle: CSS styles for checkboxes
            **kwargs: Additional props for dcc.Checklist
        """
        self.id = id
        self.options = options
        self.value = value or []
        self.theme = theme
        self.inline = inline
        self.style = style or {}
        self.className = className
        self.labelStyle = labelStyle or {}
        self.inputStyle = inputStyle or {}
        self.kwargs = kwargs
    
    def _get_default_styles(self) -> Dict[str, Dict[str, Any]]:
        """Get default styles based on theme."""
        if not self.theme:
            return {
                "container": {},
                "label": {},
                "input": {}
            }
        
        return {
            "container": {
                "color": self.theme.text_light,
                "fontFamily": "Inter, sans-serif"
            },
            "label": {
                "color": self.theme.text_light,
                "marginLeft": "8px",
                "marginRight": "15px" if self.inline else "0px",
                "display": "block" if not self.inline else "inline-block",
                "cursor": "pointer",
                "fontSize": "14px",
                "fontWeight": "400"
            },
            "input": {
                "marginRight": "5px",
                "accentColor": self.theme.primary,
                "cursor": "pointer"
            }
        }
    
    def render(self) -> dcc.Checklist:
        """
        Render the checkbox component.
        
        Returns:
            Configured dcc.Checklist component
        """
        default_styles = self._get_default_styles()
        
        # Merge default styles with user-provided styles
        container_style = {**default_styles["container"], **self.style}
        label_style = {**default_styles["label"], **self.labelStyle}
        input_style = {**default_styles["input"], **self.inputStyle}
        
        return dcc.Checklist(
            id=self.id,
            options=self.options,
            value=self.value,
            inline=self.inline,
            style=container_style,
            className=self.className,
            labelStyle=label_style,
            inputStyle=input_style,
            **self.kwargs
        ) 