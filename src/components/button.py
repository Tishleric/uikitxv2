from __future__ import annotations

import uuid
from typing import Any, cast

import dash_bootstrap_components as dbc
from dash.development.base_component import Component

from core.base_component import BaseComponent
from utils.colour_palette import Theme, default_theme


class Button(BaseComponent):
    """One-liner dark-theme wrapper around `dbc.Button`."""

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
