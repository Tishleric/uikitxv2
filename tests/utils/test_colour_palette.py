from dataclasses import FrozenInstanceError

import pytest

from components.themes import (
    default_theme,
    get_button_default_style,
    get_combobox_default_style,
    get_container_default_style,
    get_datatable_default_styles,
    get_graph_figure_layout_defaults,
    get_graph_wrapper_default_style,
    get_grid_default_style,
    get_listbox_default_styles,
    get_mermaid_default_styles,
    get_radiobutton_default_styles,
    get_tabs_default_styles,
)


def test_default_theme_values() -> None:
    """Ensure default theme constants are as expected."""
    assert default_theme.base_bg == "#000000"
    assert default_theme.panel_bg == "#121212"
    assert default_theme.primary == "#18F0C3"
    assert default_theme.secondary == "#8F8F8F"
    assert default_theme.accent == "#F01899"
    assert default_theme.text_light == "#E5E5E5"
    assert default_theme.text_subtle == "#9A9A9A"
    assert default_theme.danger == "#FF5555"
    assert default_theme.success == "#4CE675"


def test_theme_is_frozen() -> None:
    """Default theme dataclass should be immutable."""
    with pytest.raises(FrozenInstanceError):
        default_theme.base_bg = "#FFF"


def test_get_combobox_default_style() -> None:
    """ComboBox default style matches theme colors."""
    style = get_combobox_default_style(default_theme)
    assert style["backgroundColor"] == default_theme.panel_bg
    assert style["color"] == default_theme.text_light


def test_get_button_default_style() -> None:
    """Button style uses primary color and light text."""
    style = get_button_default_style(default_theme)
    assert style["backgroundColor"] == default_theme.primary
    assert style["color"] == default_theme.text_light


def test_get_container_default_style() -> None:
    """Container defaults include panel background and border radius."""
    style = get_container_default_style(default_theme)
    assert style["backgroundColor"] == default_theme.panel_bg
    assert "borderRadius" in style


def test_get_datatable_default_styles() -> None:
    """DataTable styles derive from the theme palette."""
    styles = get_datatable_default_styles(default_theme)
    assert styles["style_header"]["backgroundColor"] == default_theme.panel_bg
    assert styles["style_cell"]["backgroundColor"] == default_theme.base_bg


def test_get_graph_figure_layout_defaults() -> None:
    """Graph figure layout uses theme colors."""
    layout = get_graph_figure_layout_defaults(default_theme)
    assert layout["plot_bgcolor"] == default_theme.base_bg
    assert layout["paper_bgcolor"] == default_theme.panel_bg


def test_get_graph_wrapper_default_style() -> None:
    """Graph wrapper returns empty style by default."""
    assert get_graph_wrapper_default_style(default_theme) == {}


def test_get_grid_default_style() -> None:
    """Grid default style uses panel background."""
    style = get_grid_default_style(default_theme)
    assert style["backgroundColor"] == default_theme.panel_bg


def test_get_listbox_default_styles() -> None:
    """ListBox styles include scroll area and colors."""
    styles = get_listbox_default_styles(default_theme, height_px=100)
    assert styles["style"]["backgroundColor"] == default_theme.panel_bg


def test_get_radiobutton_default_styles() -> None:
    """RadioButton styles honor theme and checked color."""
    styles = get_radiobutton_default_styles(default_theme)
    assert styles["style"]["color"] == default_theme.text_light
    assert styles["input_checked_style"]["backgroundColor"] == default_theme.primary


def test_get_tabs_default_styles() -> None:
    """Tabs style uses theme colors for active and inactive labels."""
    styles = get_tabs_default_styles(default_theme)
    assert styles["main_tabs_style"]["borderBottom"].endswith(default_theme.primary)
    assert styles["label_style"]["color"] == default_theme.text_subtle


def test_get_mermaid_default_styles() -> None:
    """Mermaid styling merges theme variables."""
    styles = get_mermaid_default_styles(default_theme)
    assert styles["style"]["backgroundColor"] == default_theme.panel_bg
    assert styles["mermaid_config"]["themeVariables"]["primaryColor"] == default_theme.primary
