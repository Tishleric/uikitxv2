# uikitxv2/src/components/datatable.py

from dash import dash_table
import pandas as pd

# Corrected relative import: Go up one level (..) to src, then down to core
from ..core import BaseComponent
# Corrected relative import: Go up one level (..) to src, then down to utils
from ..themes import default_theme, get_datatable_default_styles

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
        # Get default styles based on theme
        default_styles = get_datatable_default_styles(self.theme)
        
        # Merge default styles with instance-specific styles
        final_style_table = {**default_styles["style_table"], **self.style_table}
        final_style_cell = {**default_styles["style_cell"], **self.style_cell}
        final_style_header = {**default_styles["style_header"], **self.style_header}
        
        # Merge conditional styles, prioritizing instance-specific ones
        final_style_data_conditional = [
            *default_styles["style_data_conditional"],
            *self.style_data_conditional
        ]

        # If you need to use self.className, wrap the DataTable in an html.Div:
        # return html.Div(className=self.className, children=[ dash_table.DataTable(...) ])
        # For now, just remove className from the DataTable call:

        return dash_table.DataTable(
            id=self.id,
            columns=self.columns,
            data=self.data,
            page_size=self.page_size if self.page_size is not None else default_styles["page_size"],
            style_table=final_style_table,
            style_cell=final_style_cell,
            style_header=final_style_header,
            style_data_conditional=final_style_data_conditional,
            # page_action=default_styles["page_action"],  # REMOVED: No longer valid in newer Dash versions
            sort_action=default_styles["sort_action"],
            filter_action=default_styles["filter_action"],
            # style_as_list_view=default_styles["style_as_list_view"]  # REMOVED: No longer valid
            # className=self.className # REMOVED: This argument is not allowed
        )

