from __future__ import annotations

from dataclasses import dataclass

__all__ = ["Theme", "default_theme"]


@dataclass(frozen=True, slots=True)
class Theme:
    base_bg: str
    panel_bg: str
    primary: str
    secondary: str
    accent: str
    text_light: str
    text_subtle: str
    danger: str
    success: str


# “Black Cat Dark” palette
default_theme = Theme(
    base_bg="#000000",
    panel_bg="#121212",
    primary="#18F0C3",
    secondary="#8F8F8F",
    accent="#F01899",
    text_light="#E5E5E5",
    text_subtle="#9A9A9A",
    danger="#FF5555",
    success="#4CE675",
)
