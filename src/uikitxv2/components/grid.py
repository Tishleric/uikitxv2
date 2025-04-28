from __future__ import annotations

import math
import uuid
from typing import Any, Sequence, cast

import dash_bootstrap_components as dbc
from dash.development.base_component import Component

from uikitxv2.core.base_component import BaseComponent
from uikitxv2.utils.colour_palette import Theme, default_theme


class Grid(BaseComponent):
    """Even-split Bootstrap grid for a sequence of wrapped components."""

    def __init__(
        self,
        children: Sequence[BaseComponent],
        *,
        cols: int = 12,
        gap: int = 2,  # Bootstrap gutter scale 0-5
        id: str | None = None,
        theme: Theme = default_theme,
        **row_kwargs: Any,
    ) -> None:
        if not children:
            raise ValueError("Grid requires at least one child component.")
        if not (1 <= cols <= 12):
            raise ValueError("cols must be between 1 and 12.")

        self.children = list(children)
        self.cols = cols
        self.gap = gap
        self.id = id or f"grid-{uuid.uuid4().hex[:8]}"
        self.theme = theme
        self.kwargs = row_kwargs

    # -------------------------------------------------------------- #
    def _build_cols(self) -> list[dbc.Col]: 
        n = len(self.children)
        min_width = math.floor(self.cols / n) or 1
        cols: list[dbc.Col] = []
        for wrapped in self.children:
            cols.append(
                dbc.Col(
                    wrapped.render(),
                    width=min_width,
                )
            )
        return cols

    def render(self) -> Component:
        row = dbc.Row(
            self._build_cols(),
            id=self.id,
            className=f"g-{self.gap}",
            style={"backgroundColor": self.theme.panel_bg},
            **self.kwargs,
        )
        return cast(Component, row)
