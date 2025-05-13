# uikitxv2/src/components/container.py

import dash_bootstrap_components as dbc
from dash import html # Added for completeness if html components are ever direct children
from dash.development.base_component import Component as DashBaseComponent # For robust type checking
from ..core.base_component import BaseComponent
from ..utils.colour_palette import default_theme, get_container_default_style

class Container(BaseComponent):
    """
    A wrapper for dbc.Container that allows for easier styling and theme integration.
    It can accept other BaseComponent instances as children and will render them.
    """
    def __init__(self, id, children=None, theme=None, style=None, fluid=False, className=""):
        super().__init__(id, theme)
        self.children = children if children is not None else []
        self.style = style if style is not None else {}
        self.fluid = fluid
        self.className = className

    def render(self):
        # Get default styles from utility function
        default_style = get_container_default_style(self.theme)
        
        # Merge default styles with instance-specific styles
        final_style = {**default_style, **self.style}

        processed_children = []
        
        # Ensure self.children is always a list to iterate over
        children_to_process = self.children
        if not isinstance(children_to_process, (list, tuple)):
            children_to_process = [children_to_process]

        for child in children_to_process:
            if hasattr(child, 'render') and callable(child.render) and \
               not isinstance(child, (DashBaseComponent, dict, str)):
                # If it's one of our custom components (or any object with .render())
                # that isn't already a Dash component, a dict (Dash component shorthand), or a string.
                processed_children.append(child.render())
            elif isinstance(child, (list, tuple)):
                # If the child is itself a list/tuple, process its items and extend the main list
                # This prevents creating nested lists of children like [[comp1, comp2]]
                temp_list = []
                for sub_child in child:
                    if hasattr(sub_child, 'render') and callable(sub_child.render) and \
                       not isinstance(sub_child, (DashBaseComponent, dict, str)):
                        temp_list.append(sub_child.render())
                    # No need for `elif isinstance(sub_child, BaseComponent)` here if caught by hasattr
                    else:
                        # Already a Dash component, dict, string, or other primitive
                        temp_list.append(sub_child)
                processed_children.extend(temp_list) # Key change: use extend
            else:
                # Already a Dash component (dict, DashBaseComponent instance), string, or number
                processed_children.append(child)
        
        return dbc.Container(
            children=processed_children,
            id=self.id,
            style=final_style,
            fluid=self.fluid,
            className=self.className
        )

