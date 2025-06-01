"""Test UI components functionality."""

import pytest
from dash import html


class TestButton:
    """Test Button component."""
    
    def test_button_creation(self, sample_theme):
        """Test creating a Button component."""
        from components import Button
        
        button = Button(
            id="test-button",
            label="Click me",
            theme=sample_theme
        )
        
        assert button.id == "test-button"
        assert button.label == "Click me"
        assert button.theme == sample_theme
    
    def test_button_render(self):
        """Test Button render method."""
        from components import Button
        
        button = Button(id="test-btn", label="Test")
        rendered = button.render()
        
        # Should return a dbc.Button
        assert hasattr(rendered, 'id')
        assert rendered.id == "test-btn"
        assert rendered.children == "Test"


class TestCheckbox:
    """Test Checkbox component."""
    
    def test_checkbox_creation(self):
        """Test creating a Checkbox component."""
        from components import Checkbox
        
        checkbox = Checkbox(
            id="test-checkbox",
            options=[
                {"label": "Option 1", "value": "opt1"},
                {"label": "Option 2", "value": "opt2"}
            ],
            value=["opt1"]
        )
        
        assert checkbox.id == "test-checkbox"
        assert len(checkbox.options) == 2
        assert checkbox.value == ["opt1"]
    
    def test_checkbox_render(self):
        """Test Checkbox render method."""
        from components import Checkbox
        
        checkbox = Checkbox(
            id="test-cb",
            options=["A", "B", "C"],
            value=["A"]
        )
        rendered = checkbox.render()
        
        # Should return a dcc.Checklist
        assert hasattr(rendered, 'id')
        assert rendered.id == "test-cb"
        assert len(rendered.options) == 3
        assert rendered.value == ["A"]


class TestContainer:
    """Test Container component."""
    
    def test_container_with_children(self, sample_theme):
        """Test Container with child components."""
        from components import Container
        
        children = [
            html.H1("Title"),
            html.P("Paragraph"),
            html.Div("Content")
        ]
        
        container = Container(
            id="test-container",
            children=children,
            theme=sample_theme,
            fluid=True
        )
        
        assert container.id == "test-container"
        assert len(container.children) == 3
        assert container.fluid is True
    
    def test_container_render(self):
        """Test Container render method."""
        from components import Container
        
        container = Container(
            id="test-cont",
            children=html.Div("Test content")
        )
        rendered = container.render()
        
        # Should return a dbc.Container
        assert hasattr(rendered, 'id')
        assert rendered.id == "test-cont"
        assert rendered.children is not None


class TestDataTable:
    """Test DataTable component."""
    
    def test_datatable_with_dataframe(self, sample_dataframe):
        """Test DataTable with pandas DataFrame."""
        from components import DataTable
        
        table = DataTable(
            id="test-table",
            data=sample_dataframe,
            page_size=10
        )
        
        assert table.id == "test-table"
        assert table.page_size == 10
        # Data should be converted to records format
        assert isinstance(table.data, list)
        assert len(table.data) == 3  # Sample has 3 rows
    
    def test_datatable_render(self, sample_dataframe):
        """Test DataTable render method."""
        from components import DataTable
        
        table = DataTable(
            id="test-dt",
            data=sample_dataframe
        )
        rendered = table.render()
        
        # Should return a dash_table.DataTable
        assert hasattr(rendered, 'id')
        assert rendered.id == "test-dt"
        assert len(rendered.data) == 3
        assert len(rendered.columns) == 3  # id, name, value columns


class TestGraph:
    """Test Graph component."""
    
    def test_graph_creation(self, sample_plotly_figure):
        """Test creating a Graph component."""
        from components import Graph
        
        graph = Graph(
            id="test-graph",
            figure=sample_plotly_figure,
            config={'displayModeBar': False}
        )
        
        assert graph.id == "test-graph"
        assert graph.figure == sample_plotly_figure
        assert graph.config['displayModeBar'] is False
    
    def test_graph_render(self, sample_plotly_figure):
        """Test Graph render method."""
        from components import Graph
        
        graph = Graph(
            id="test-plot",
            figure=sample_plotly_figure
        )
        rendered = graph.render()
        
        # Should return a dcc.Graph
        assert hasattr(rendered, 'id')
        assert rendered.id == "test-plot"
        assert rendered.figure == sample_plotly_figure


class TestGrid:
    """Test Grid component."""
    
    def test_grid_with_components(self):
        """Test Grid layout with components."""
        from components import Grid, Button
        
        children = [
            (Button(id="btn1", label="Button 1"), {"width": 6}),
            (Button(id="btn2", label="Button 2"), {"width": 6})
        ]
        
        grid = Grid(
            id="test-grid",
            children=children
        )
        
        assert grid.id == "test-grid"
        assert len(grid.children) == 2
    
    def test_grid_render(self):
        """Test Grid render method."""
        from components import Grid
        
        grid = Grid(
            id="test-layout",
            children=[
                (html.Div("Col 1"), {"width": 4}),
                (html.Div("Col 2"), {"width": 8})
            ]
        )
        rendered = grid.render()
        
        # Should return a dbc.Row
        assert hasattr(rendered, 'id')
        assert rendered.id == "test-layout"
        assert hasattr(rendered, 'children')
        assert len(rendered.children) == 2  # Two columns


class TestTabs:
    """Test Tabs component."""
    
    def test_tabs_creation(self):
        """Test creating a Tabs component."""
        from components import Tabs
        
        tabs = Tabs(
            id="test-tabs",
            tabs=[
                ("Tab 1", html.Div("Content 1")),
                ("Tab 2", html.Div("Content 2"))
            ],
            active_tab="tab-1"
        )
        
        assert tabs.id == "test-tabs"
        assert len(tabs.tabs_data) == 2  # Internal attribute is tabs_data
        assert tabs.active_tab == "tab-1"
    
    def test_tabs_render(self):
        """Test Tabs render method."""
        from components import Tabs
        
        tabs = Tabs(
            id="test-tb",
            tabs=[
                ("First", html.P("First content")),
                ("Second", html.P("Second content"))
            ]
        )
        rendered = tabs.render()
        
        # Should return a dbc.Tabs
        assert hasattr(rendered, 'id')
        assert rendered.id == "test-tb"
        assert hasattr(rendered, 'children')


class TestThemeApplication:
    """Test theme application across components."""
    
    def test_default_theme_applied(self):
        """Test that components use default theme when none specified."""
        from components import Button, Container
        from components.themes import default_theme
        
        button = Button(id="btn", label="Test")
        container = Container(id="cont", children=[])
        
        # Should use default theme
        assert button.theme == default_theme
        assert container.theme == default_theme
    
    def test_custom_theme_override(self, sample_theme):
        """Test that custom theme overrides default."""
        from components import Button
        
        button = Button(id="btn", label="Test", theme=sample_theme)
        
        assert button.theme == sample_theme
        # Remove the _get_theme test as it's not a public method 