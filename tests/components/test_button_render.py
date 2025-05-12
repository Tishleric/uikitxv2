"""
Tests for the Button component rendering.
"""
from components.button import Button
from utils.colour_palette import default_theme


def test_button_render():
    """
    Test that the Button component renders correctly with proper styling.
    
    Validates:
        - Button text content
        - ID format
        - Button color matches theme
        - Inline styles match theme colors
    """
    btn = Button("Refresh").render()

    # minimal snapshot: children, id, bootstrap colour & inline style keys
    assert btn.children == "Refresh"
    assert btn.id.startswith("btn-")
    assert btn.color == "primary"

    style = btn.style
    assert style["backgroundColor"] == default_theme.primary
    assert style["color"] == default_theme.text_light
