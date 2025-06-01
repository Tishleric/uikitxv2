# lib/components/basic/tooltip.py

import dash_bootstrap_components as dbc
from typing import Any, Dict, Optional, Union

# Import from parent directories in the new structure
from ..core import BaseComponent
from ..themes import default_theme

class Tooltip(BaseComponent):
    """
    A wrapper for dbc.Tooltip that integrates with the theme system.
    
    This component creates a tooltip that appears on hover over a target element,
    with support for HTML content and automatic theming.
    """
    
    def __init__(
        self, 
        id: str,
        target: Union[str, Dict[str, str]],
        children: Any = None,
        theme: Optional[Any] = None,
        style: Optional[Dict[str, Any]] = None,
        className: str = "",
        placement: str = "auto",
        delay: Optional[Dict[str, int]] = None,
        **kwargs
    ):
        """
        Initialize a Tooltip component.
        
        Args:
            id: The component's unique identifier.
            target: ID of the target element or dict with 'type' and 'index' for pattern matching.
            children: Content to display in the tooltip (can be string or HTML elements).
            theme: Theme configuration. Defaults to None.
            style: Additional CSS styles to apply. Defaults to None.
            className: Additional CSS class names. Defaults to "".
            placement: Tooltip placement relative to target. Options: 'auto', 'top', 'bottom', 
                      'left', 'right', etc. Defaults to "auto".
            delay: Dict with 'show' and/or 'hide' keys for delays in ms. Defaults to None.
            **kwargs: Additional properties passed to dbc.Tooltip.
        """
        super().__init__(id, theme)
        self.target = target
        self.children = children
        self.style = style if style is not None else {}
        self.className = className
        self.placement = placement
        self.delay = delay
        self.kwargs = kwargs

    def render(self) -> dbc.Tooltip:
        """
        Render the tooltip component.
        
        Returns:
            dbc.Tooltip: The rendered Dash Bootstrap tooltip component.
        """
        # Apply theme styles
        theme_style = {}
        if self.theme:
            theme_style = {
                'backgroundColor': self.theme.panel_bg,
                'color': self.theme.text_light,
                'border': f'1px solid {self.theme.secondary}',
                'borderRadius': '4px',
                'padding': '8px 12px',
                'fontSize': '14px',
                'maxWidth': '400px',  # Reasonable max width for readability
            }
        
        # Merge theme styles with custom styles
        final_style = {**theme_style, **self.style}
        
        # Build tooltip properties
        tooltip_props = {
            'id': self.id,
            'target': self.target,
            'children': self.children,
            'style': final_style,
            'className': self.className,
            'placement': self.placement,
        }
        
        # Add optional properties
        if self.delay is not None:
            tooltip_props['delay'] = self.delay
            
        # Add any additional kwargs
        tooltip_props.update(self.kwargs)
        
        return dbc.Tooltip(**tooltip_props) 