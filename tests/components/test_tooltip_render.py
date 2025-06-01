"""Tests for Tooltip component rendering."""

import pytest
from dash import html

from components import Tooltip
from components.themes import default_theme


def test_tooltip_render_basic():
    """Test basic rendering of Tooltip component."""
    tooltip = Tooltip(
        id="test-tooltip", 
        target="test-button",
        children="This is a helpful tooltip"
    )
    
    rendered = tooltip.render()
    
    assert rendered.id == "test-tooltip"
    assert rendered.target == "test-button"
    assert rendered.children == "This is a helpful tooltip"
    assert rendered.placement == "auto"  # default


def test_tooltip_render_with_theme():
    """Test rendering with theme applied."""
    tooltip = Tooltip(
        id="test-tooltip",
        target="test-element",
        children="Themed tooltip",
        theme=default_theme
    )
    
    rendered = tooltip.render()
    
    # Check that theme styles are applied
    assert 'backgroundColor' in rendered.style
    assert rendered.style['backgroundColor'] == default_theme.panel_bg
    assert rendered.style['color'] == default_theme.text_light


def test_tooltip_render_with_custom_style():
    """Test rendering with custom styles."""
    custom_style = {"fontSize": "16px", "fontWeight": "bold"}
    
    tooltip = Tooltip(
        id="test-tooltip",
        target="test-target",
        children="Custom styled tooltip",
        style=custom_style,
        theme=default_theme
    )
    
    rendered = tooltip.render()
    
    # Custom styles should override theme styles
    assert rendered.style['fontSize'] == "16px"
    assert rendered.style['fontWeight'] == "bold"
    # Theme styles should still be present
    assert 'backgroundColor' in rendered.style


def test_tooltip_render_with_html_content():
    """Test rendering with HTML content."""
    html_content = html.Div([
        html.Strong("Important:"),
        html.P("This is a detailed explanation.")
    ])
    
    tooltip = Tooltip(
        id="test-tooltip",
        target="help-icon",
        children=html_content,
        placement="right"
    )
    
    rendered = tooltip.render()
    
    assert rendered.children == html_content
    assert rendered.placement == "right"


def test_tooltip_render_with_delay():
    """Test rendering with delay configuration."""
    delay_config = {"show": 1000, "hide": 200}
    
    tooltip = Tooltip(
        id="test-tooltip",
        target="delayed-element",
        children="Delayed tooltip",
        delay=delay_config
    )
    
    rendered = tooltip.render()
    
    assert rendered.delay == delay_config


def test_tooltip_render_with_pattern_target():
    """Test rendering with pattern matching target."""
    pattern_target = {"type": "dynamic-button", "index": 0}
    
    tooltip = Tooltip(
        id="test-tooltip",
        target=pattern_target,
        children="Pattern matched tooltip"
    )
    
    rendered = tooltip.render()
    
    assert rendered.target == pattern_target


def test_tooltip_render_with_additional_props():
    """Test rendering with additional properties via kwargs."""
    tooltip = Tooltip(
        id="test-tooltip",
        target="test-target",
        children="Tooltip with extras",
        flip=True,
        autohide=False
    )
    
    rendered = tooltip.render()
    
    # These should be passed through to dbc.Tooltip
    assert hasattr(rendered, 'flip')
    assert hasattr(rendered, 'autohide') 