from uikitxv2.components.button import Button
from uikitxv2.components.tabs import Tabs
from uikitxv2.utils.colour_palette import default_theme


def test_tabs_render():
    tab_a = Button("A")
    tab_b = Button("B")
    tabs = Tabs([("First", tab_a), ("Second", tab_b)], active_tab_index=1).render()

    # Core snapshot checks
    assert len(tabs.children) == 2
    assert tabs.active_tab == f"{tabs.id}-tab-1"

    inactive_style = tabs.children[0].tab_style
    active_style = tabs.children[1].active_tab_style
    assert inactive_style["color"] == default_theme.text_subtle
    assert active_style["color"] == default_theme.primary
