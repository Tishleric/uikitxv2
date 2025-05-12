# uikitxv2/src/components/container.py

import dash_bootstrap_components as dbc
from dash import html
from dash.development.base_component import Component as DashBaseComponent
from ..core.base_component import BaseComponent
from ..utils.colour_palette import default_theme

class Container(BaseComponent):
    """
    A wrapper for dbc.Container that allows for easier styling and theme integration.
    It can accept other BaseComponent instances as children and will render them.
    """
    def __init__(self, id, children=None, theme=None, style=None, fluid=False, className=""):
        """
        Initialize a Container component.
        
        Args:
            id (str): The component's ID, required for Dash callbacks.
            children (list or component, optional): Child components to display. Defaults to None.
            theme (Any, optional): Theme object for styling. Defaults to None.
            style (dict, optional): Additional CSS styles to apply. Defaults to None.
            fluid (bool, optional): Whether the container should be responsive full-width. Defaults to False.
            className (str, optional): Additional CSS classes. Defaults to "".
        """
        super().__init__(id, theme)
        self.children = children if children is not None else []
        self.style = style if style is not None else {}
        self.fluid = fluid
        self.className = className

    def render(self):
        """
        Render the Container component.
        
        Processes all children, rendering any custom components, and returns a
        styled dbc.Container with the processed children.
        
        Returns:
            dbc.Container: A Dash Bootstrap Component container with rendered children.
        """
        processed_children = []
        
        children_to_process = self.children
        if not isinstance(children_to_process, (list, tuple)):
            children_to_process = [children_to_process]

        for child in children_to_process:
            if hasattr(child, 'render') and callable(child.render) and \
               not isinstance(child, (DashBaseComponent, dict, str)):
                processed_children.append(child.render())
            elif isinstance(child, (list, tuple)):
                temp_list = []
                for sub_child in child:
                    if hasattr(sub_child, 'render') and callable(sub_child.render) and \
                       not isinstance(sub_child, (DashBaseComponent, dict, str)):
                        temp_list.append(sub_child.render())
                    else:
                        temp_list.append(sub_child)
                processed_children.extend(temp_list)
            else:
                processed_children.append(child)
        
        return dbc.Container(
            children=processed_children,
            id=self.id,
            style=self.style,
            fluid=self.fluid,
            className=self.className
        )

