from __future__ import annotations

import uuid
from typing import Any, cast

import dash_bootstrap_components as dbc
from dash.development.base_component import Component

from core.base_component import BaseComponent
from utils.colour_palette import Theme, default_theme


class Button(BaseComponent):
    """Dark-theme wrapper around `dbc.Button`.
    
    Args:
        label: Text label displayed on the button.
        id: Component ID. Auto-generated if None.
        theme: Colour theme object. Defaults to uikitxv2.utils.default_theme.
        **dbc_kwargs: Additional keyword arguments passed to the underlying dbc.Button.
    """

    def __init__(
        self,
        label: str,
        *,
        id: str | None = None,
        theme: Theme = default_theme,
        **dbc_kwargs: Any,          # ← explicit type
    ) -> None:
        self.label = label
        self.id = id or f"btn-{uuid.uuid4().hex[:8]}"
        self.theme = theme
        self.kwargs = dbc_kwargs

    def render(self) -> Component:
        btn = dbc.Button(
            self.label,
            id=self.id,
            color="primary",
            style={
                "backgroundColor": self.theme.primary,
                "borderColor": self.theme.primary,
                "borderRadius": "4px",
                "color": self.theme.text_light,
                "fontFamily": "Inter, sans-serif",
                "fontSize": "15px",
            },
            **self.kwargs,
        )
        return cast(Component, btn)   # ← makes mypy happy
