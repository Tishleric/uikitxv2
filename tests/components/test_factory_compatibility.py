"""
Tests for backwards compatibility of the component factory.

These tests ensure that existing code continues to work without modification
when the factory is added to the codebase.
"""

import pytest


class TestBackwardsCompatibility:
    """Test that factory doesn't break existing functionality."""
    
    def test_direct_imports_still_work(self):
        """Test that all existing import patterns continue to work."""
        # All these imports should work without error
        from lib.components.advanced import DataTable, Grid, Graph
        from lib.components.basic import Button, Container, TextInput
        from lib.components import BaseComponent
        
        # Verify imports succeeded
        assert DataTable is not None
        assert Button is not None
        assert BaseComponent is not None
    
    def test_component_instantiation_unchanged(self):
        """Test that direct component instantiation works as before."""
        from lib.components.advanced import DataTable
        from lib.components.basic import Button
        
        # This is how existing code creates components
        table = DataTable(
            id="my-table",
            data=[{"a": 1, "b": 2}],
            columns=[{"name": "A", "id": "a"}],
            page_size=20
        )
        
        button = Button(
            id="my-button",
            text="Click Me",
            variant="primary",
            disabled=False
        )
        
        # Verify components created successfully
        assert table.id == "my-table"
        assert table.data == [{"a": 1, "b": 2}]
        assert table.page_size == 20
        
        assert button.id == "my-button"
        assert button.text == "Click Me"
        assert button.variant == "primary"
    
    def test_callbacks_work_with_components(self):
        """Test that Dash callbacks work with components."""
        from dash import Output, Input
        from lib.components.advanced import DataTable
        
        table = DataTable(id="test-table")
        
        # Simulate callback registration (would be in actual Dash app)
        output = Output(table.id, "data")
        input = Input(table.id, "selected_rows")
        
        assert output.component_id == "test-table"
        assert output.component_property == "data"
        assert input.component_id == "test-table"
        assert input.component_property == "selected_rows"
    
    def test_component_render_method_unchanged(self):
        """Test that component render methods work as before."""
        from lib.components.advanced import DataTable
        from lib.components.basic import Button
        
        table = DataTable(id="test-table")
        button = Button(id="test-button", text="Test")
        
        # Render methods should return Dash components
        rendered_table = table.render()
        rendered_button = button.render()
        
        assert hasattr(rendered_table, '_prop_names')  # Dash component property
        assert hasattr(rendered_button, '_prop_names')
    
    def test_factory_is_optional(self):
        """Test that factory import is completely optional."""
        # This simulates existing code that doesn't know about factory
        try:
            # Don't import factory at all
            from lib.components.advanced import DataTable
            from lib.components.basic import Button
            
            # Create components the old way
            table = DataTable(id="table1")
            button = Button(id="button1", text="OK")
            
            # Everything should work fine
            assert table is not None
            assert button is not None
            
        except ImportError:
            pytest.fail("Existing imports failed when factory exists")
    
    def test_grid_with_datatable_pattern(self):
        """Test the existing pattern of DataTable in Grid."""
        from lib.components.advanced import DataTable, Grid
        
        # This is how existing code creates datatable in grid
        datatable = DataTable(
            id="sales-table",
            data=[],
            columns=[]
        )
        
        grid = Grid(
            id="main-grid",
            children=[datatable]
        )
        
        assert grid.id == "main-grid"
        assert len(grid.children) == 1
        assert grid.children[0].id == "sales-table"
    
    def test_dynamic_datatable_population(self):
        """Test that dynamic population pattern still works."""
        from lib.components.advanced import DataTable, Grid
        
        # Create empty datatable
        table = DataTable(id="dynamic-table", data=[], columns=[])
        grid = Grid(id="container-grid", children=[table])
        
        # Simulate callback updating data
        new_data = [{"x": 1, "y": 2}, {"x": 3, "y": 4}]
        new_columns = [{"name": "X", "id": "x"}, {"name": "Y", "id": "y"}]
        
        # This would happen in a callback
        table.data = new_data
        table.columns = new_columns
        
        assert table.data == new_data
        assert table.columns == new_columns
    
    def test_theme_application_unchanged(self):
        """Test that manual theme application still works."""
        from lib.components.advanced import DataTable
        from lib.components.themes import default_theme
        
        # Existing code might apply themes manually
        custom_theme = {"primary": "#FF0000", "secondary": "#00FF00"}
        
        table = DataTable(
            id="themed-table",
            theme=custom_theme
        )
        
        assert table.theme == custom_theme
    
    def test_no_side_effects_on_import(self):
        """Test that importing factory doesn't cause side effects."""
        # Import everything
        from lib.components.advanced import DataTable
        from lib.components.factory import DashComponentFactory
        
        # Create component without factory
        table1 = DataTable(id="table1")
        
        # Create factory
        factory = DashComponentFactory()
        
        # Create another component without factory
        table2 = DataTable(id="table2")
        
        # Both should work identically
        assert type(table1) == type(table2)
        assert table1.data == table2.data == [] 