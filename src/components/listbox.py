from __future__ import annotations

import uuid
from typing import Any, Mapping, Sequence, TypedDict, Union, cast

import dash.dcc as dcc
from dash.development.base_component import Component

from core.base_component import BaseComponent
from utils.colour_palette import Theme, default_theme


class _Option(TypedDict):
    label: str
    value: str


class ListBox(BaseComponent):
    """Dark-theme multi-select list box built on `dcc.Checklist`.
    
    Args:
        options: Sequence of option strings or dicts with 'label' and 'value' keys.
        values: List of initially selected values. Defaults to None.
        height_px: Height of the listbox in pixels. Defaults to 160.
        id: Component ID. Auto-generated if None.
        theme: Colour theme object. Defaults to uikitxv2.utils.default_theme.
        **check_kwargs: Additional keyword arguments passed to the underlying dcc.Checklist.
    """

    def __init__(
        self,
        options: Sequence[Union[str, Mapping[str, str]]],
        *,
        values: list[str] | None = None,
        height_px: int = 160,
        id: str | None = None,
        theme: Theme = default_theme,
        **check_kwargs: Any,
    ) -> None:
        if not options:
            raise ValueError("ListBox requires a non-empty options list.")

        norm: list[_Option] = []
        for o in options:
            if isinstance(o, str):
                norm.append({"label": o, "value": o})
            else:
                if "label" not in o or "value" not in o:
                    raise KeyError("Option dicts need both 'label' and 'value'.")
                norm.append({"label": o["label"], "value": o["value"]})
        self._options = norm

        self.values = values
        self.height_px = height_px
        self.id = id or f"listbox-{uuid.uuid4().hex[:8]}"
        self.theme = theme
        self.kwargs = check_kwargs

    # ------------------------------------------------------------------ #
    def render(self) -> Component:
        style: dict[str, str | int] = {
            "backgroundColor": self.theme.panel_bg,
            "color": self.theme.text_light,
            "borderRadius": "4px",
            "overflowY": "auto",
            "height": f"{self.height_px}px",
            "padding": "4px",
        }

        checklist = dcc.Checklist(
            id=self.id,
            options=cast(Any, self._options),  
            value=self.values,
            style=style,
            inputStyle={"marginRight": "6px"},
            labelStyle={"display": "block", "cursor": "pointer"},
            **self.kwargs,
        )
        return cast(Component, checklist)
