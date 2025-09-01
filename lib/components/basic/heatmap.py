"""
Heatmap component wrapper rendering a Plotly heatmap/imshow figure within a
Dash Graph, following the same pattern as other wrapped components.
"""

from typing import Any, Optional, Dict

from dash import dcc

from ..core import BaseComponent


class Heatmap(BaseComponent):
    """Thin wrapper around dcc.Graph to display a heatmap figure.

    Usage mirrors other wrappers: construct, then call render().
    """

    def __init__(
        self,
        id: str,
        figure: Optional[Any] = None,
        style: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
        theme: Optional[Any] = None,
    ) -> None:
        super().__init__(id=id, theme=theme)
        self.figure = figure
        self.style = style or {}
        self.config = config or {}

    def render(self) -> dcc.Graph:
        return dcc.Graph(id=self.id, figure=self.figure, style=self.style, config=self.config)


