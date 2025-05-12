# uikitxv2/src/components/datatable.py

from dash import dash_table
import pandas as pd

# Corrected relative import: Go up one level (..) to src, then down to core
from ..core.base_component import BaseComponent
# Corrected relative import: Go up one level (..) to src, then down to utils
from ..utils.colour_palette import default_theme

class DataTable(BaseComponent):
    """
    A wrapper for dash_table.DataTable with theme integration.
    
    This component creates a styled data table using Dash's DataTable component,
    with automatic theming support. It handles both dict-based data and pandas DataFrames.
    """
    def __init__(self, id, data=None, columns=None, theme=None, style_table=None, style_cell=None, style_header=None, style_data_conditional=None, page_size=10, className=""):
        """
        Initialize a DataTable component.
        
        Args:
            id (str): The component's unique identifier.
            data (list or DataFrame, optional): Data to display in the table. Can be a list of dicts
                or a pandas DataFrame. Defaults to None (empty list).
            columns (list, optional): Column definitions. If None and data is provided, 
                will be auto-generated from data keys. Defaults to None.
            theme (dict, optional): Theme configuration. Defaults to None.
            style_table (dict, optional): Styles for the table container. Defaults to None.
            style_cell (dict, optional): Styles for all cells. Defaults to None.
            style_header (dict, optional): Styles for header cells. Defaults to None.
            style_data_conditional (list, optional): Conditional styling rules. Defaults to None.
            page_size (int, optional): Number of rows per page. Defaults to 10.
            className (str, optional): Additional CSS class names. Not directly used by dash_table.
                Defaults to "".
        """
        # Note: className is accepted here but NOT passed to dash_table.DataTable below
        super().__init__(id, theme)
        self.data = data if data is not None else []
        self.columns = columns if columns is not None else []
        self.style_table = style_table if style_table is not None else {}
        self.style_cell = style_cell if style_cell is not None else {}
        self.style_header = style_header if style_header is not None else {}
        self.style_data_conditional = style_data_conditional if style_data_conditional is not None else []
        self.page_size = page_size
        self.className = className # Store it, but don't pass it directly to dash_table

        # Basic validation or processing if needed
        if isinstance(self.data, pd.DataFrame):
            self.data = self.data.to_dict('records')
        if not self.columns and self.data:
            sample_record = self.data[0]
            self.columns = [{"name": i, "id": i} for i in sample_record.keys()]

    def render(self):
        """
        Render the data table component.
        
        Creates a styled data table with pagination, applying theme-based styles
        to the table container, cells, and headers.
        
        Returns:
            dash_table.DataTable: The rendered Dash DataTable component.
        """
        # Define default styles based on theme
        default_style_table = {'overflowX': 'auto', 'minWidth': '100%', **self.style_table}
        default_style_cell = {
            'padding': '10px', 'textAlign': 'left', 'backgroundColor': self.theme.base_bg,
            'color': self.theme.text_light, 'border': f'1px solid {self.theme.secondary}',
            'fontFamily': 'Inter, sans-serif', 'fontSize': '0.9rem',
            **self.style_cell
        }
        default_style_header = {
            'backgroundColor': self.theme.panel_bg, 'fontWeight': 'bold',
            'color': self.theme.text_light, 'border': f'1px solid {self.theme.secondary}',
            **self.style_header
        }
        default_style_data_conditional = [
            {'if': {'row_index': 'odd'}, 'backgroundColor': self.theme.panel_bg},
            *self.style_data_conditional
        ]

        # If you need to use self.className, wrap the DataTable in an html.Div:
        # return html.Div(className=self.className, children=[ dash_table.DataTable(...) ])
        # For now, just remove className from the DataTable call:

        return dash_table.DataTable(
            id=self.id,
            columns=self.columns,
            data=self.data,
            page_size=self.page_size,
            style_table=default_style_table,
            style_cell=default_style_cell,
            style_header=default_style_header,
            style_data_conditional=default_style_data_conditional
            # className=self.className # REMOVED: This argument is not allowed
        )

