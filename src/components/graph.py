from __future__ import annotations

import uuid
from typing import Any, Dict, Union, cast

import dash.dcc as dcc
import plotly.graph_objects as go  # plotly ships no type stubs
from dash.development.base_component import Component

from core.base_component import BaseComponent
from utils.colour_palette import Theme, default_theme

FigureLike = Union[go.Figure, Dict[str, Any]]


class Graph(BaseComponent):
    """Dark-theme wrapper around `dcc.Graph` with plotly figure integration.
    
    Args:
        figure: Plotly Figure object or figure dict to display.
        responsive: Whether the graph should resize with its container. Defaults to True.
        config: Optional plotly configuration dict. Defaults to None.
        height_px: Fixed height in pixels. If None, height is determined by container. Defaults to None.
        id: Component ID. Auto-generated if None.
        theme: Colour theme object. Defaults to uikitxv2.utils.default_theme.
        **graph_kwargs: Additional keyword arguments passed to the underlying dcc.Graph.
    """

    def __init__(
        self,
        figure: FigureLike,
        *,
        responsive: bool = True,
        config: Dict[str, Any] | None = None,
        height_px: int | None = None,
        id: str | None = None,
        theme: Theme = default_theme,
        **graph_kwargs: Any,
    ) -> None:
        self.figure = figure
        self.responsive = responsive
        self.config: Dict[str, Any] = config or {}
        self.height_px = height_px
        self.id = id or f"graph-{uuid.uuid4().hex[:8]}"
        self.theme = theme
        self.kwargs = graph_kwargs

        # Apply dark layout defaults
        if isinstance(self.figure, dict):
            layout = self.figure.setdefault("layout", {})
            layout.setdefault("paper_bgcolor", self.theme.panel_bg)
            layout.setdefault("plot_bgcolor", self.theme.panel_bg)
            layout.setdefault("font", {}).setdefault("color", self.theme.text_light)
        elif isinstance(self.figure, go.Figure):
            self.figure.update_layout(
                paper_bgcolor=self.theme.panel_bg,
                plot_bgcolor=self.theme.panel_bg,
                font=dict(color=self.theme.text_light),
            )
        else:
            raise TypeError("figure must be a Plotly Figure or a figure dict")

    # ------------------------------------------------------------------ #
    def render(self) -> Component:
        cfg: Dict[str, Any] = {**self.config}
        if self.responsive:
            cfg.setdefault("responsive", True)

        style = {"height": f"{self.height_px}px"} if self.height_px else {}

        graph = dcc.Graph(
            id=self.id,
            figure=self.figure,
            config=cast(Any, cfg),
            style=style,
            **self.kwargs,
        )
        return cast(Component, graph)
