# tests/components/test_tabs_render.py

from components import Button
from components import Tabs
from components.themes import default_theme


def test_tabs_render() -> None:
    """Render Tabs component and verify active tab styling."""
    tab_a = Button("A")
    tab_b = Button("B")
    tabs_wrapper = Tabs([("First", tab_a), ("Second", tab_b)], active_tab_index=1)
    tabs_component = tabs_wrapper.render() # Get the rendered dbc.Tabs

    # Core snapshot checks
    assert len(tabs_component.children) == 2
    # Ensure the active_tab uses the generated tab_id
    expected_active_tab_id = f"{tabs_wrapper.id}-tab-1"
    assert tabs_component.active_tab == expected_active_tab_id

    # Get the individual dbc.Tab components
    inactive_tab = tabs_component.children[0]
    active_tab = tabs_component.children[1]

    # --- Corrected Assertions ---
    # Check the *label* styles for color
    assert inactive_tab.label_style["color"] == default_theme.text_light
    assert active_tab.active_label_style["color"] == default_theme.primary

    # Optional: Check other styles if needed
    assert inactive_tab.tab_style["backgroundColor"] == default_theme.panel_bg
    assert active_tab.active_tab_style["backgroundColor"] == default_theme.panel_bg
    assert active_tab.active_tab_style["fontWeight"] == "bold"

