from uikitxv2.components.button import Button
from uikitxv2.utils.colour_palette import default_theme


def test_button_render():
    btn = Button("Refresh").render()

    # minimal snapshot: children, id, bootstrap colour & inline style keys
    assert btn.children == "Refresh"
    assert btn.id.startswith("btn-")
    assert btn.color == "primary"

    style = btn.style
    assert style["backgroundColor"] == default_theme.primary
    assert style["color"] == default_theme.text_light
