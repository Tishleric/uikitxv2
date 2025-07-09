"""
Component factory for creating Dash components with sensible defaults.

This factory provides an optional way to create components with default values,
without affecting any existing code or component behavior.
"""

from typing import Any, Dict, Optional, List, Union
from .defaults import COMPONENT_DEFAULTS
from . import templates


class DashComponentFactory:
    """
    Factory for creating Dash components with sensible defaults.
    
    This factory creates the SAME component instances as direct instantiation,
    just with convenient default values. All existing code continues to work
    without any modifications.
    
    Example:
        factory = DashComponentFactory(theme=my_theme)
        table = factory.create_datatable(id="my-table")
        # Equivalent to: DataTable(id="my-table", data=[], columns=[], ...)
    """
    
    def __init__(self, theme: Optional[Dict[str, Any]] = None, 
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize the component factory.
        
        Args:
            theme: Optional theme to apply to all created components
            config: Optional configuration overrides for defaults
        """
        self.theme = theme
        self.config = config or {}
        
    def _get_defaults(self, component_type: str) -> Dict[str, Any]:
        """
        Get default configuration for a component type.
        
        Args:
            component_type: Type of component (e.g., 'datatable', 'button')
            
        Returns:
            Dictionary of default values
        """
        # Start with built-in defaults
        defaults = COMPONENT_DEFAULTS.get(component_type, {}).copy()
        
        # Apply any config overrides
        if component_type in self.config:
            defaults.update(self.config[component_type])
            
        return defaults
        
    def _merge_kwargs(self, component_type: str, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge factory defaults with user-provided kwargs.
        
        User kwargs always take precedence over factory defaults.
        
        Args:
            component_type: Type of component
            kwargs: User-provided keyword arguments
            
        Returns:
            Merged keyword arguments
        """
        defaults = self._get_defaults(component_type)
        final_kwargs = {**defaults, **kwargs}
        
        # Apply theme if not explicitly provided
        if 'theme' not in kwargs and self.theme:
            final_kwargs['theme'] = self.theme
            
        return final_kwargs
    
    def create_datatable(self, id: str, **kwargs) -> Any:
        """
        Create a DataTable instance with factory defaults.
        
        Returns the EXACT same DataTable instance as:
        DataTable(id, **kwargs)
        
        Args:
            id: Component ID
            **kwargs: Additional arguments (override defaults)
            
        Returns:
            DataTable instance
        """
        from ..advanced import DataTable
        
        final_kwargs = self._merge_kwargs('datatable', kwargs)
        return DataTable(id, **final_kwargs)
    
    def create_grid(self, id: str, **kwargs) -> Any:
        """
        Create a Grid instance with factory defaults.
        
        Args:
            id: Component ID
            **kwargs: Additional arguments (override defaults)
            
        Returns:
            Grid instance
        """
        from ..advanced import Grid
        
        final_kwargs = self._merge_kwargs('grid', kwargs)
        return Grid(id, **final_kwargs)
    
    def create_button(self, id: str, **kwargs) -> Any:
        """
        Create a Button instance with factory defaults.
        
        Args:
            id: Component ID
            **kwargs: Additional arguments (override defaults)
            
        Returns:
            Button instance
        """
        from ..basic import Button
        
        final_kwargs = self._merge_kwargs('button', kwargs)
        return Button(id, **final_kwargs)
    
    def create_graph(self, id: str, **kwargs) -> Any:
        """
        Create a Graph instance with factory defaults.
        
        Args:
            id: Component ID
            **kwargs: Additional arguments (override defaults)
            
        Returns:
            Graph instance
        """
        from ..advanced import Graph
        
        final_kwargs = self._merge_kwargs('graph', kwargs)
        return Graph(id, **final_kwargs)
    
    def create_container(self, id: str, **kwargs) -> Any:
        """
        Create a Container instance with factory defaults.
        
        Args:
            id: Component ID
            **kwargs: Additional arguments (override defaults)
            
        Returns:
            Container instance
        """
        from ..basic import Container
        
        final_kwargs = self._merge_kwargs('container', kwargs)
        return Container(id, **final_kwargs)
    
    def create_text_input(self, id: str, **kwargs) -> Any:
        """
        Create a TextInput instance with factory defaults.
        
        Args:
            id: Component ID
            **kwargs: Additional arguments (override defaults)
            
        Returns:
            TextInput instance
        """
        from ..basic import TextInput
        
        final_kwargs = self._merge_kwargs('text_input', kwargs)
        return TextInput(id, **final_kwargs)
    
    def create_number_input(self, id: str, **kwargs) -> Any:
        """
        Create a NumberInput instance with factory defaults.
        
        Args:
            id: Component ID
            **kwargs: Additional arguments (override defaults)
            
        Returns:
            NumberInput instance
        """
        from ..basic import NumberInput
        
        final_kwargs = self._merge_kwargs('number_input', kwargs)
        return NumberInput(id, **final_kwargs)
    
    def create_dropdown(self, id: str, **kwargs) -> Any:
        """
        Create a Dropdown instance with factory defaults.
        
        Args:
            id: Component ID
            **kwargs: Additional arguments (override defaults)
            
        Returns:
            Dropdown instance
        """
        from ..basic import Dropdown
        
        final_kwargs = self._merge_kwargs('dropdown', kwargs)
        return Dropdown(id, **final_kwargs)
    
    def create_date_picker(self, id: str, **kwargs) -> Any:
        """
        Create a DatePicker instance with factory defaults.
        
        Args:
            id: Component ID
            **kwargs: Additional arguments (override defaults)
            
        Returns:
            DatePicker instance
        """
        from ..basic import DatePicker
        
        final_kwargs = self._merge_kwargs('date_picker', kwargs)
        return DatePicker(id, **final_kwargs)
    
    def create_checkbox(self, id: str, **kwargs) -> Any:
        """
        Create a Checkbox instance with factory defaults.
        
        Args:
            id: Component ID
            **kwargs: Additional arguments (override defaults)
            
        Returns:
            Checkbox instance
        """
        from ..basic import Checkbox
        
        final_kwargs = self._merge_kwargs('checkbox', kwargs)
        return Checkbox(id, **final_kwargs)
    
    def create_radio_button(self, id: str, **kwargs) -> Any:
        """
        Create a RadioButton instance with factory defaults.
        
        Args:
            id: Component ID
            **kwargs: Additional arguments (override defaults)
            
        Returns:
            RadioButton instance
        """
        from ..basic import RadioButton
        
        final_kwargs = self._merge_kwargs('radio_button', kwargs)
        return RadioButton(id, **final_kwargs)
    
    def create_slider(self, id: str, **kwargs) -> Any:
        """
        Create a Slider instance with factory defaults.
        
        Args:
            id: Component ID
            **kwargs: Additional arguments (override defaults)
            
        Returns:
            Slider instance
        """
        from ..basic import Slider
        
        final_kwargs = self._merge_kwargs('slider', kwargs)
        return Slider(id, **final_kwargs)
    
    # Template methods for common patterns
    
    def create_datatable_in_grid(self, 
                                grid_id: str, 
                                table_id: str,
                                grid_width: Optional[Union[int, Dict[str, int]]] = None,
                                table_kwargs: Optional[Dict[str, Any]] = None,
                                grid_kwargs: Optional[Dict[str, Any]] = None) -> Any:
        """
        Convenience method to create a DataTable wrapped in a Grid.
        
        This is equivalent to:
        grid = Grid(grid_id, children=[DataTable(table_id)])
        
        Args:
            grid_id: ID for the grid component
            table_id: ID for the datatable component  
            grid_width: Width specification for the table column
            table_kwargs: Additional kwargs for the datatable
            grid_kwargs: Additional kwargs for the grid
            
        Returns:
            Grid instance containing the DataTable
        """
        return templates.create_datatable_in_grid(
            self, grid_id, table_id, grid_width, table_kwargs, grid_kwargs
        )
    
    def create_form_grid(self,
                        grid_id: str,
                        form_elements: List[Dict[str, Any]],
                        submit_button_text: str = "Submit",
                        grid_kwargs: Optional[Dict[str, Any]] = None) -> Any:
        """
        Create a form-like grid with input elements and a submit button.
        
        Args:
            grid_id: ID for the grid component
            form_elements: List of dicts describing form elements
            submit_button_text: Text for the submit button
            grid_kwargs: Additional kwargs for the grid
            
        Returns:
            Grid instance containing form elements
        """
        return templates.create_form_grid(
            self, grid_id, form_elements, submit_button_text, grid_kwargs
        )
    
    def create_dashboard_layout(self,
                              container_id: str,
                              title: str,
                              sections: List[Dict[str, Any]],
                              container_kwargs: Optional[Dict[str, Any]] = None) -> Any:
        """
        Create a dashboard layout with title and sections.
        
        Args:
            container_id: ID for the main container
            title: Dashboard title
            sections: List of section definitions
            container_kwargs: Additional kwargs for the container
            
        Returns:
            Container instance with dashboard layout
        """
        return templates.create_dashboard_layout(
            self, container_id, title, sections, container_kwargs
        ) 