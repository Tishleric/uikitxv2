"""
Loading component wrapper for dcc.Loading with theme support.
"""

from dash import dcc, html
from typing import Any, List, Union, Optional
from ..core import BaseComponent
from ..themes import Theme, default_theme


class Loading(BaseComponent):
    """
    A wrapper around dcc.Loading that provides theme-consistent loading indicators.
    
    Args:
        id (str): The ID of this component
        children (Union[Component, List[Component]]): The content to wrap with loading indicator
        type (str): Type of loading indicator ('graph', 'cube', 'circle', 'dot', 'default')
        theme (Theme): Theme object for styling
        color (str, optional): Override color for the loading indicator
        parent_style (dict, optional): Style to apply to the parent container
        fullscreen (bool): Whether the loading indicator should be fullscreen
        debug (bool): If True, loading indicator will always be visible
        **kwargs: Additional properties passed to dcc.Loading
    
    Example:
        ```python
        loading = Loading(
            id="my-loading",
            children=html.Div("Content that takes time to load"),
            type="circle",
            theme=default_theme
        )
        ```
    """
    
    def __init__(
        self,
        id: str,
        children: Union[Any, List[Any]] = None,
        type: str = "default",
        theme: Theme = default_theme,
        color: Optional[str] = None,
        parent_style: Optional[dict] = None,
        fullscreen: bool = False,
        debug: bool = False,
        **kwargs
    ):
        """Initialize the Loading component."""
        super().__init__(id=id, theme=theme)
        self.children = children
        self.type = type
        self.color = color or theme.primary
        self.parent_style = parent_style or {}
        self.fullscreen = fullscreen
        self.debug = debug
        self.additional_props = kwargs
    
    def render(self) -> dcc.Loading:
        """
        Render the Loading component.
        
        Returns:
            dcc.Loading: A Dash Loading component with theme styling
        """
        # Default parent style with theme colors
        default_parent_style = {
            'position': 'relative',
            'minHeight': '60px' if not self.fullscreen else '100vh',
            'display': 'flex',
            'alignItems': 'center',
            'justifyContent': 'center'
        }
        
        # Merge with custom parent style
        parent_style = {**default_parent_style, **self.parent_style}
        
        # Create the loading component
        loading_props = {
            'id': self.id,
            'children': self.children,
            'type': self.type,
            'color': self.color,
            'parent_style': parent_style,
            'fullscreen': self.fullscreen,
            'debug': self.debug,
            **self.additional_props
        }
        
        return dcc.Loading(**loading_props) 