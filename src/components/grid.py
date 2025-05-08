# uikitxv2/src/components/grid.py

import dash_bootstrap_components as dbc
from dash import html
from dash.development.base_component import Component as DashBaseComponent

# Corrected relative import: Go up one level (..) to src, then down to core
from ..core.base_component import BaseComponent
# Corrected relative import: Go up one level (..) to src, then down to utils
from ..utils.colour_palette import default_theme # Only default_theme seems used here

class Grid(BaseComponent):
    """
    A wrapper for creating a grid layout using dbc.Row and dbc.Col.
    Children should be a list of components or tuples (component, width_dict).
    width_dict example: {'xs': 12, 'md': 6, 'lg': 4}
    """
    def __init__(self, id, children=None, theme=None, style=None, className=""):
        super().__init__(id, theme)
        self.children = children if children is not None else []
        self.style = style if style is not None else {}
        self.className = className

    def _build_cols(self):
        """Builds dbc.Col components from children."""
        cols = []
        children_to_process = self.children
        if not isinstance(children_to_process, (list, tuple)):
             children_to_process = [children_to_process]

        for child_item in children_to_process:
            child_component = None
            width_args = {} # Default: Col will auto-size

            if isinstance(child_item, tuple) and len(child_item) == 2:
                child_component = child_item[0]
                if isinstance(child_item[1], dict):
                    # Assumes dict specifies widths like {'xs': 12, 'md': 6}
                    width_args = child_item[1]
                elif isinstance(child_item[1], int):
                    # Assumes int is the default width (applied to all sizes unless overridden)
                    width_args = {'width': child_item[1]} # Use 'width' key for default span
            else:
                # Assume the item is just the component, let Col auto-size
                child_component = child_item

            rendered_child = None
            # Check if it's one of our custom components or needs rendering
            if isinstance(child_component, BaseComponent) or \
               (hasattr(child_component, 'render') and callable(child_component.render) and \
               not isinstance(child_component, (DashBaseComponent, dict, str))):
                rendered_child = child_component.render()
            else:
                # Assume it's already a Dash component, dict, string, etc.
                rendered_child = child_component

            if rendered_child is not None:
                 cols.append(dbc.Col(rendered_child, **width_args)) # Pass width dict as kwargs

        return cols

    def render(self):
        # Apply theme defaults if not overridden by style prop
        # Example: default_style = {'padding': '10px 0'}
        # final_style = {**default_style, **self.style}

        return dbc.Row(
            children=self._build_cols(),
            id=self.id,
            style=self.style, # Use self.style directly
            className=self.className
        )

