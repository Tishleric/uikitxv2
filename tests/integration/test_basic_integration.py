"""Basic integration tests for UIKitXv2 components and monitoring."""

import pytest
from dash import Dash, html
import time

from components import Button, ComboBox, DataTable, Graph, Grid, Container, Tooltip
from monitoring.decorators import TraceTime, TraceCloser, TraceCpu, TraceMemory
from monitoring.logging import setup_logging, shutdown_logging
import plotly.graph_objects as go


def test_components_render_in_dash_app():
    """Test that all components can be rendered in a Dash app."""
    app = Dash(__name__)
    
    # Create various components
    button = Button(id="test-button", label="Click Me")
    combo = ComboBox(id="test-combo", options=["Option 1", "Option 2"])
    
    # Create a graph
    fig = go.Figure(data=[go.Scatter(x=[1, 2, 3], y=[4, 5, 6])])
    graph = Graph(id="test-graph", figure=fig)
    
    # Create a data table
    table = DataTable(
        id="test-table",
        columns=[{"name": "Col1", "id": "col1"}, {"name": "Col2", "id": "col2"}],
        data=[{"col1": "A", "col2": 1}, {"col1": "B", "col2": 2}]
    )
    
    # Create tooltip
    tooltip = Tooltip(
        id="test-tooltip",
        target="test-button",
        children="This button does something!"
    )
    
    # Create layout with Grid
    app.layout = Container(
        id="main-container",
        children=[
            Grid(
                id="main-grid",
                children=[
                    button.render(),
                    combo.render(),
                    graph.render(),
                    table.render(),
                    tooltip.render()
                ]
            ).render()
        ]
    ).render()
    
    # Verify app can be created without errors
    assert app is not None
    assert app.layout is not None


@TraceCloser()
@TraceCpu()
@TraceMemory()  
@TraceTime()
def sample_function_with_all_decorators(x, y):
    """Sample function to test decorator stacking."""
    time.sleep(0.01)  # Small delay to ensure measurable time
    return x + y


def test_decorator_integration():
    """Test that all decorators work together."""
    # Setup logging
    setup_logging(db_path=":memory:")  # Use in-memory database for testing
    
    try:
        # Call decorated function
        result = sample_function_with_all_decorators(5, 3)
        assert result == 8
        
        # Call it again to test multiple invocations
        result2 = sample_function_with_all_decorators(10, 20)
        assert result2 == 30
        
    finally:
        # Cleanup
        shutdown_logging()


def test_components_with_tooltips():
    """Test that tooltips work with various components."""
    app = Dash(__name__)
    
    # Create components with unique IDs
    button1 = Button(id="btn-1", label="Button 1")
    button2 = Button(id="btn-2", label="Button 2")
    combo = ComboBox(id="combo-1", options=["A", "B", "C"])
    
    # Create tooltips for each
    tooltip1 = Tooltip(
        id="tooltip-1",
        target="btn-1",
        children="This is Button 1"
    )
    
    tooltip2 = Tooltip(
        id="tooltip-2", 
        target="btn-2",
        children=html.Div([
            html.Strong("Button 2 Info:"),
            html.P("This button has HTML content in its tooltip")
        ])
    )
    
    tooltip3 = Tooltip(
        id="tooltip-3",
        target="combo-1",
        children="Select an option from this dropdown",
        placement="bottom"
    )
    
    # Create layout
    app.layout = html.Div([
        button1.render(),
        button2.render(),
        combo.render(),
        tooltip1.render(),
        tooltip2.render(),
        tooltip3.render()
    ])
    
    # Verify all components rendered
    assert app.layout is not None
    assert len(app.layout.children) == 6  # 3 components + 3 tooltips


def test_data_flow_integration():
    """Test data flow from service through visualization."""
    from trading.actant.eod import ActantDataService
    
    # Create service
    service = ActantDataService()
    
    # Test basic operations (without actual data files)
    assert service.get_scenario_headers() == []
    assert service.get_metric_names() == []
    assert not service.is_pm_data_loaded()
    
    # Create a graph component (would normally use service data)
    fig = go.Figure()
    graph = Graph(id="data-graph", figure=fig)
    
    # Verify graph can be rendered
    rendered = graph.render()
    assert rendered.id == "data-graph"


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 