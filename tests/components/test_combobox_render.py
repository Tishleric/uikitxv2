from uikitxv2.components.combobox import ComboBox
from uikitxv2.utils.colour_palette import default_theme


def test_combobox_render():
    cb = ComboBox(["A", "B", "C"]).render()

    assert cb.id.startswith("combo-")
    assert cb.options[0]["label"] == "A"
    assert cb.multi is False

    style = cb.style
    assert style["backgroundColor"] == default_theme.panel_bg
    assert style["color"] == default_theme.text_light
