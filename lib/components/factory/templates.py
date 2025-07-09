"""
Template methods for common component patterns.

These are convenience methods that create pre-configured component combinations.
"""

from typing import Any, Dict, List, Optional, Union


def create_datatable_in_grid(factory: 'DashComponentFactory', 
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
        factory: The component factory instance
        grid_id: ID for the grid component
        table_id: ID for the datatable component
        grid_width: Width specification for the table column
        table_kwargs: Additional kwargs for the datatable
        grid_kwargs: Additional kwargs for the grid
        
    Returns:
        Grid instance containing the DataTable
    """
    table_kwargs = table_kwargs or {}
    grid_kwargs = grid_kwargs or {}
    
    # Create the datatable
    datatable = factory.create_datatable(table_id, **table_kwargs)
    
    # Prepare children for grid
    if grid_width is not None:
        children = [(datatable, grid_width)]
    else:
        children = [datatable]
    
    # Create and return the grid
    return factory.create_grid(
        grid_id,
        children=children,
        **grid_kwargs
    )


def create_form_grid(factory: 'DashComponentFactory',
                    grid_id: str,
                    form_elements: List[Dict[str, Any]],
                    submit_button_text: str = "Submit",
                    grid_kwargs: Optional[Dict[str, Any]] = None) -> Any:
    """
    Create a form-like grid with input elements and a submit button.
    
    Args:
        factory: The component factory instance
        grid_id: ID for the grid component
        form_elements: List of dicts describing form elements
        submit_button_text: Text for the submit button
        grid_kwargs: Additional kwargs for the grid
        
    Returns:
        Grid instance containing form elements
    """
    grid_kwargs = grid_kwargs or {}
    children = []
    
    # Create form elements
    for element in form_elements:
        element_type = element.get('type', 'text_input')
        element_id = element.get('id')
        element_kwargs = element.get('kwargs', {})
        element_width = element.get('width', {"xs": 12, "md": 6})
        
        # Create the appropriate component
        if element_type == 'text_input':
            component = factory.create_text_input(element_id, **element_kwargs)
        elif element_type == 'number_input':
            component = factory.create_number_input(element_id, **element_kwargs)
        elif element_type == 'dropdown':
            component = factory.create_dropdown(element_id, **element_kwargs)
        elif element_type == 'date_picker':
            component = factory.create_date_picker(element_id, **element_kwargs)
        elif element_type == 'checkbox':
            component = factory.create_checkbox(element_id, **element_kwargs)
        else:
            continue
            
        children.append((component, element_width))
    
    # Add submit button
    submit_button = factory.create_button(
        f"{grid_id}-submit",
        text=submit_button_text,
        variant="primary"
    )
    children.append((submit_button, {"xs": 12, "md": 3}))
    
    return factory.create_grid(
        grid_id,
        children=children,
        **grid_kwargs
    )


def create_dashboard_layout(factory: 'DashComponentFactory',
                          container_id: str,
                          title: str,
                          sections: List[Dict[str, Any]],
                          container_kwargs: Optional[Dict[str, Any]] = None) -> Any:
    """
    Create a dashboard layout with title and sections.
    
    Args:
        factory: The component factory instance
        container_id: ID for the main container
        title: Dashboard title
        sections: List of section definitions
        container_kwargs: Additional kwargs for the container
        
    Returns:
        Container instance with dashboard layout
    """
    from dash import html
    
    container_kwargs = container_kwargs or {}
    children = []
    
    # Add title
    children.append(html.H1(title, className="dashboard-title"))
    
    # Add sections
    for section in sections:
        section_title = section.get('title')
        section_components = section.get('components', [])
        
        if section_title:
            children.append(html.H3(section_title, className="section-title"))
            
        # Create grid for section components
        grid_id = f"{container_id}-{section.get('id', 'section')}-grid"
        grid = factory.create_grid(
            grid_id,
            children=section_components
        )
        children.append(grid)
        
    return factory.create_container(
        container_id,
        children=children,
        **container_kwargs
    ) 