"""
Range Slider component for UIKit v2.

A wrapper around Dash Core Components' RangeSlider that provides consistent theming
and styling across the application.
"""

from typing import Dict, Any, Optional, List, Union
from dash import dcc, html
from ..themes import Theme


class RangeSlider:
    """
    A themed range slider component wrapper for dcc.RangeSlider.
    
    Provides consistent styling and theming for range selection across the application.
    """
    
    def __init__(
        self,
        id: str,
        min: float,
        max: float,
        step: Optional[float] = None,
        value: Optional[List[float]] = None,
        marks: Optional[Dict[Union[int, float], Any]] = None,
        theme: Optional[Theme] = None,
        vertical: bool = False,
        allowCross: bool = True,
        disabled: bool = False,
        pushable: Union[bool, int] = False,
        tooltip: Optional[Dict[str, Any]] = None,
        style: Optional[Dict[str, Any]] = None,
        className: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize range slider component.
        
        Args:
            id: Unique identifier for the component
            min: Minimum value of the slider
            max: Maximum value of the slider
            step: Step size for the slider
            value: Current selected range [start, end]
            marks: Dictionary of marks to display on the slider
            theme: Theme protocol instance for styling
            vertical: Whether the slider is vertical
            allowCross: Whether handles can cross each other
            disabled: Whether the slider is disabled
            pushable: Whether handles push each other when they meet
            tooltip: Tooltip configuration
            style: Additional CSS styles
            className: CSS class name
            **kwargs: Additional props for dcc.RangeSlider
        """
        self.id = id
        self.min = min
        self.max = max
        self.step = step
        self.value = value or [min, max]
        self.marks = marks
        self.theme = theme
        self.vertical = vertical
        self.allowCross = allowCross
        self.disabled = disabled
        self.pushable = pushable
        self.tooltip = tooltip or {"placement": "bottom", "always_visible": False}
        self.style = style or {}
        self.className = className
        self.kwargs = kwargs
    
    def _get_default_styles(self) -> Dict[str, Any]:
        """Get default styles based on theme."""
        if not self.theme:
            return {}
        
        return {
            "marginBottom": "20px",
            "marginTop": "10px",
            "padding": "0 10px"
        }
    
    def _generate_marks(self) -> Dict[Union[int, float], Any]:
        """Generate default marks if none provided."""
        if self.marks is not None:
            return self.marks
        
        # Generate 5 evenly spaced marks
        range_size = self.max - self.min
        step_size = range_size / 4
        
        marks = {}
        for i in range(5):
            value = self.min + (i * step_size)
            # Format the label based on the value magnitude
            if abs(value) >= 1000:
                label = f"{value/1000:.1f}k"
            elif abs(value) >= 1:
                label = f"{value:.1f}"
            else:
                label = f"{value:.3f}"
            
            marks[value] = {
                "label": label,
                "style": {
                    "color": self.theme.text_light if self.theme else "#333",
                    "fontSize": "12px"
                }
            }
        
        return marks
    
    def render(self) -> html.Div:
        """
        Render the range slider component.
        
        Returns:
            Configured dcc.RangeSlider wrapped in styled html.Div
        """
        default_styles = self._get_default_styles()
        container_style = {**default_styles, **self.style}
        
        # Generate marks if not provided
        marks = self._generate_marks()
        
        return html.Div([
            dcc.RangeSlider(
                id=self.id,
                min=self.min,
                max=self.max,
                step=self.step,
                value=self.value,
                marks=marks,
                vertical=self.vertical,
                allowCross=self.allowCross,
                disabled=self.disabled,
                pushable=self.pushable,
                tooltip=self.tooltip,
                className=self.className,
                **self.kwargs
            )
        ], style=container_style) 