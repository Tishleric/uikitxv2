from components.listbox import ListBox
from utils.colour_palette import default_theme


def test_listbox_render():
    lb = ListBox(["One", "Two", "Three"], values=["Two"]).render()

    assert lb.id.startswith("listbox-")
    assert lb.value == ["Two"]

    style = lb.style
    assert style["backgroundColor"] == default_theme.panel_bg
    assert style["overflowY"] == "auto"
