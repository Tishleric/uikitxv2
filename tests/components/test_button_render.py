from components import Button
from components.themes import default_theme


def test_button_render() -> None:
    """Render a Button and verify default properties."""
    btn = Button("Refresh").render()

    # minimal snapshot: children, id, bootstrap colour & inline style keys
    assert btn.children == "Refresh"
    assert btn.id.startswith("btn-")
    assert btn.color == "primary"

    style = btn.style
    assert style["backgroundColor"] == default_theme.primary
    assert style["color"] == default_theme.text_light
