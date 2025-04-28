from __future__ import annotations

import uuid
from typing import Any, List, Sequence, Tuple, cast

import dash_bootstrap_components as dbc
from dash.development.base_component import Component

from uikitxv2.core.base_component import BaseComponent
from uikitxv2.utils.colour_palette import Theme, default_theme


class Tabs(BaseComponent):
    """Dark-theme wrapper around `dbc.Tabs` and `dbc.Tab`."""

    def __init__(
        self,
        tabs: Sequence[Tuple[str, BaseComponent]],  # (label, wrapped component)
        *,
        active_tab_index: int = 0,
        id: str | None = None,
        theme: Theme = default_theme,
        **dbc_kwargs: Any,
    ) -> None:
        if not tabs:
            raise ValueError("Tabs wrapper requires at least one tab.")
        if not (0 <= active_tab_index < len(tabs)):
            raise IndexError("active_tab_index out of range.")

        self.tabs = list(tabs)
        self.active_tab_index = active_tab_index
        self.id = id or f"tabs-{uuid.uuid4().hex[:8]}"
        self.theme = theme
        self.kwargs = dbc_kwargs

    # --------------------------------------------------------------------- #
    # Helpers
    # --------------------------------------------------------------------- #
    def _build_tab_children(self) -> List[dbc.Tab]:  
        children: list[dbc.Tab] = []
        for idx, (label, wrapped) in enumerate(self.tabs):
            tab_id = f"{self.id}-tab-{idx}"
            children.append(
                dbc.Tab(
                    wrapped.render(),          # children (positional)
                    label=label,               # tab label
                    id=tab_id,
                    tab_id=tab_id,
                    tab_style={
                        "backgroundColor": self.theme.panel_bg,
                        "color": self.theme.text_subtle,
                    },
                    active_tab_style={
                        "backgroundColor": self.theme.panel_bg,
                        "color": self.theme.primary,
                    },
                )
            )
        return children

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    def render(self) -> Component:
        child_tabs = self._build_tab_children()
        tabs = dbc.Tabs(                     # removed card=True
            child_tabs,
            id=self.id,
            active_tab=child_tabs[self.active_tab_index].id,
            className="card-header-tabs",    # opt-in header style (optional)
            **self.kwargs,
        )
        return cast(Component, tabs)