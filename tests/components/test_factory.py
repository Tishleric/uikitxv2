"""
Tests for the DashComponentFactory.

These tests ensure the factory creates components correctly with defaults
and that user overrides work as expected.
"""

import pytest
from lib.components.factory import DashComponentFactory
from lib.components.advanced import DataTable, Grid, Graph
from lib.components.basic import Button, Container, TextInput, Dropdown


class TestDashComponentFactory:
    """Test the component factory functionality."""
    
    def test_factory_creates_datatable_with_defaults(self):
        """Test that factory creates DataTable with default values."""
        factory = DashComponentFactory()
        table = factory.create_datatable(id="test-table")
        
        assert table.id == "test-table"
        assert table.data == []
        assert table.columns == []
        assert table.page_size == 10
        assert table.style_table == {}
        assert table.style_cell == {}
        assert table.style_header == {}
        assert table.style_data_conditional == []
    
    def test_factory_respects_user_overrides(self):
        """Test that user-provided values override factory defaults."""
        factory = DashComponentFactory()
        custom_data = [{"col1": "value1", "col2": "value2"}]
        custom_columns = [{"name": "Column 1", "id": "col1"}]
        
        table = factory.create_datatable(
            id="test-table",
            data=custom_data,
            columns=custom_columns,
            page_size=25
        )
        
        assert table.data == custom_data
        assert table.columns == custom_columns
        assert table.page_size == 25
    
    def test_factory_applies_theme(self):
        """Test that factory applies theme to components."""
        custom_theme = {"primary": "#123456"}
        factory = DashComponentFactory(theme=custom_theme)
        
        table = factory.create_datatable(id="test-table")
        button = factory.create_button(id="test-button")
        
        assert table.theme == custom_theme
        assert button.theme == custom_theme
    
    def test_factory_theme_can_be_overridden(self):
        """Test that explicit theme argument overrides factory theme."""
        factory_theme = {"primary": "#123456"}
        override_theme = {"primary": "#654321"}
        
        factory = DashComponentFactory(theme=factory_theme)
        table = factory.create_datatable(id="test-table", theme=override_theme)
        
        assert table.theme == override_theme
    
    def test_factory_config_overrides_defaults(self):
        """Test that factory config can override component defaults."""
        config = {
            "datatable": {"page_size": 50},
            "button": {"variant": "secondary"}
        }
        
        factory = DashComponentFactory(config=config)
        table = factory.create_datatable(id="test-table")
        button = factory.create_button(id="test-button")
        
        assert table.page_size == 50
        assert button.variant == "secondary"
    
    def test_all_component_creation_methods(self):
        """Test that all component creation methods work."""
        factory = DashComponentFactory()
        
        # Test each component type
        components = {
            "datatable": factory.create_datatable(id="dt"),
            "grid": factory.create_grid(id="gr"),
            "button": factory.create_button(id="bt"),
            "graph": factory.create_graph(id="gp"),
            "container": factory.create_container(id="ct"),
            "text_input": factory.create_text_input(id="ti"),
            "number_input": factory.create_number_input(id="ni"),
            "dropdown": factory.create_dropdown(id="dd"),
            "date_picker": factory.create_date_picker(id="dp"),
            "checkbox": factory.create_checkbox(id="cb"),
            "radio_button": factory.create_radio_button(id="rb"),
            "slider": factory.create_slider(id="sl")
        }
        
        # Verify all components were created with correct IDs
        for comp_type, component in components.items():
            assert hasattr(component, 'id')
            assert component.id == comp_type[:2]  # First 2 chars of type
    
    def test_create_datatable_in_grid(self):
        """Test the datatable_in_grid template method."""
        factory = DashComponentFactory()
        
        grid = factory.create_datatable_in_grid(
            grid_id="test-grid",
            table_id="test-table",
            grid_width={"xs": 12, "md": 8}
        )
        
        assert grid.id == "test-grid"
        assert len(grid.children) == 1
        
        # Check that the child is a tuple with DataTable and width
        child_tuple = grid.children[0]
        assert isinstance(child_tuple, tuple)
        assert len(child_tuple) == 2
        
        datatable, width = child_tuple
        assert datatable.id == "test-table"
        assert width == {"xs": 12, "md": 8}
    
    def test_create_form_grid(self):
        """Test the form grid template method."""
        factory = DashComponentFactory()
        
        form_elements = [
            {"type": "text_input", "id": "name", "kwargs": {"placeholder": "Name"}},
            {"type": "dropdown", "id": "country", "width": {"xs": 12, "md": 4}}
        ]
        
        grid = factory.create_form_grid(
            grid_id="form-grid",
            form_elements=form_elements,
            submit_button_text="Save"
        )
        
        assert grid.id == "form-grid"
        assert len(grid.children) == 3  # 2 form elements + submit button
        
        # Check submit button
        last_child = grid.children[-1]
        button = last_child[0] if isinstance(last_child, tuple) else last_child
        assert button.text == "Save"
        assert button.id == "form-grid-submit"
    
    def test_factory_creates_identical_types(self):
        """Ensure factory components are identical to direct instantiation."""
        factory = DashComponentFactory()
        
        # Direct creation
        direct_table = DataTable(id="test", data=[], columns=[])
        direct_button = Button(id="test", text="Button")
        
        # Factory creation
        factory_table = factory.create_datatable(id="test")
        factory_button = factory.create_button(id="test")
        
        # Must be same type
        assert type(direct_table) == type(factory_table)
        assert type(direct_button) == type(factory_button)
        
        # Must have same base properties
        assert direct_table.id == factory_table.id
        assert direct_button.id == factory_button.id 