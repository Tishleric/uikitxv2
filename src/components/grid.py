from __future__ import annotations

import math
import uuid
from typing import Any, List, Sequence, cast

import dash_bootstrap_components as dbc
from dash.development.base_component import Component

from core.base_component import BaseComponent
from utils.colour_palette import Theme, default_theme


class Grid(BaseComponent):
    """Bootstrap grid wrapper for component layout.
    
    Args:
        children: Sequence of child components to arrange in the grid.
        col_widths: Optional sequence of column widths for each child. Must sum to cols value.
            If not provided, children share space equally.
        cols: Total number of grid columns. Must be between 1 and 12. Defaults to 12.
        gap: Gap size between columns. Defaults to 2.
        id: Component ID. Auto-generated if None.
        theme: Colour theme object. Defaults to uikitxv2.utils.default_theme.
        **row_kwargs: Additional keyword arguments passed to the underlying dbc.Row.
    """

    def __init__(
        self,
        children: Sequence[BaseComponent],
        *,
        col_widths: Sequence[int] | None = None,   # NEW
        cols: int = 12,
        gap: int = 2,
        id: str | None = None,
        theme: Theme = default_theme,
        **row_kwargs: Any,
    ) -> None:
        if not children:
            raise ValueError("Grid requires at least one child component.")
        if not (1 <= cols <= 12):
            raise ValueError("cols must be between 1 and 12.")
        if col_widths is not None:
            if len(col_widths) != len(children):
                raise ValueError("col_widths length must match children length.")
            if sum(col_widths) != cols:
                raise ValueError("sum(col_widths) must equal cols.")
            if any(w < 1 or w > cols for w in col_widths):
                raise ValueError("each width must be in 1..cols")
            self._widths: List[int] = list(col_widths)
        else:
            n = len(children)
            even = max(1, math.floor(cols / n))
            self._widths = [even] * n

        self.children = list(children)
        self.cols = cols
        self.gap = gap
        self.id = id or f"grid-{uuid.uuid4().hex[:8]}"
        self.theme = theme
        self.kwargs = row_kwargs

    # -------------------------------------------------------------- #
    def _build_cols(self) -> list[dbc.Col]:  
        return [
            dbc.Col(child.render(), width=w)
            for child, w in zip(self.children, self._widths, strict=True)
        ]

    def render(self) -> Component:
        row = dbc.Row(
            self._build_cols(),
            id=self.id,
            className=f"g-{self.gap}",
            style={"backgroundColor": self.theme.panel_bg},
            **self.kwargs,
        )
        return cast(Component, row)
