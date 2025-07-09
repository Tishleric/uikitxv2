"""
Tests for dynamic Grid + DataTable population.

These tests verify that the Grid+DataTable pattern works correctly
when data is populated dynamically (e.g., via callbacks).
"""

import pytest
from dash import Dash, Input, Output, callback
from lib.components.advanced import DataTable, Grid
from lib.components.factory import DashComponentFactory


class TestGridDataTableDynamic:
    """Test dynamic population of DataTable within Grid."""
    
    def test_empty_datatable_renders_in_grid(self):
        """Test that empty DataTable renders correctly in Grid."""
        # Create empty datatable
        datatable = DataTable(id="empty-table", data=[], columns=[])
        grid = Grid(id="container", children=[datatable])
        
        # Render the grid
        rendered = grid.render()
        
        # Grid should render even with empty table
        assert rendered is not None
        assert hasattr(rendered, 'children')
    
    def test_datatable_updates_preserve_grid_structure(self):
        """Test that updating DataTable data doesn't break Grid structure."""
        # Start with empty table
        datatable = DataTable(id="dynamic-table", data=[], columns=[])
        grid = Grid(id="grid", children=[(datatable, {"xs": 12, "md": 8})])
        
        # Update table data (simulating callback)
        datatable.data = [{"name": "John", "age": 30}]
        datatable.columns = [
            {"name": "Name", "id": "name"},
            {"name": "Age", "id": "age"}
        ]
        
        # Grid structure should remain intact
        assert len(grid.children) == 1
        assert grid.children[0][0] == datatable
        assert grid.children[0][1] == {"xs": 12, "md": 8}
    
    def test_factory_datatable_in_grid_dynamic(self):
        """Test factory-created DataTable in Grid with dynamic updates."""
        factory = DashComponentFactory()
        
        # Create empty table in grid using factory
        grid = factory.create_datatable_in_grid(
            grid_id="factory-grid",
            table_id="factory-table",
            grid_width={"xs": 12, "lg": 10}
        )
        
        # Get the datatable reference
        datatable = grid.children[0][0]
        
        # Initially empty
        assert datatable.data == []
        assert datatable.columns == []
        
        # Update with data
        datatable.data = [
            {"product": "A", "sales": 100},
            {"product": "B", "sales": 200}
        ]
        datatable.columns = [
            {"name": "Product", "id": "product"},
            {"name": "Sales", "id": "sales"}
        ]
        
        # Verify updates
        assert len(datatable.data) == 2
        assert len(datatable.columns) == 2
    
    def test_dash_app_with_dynamic_datatable(self):
        """Test a minimal Dash app with dynamic DataTable in Grid."""
        app = Dash(__name__)
        
        # Create components
        datatable = DataTable(id="app-table", data=[], columns=[])
        grid = Grid(id="app-grid", children=[datatable])
        button = Button(id="load-btn", text="Load Data")
        
        # Layout
        app.layout = html.Div([button, grid])
        
        # Callback to populate table
        @app.callback(
            [Output("app-table", "data"), Output("app-table", "columns")],
            Input("load-btn", "n_clicks")
        )
        def load_data(n_clicks):
            if n_clicks:
                data = [{"x": i, "y": i**2} for i in range(5)]
                columns = [{"name": "X", "id": "x"}, {"name": "Y", "id": "y"}]
                return data, columns
            return [], []
        
        # Test the callback logic
        data, columns = load_data(1)
        assert len(data) == 5
        assert len(columns) == 2
        assert data[0] == {"x": 0, "y": 0}
        assert data[4] == {"x": 4, "y": 16}
    
    def test_multiple_datatables_in_grid(self):
        """Test Grid with multiple DataTables that update independently."""
        # Create two datatables
        table1 = DataTable(id="table1", data=[], columns=[])
        table2 = DataTable(id="table2", data=[], columns=[])
        
        # Put both in a grid
        grid = Grid(
            id="multi-grid",
            children=[
                (table1, {"xs": 12, "md": 6}),
                (table2, {"xs": 12, "md": 6})
            ]
        )
        
        # Update tables independently
        table1.data = [{"a": 1}]
        table1.columns = [{"name": "A", "id": "a"}]
        
        table2.data = [{"b": 2}]
        table2.columns = [{"name": "B", "id": "b"}]
        
        # Verify independent updates
        assert table1.data != table2.data
        assert len(grid.children) == 2
    
    def test_conditional_datatable_visibility(self):
        """Test pattern for conditionally showing/hiding DataTable."""
        from dash import html
        
        # This simulates a common pattern where table visibility
        # depends on whether it has data
        datatable = DataTable(id="conditional-table", data=[], columns=[])
        
        # Function to wrap table with conditional visibility
        def create_conditional_layout(table):
            if table.data:
                return Grid(id="visible-grid", children=[table])
            else:
                return html.Div("No data available", id="empty-message")
        
        # Test with empty data
        layout_empty = create_conditional_layout(datatable)
        assert layout_empty.id == "empty-message"
        
        # Update with data
        datatable.data = [{"value": 123}]
        datatable.columns = [{"name": "Value", "id": "value"}]
        
        # Test with data
        layout_with_data = create_conditional_layout(datatable)
        assert layout_with_data.id == "visible-grid"


# Import required for test
from lib.components.basic import Button
from dash import html 