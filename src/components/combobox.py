from __future__ import annotations

import uuid
from typing import Any, Mapping, Sequence, TypedDict, Union, cast

import dash.dcc as dcc
from dash.development.base_component import Component

from core.base_component import BaseComponent
from utils.colour_palette import Theme, default_theme


class _Option(TypedDict):
    """Shape Dash expects for each dropdown option."""
    label: str
    value: str


class ComboBox(BaseComponent):
    """Dark-theme wrapper around `dcc.Dropdown` (single- or multi-select)."""

    def __init__(
        self,
        options: Sequence[Union[str, Mapping[str, str]]],
        *,
        value: Union[str, list[str], None] = None,
        multi: bool = False,
        clearable: bool = True,
        placeholder: str | None = None,
        id: str | None = None,
        theme: Theme = default_theme,
        **dropdown_kwargs: Any,
    ) -> None:
        if not options:
            raise ValueError("ComboBox requires a non-empty options list.")

        # Normalise options → list[_Option]; validate mapping inputs.
        norm: list[_Option] = []
        for o in options:
            if isinstance(o, str):
                norm.append({"label": o, "value": o})
            else:
                if "label" not in o or "value" not in o:
                    raise KeyError(
                        "ComboBox option dicts need both 'label' and 'value'."
                    )
                norm.append({"label": o["label"], "value": o["value"]})
        self._options = norm

        self.value = value
        self.multi = multi
        self.clearable = clearable
        self.placeholder = placeholder
        self.id = id or f"combo-{uuid.uuid4().hex[:8]}"
        self.theme = theme
        self.kwargs = dropdown_kwargs

    # ------------------------------------------------------------------ #
    def render(self) -> Component:
        style: dict[str, str] = {
            "backgroundColor": self.theme.panel_bg,
            "color": self.theme.text_light,
            "borderRadius": "4px",
        }

        dd = dcc.Dropdown(
            id=self.id,
            options=cast(Any, self._options),  # silence Dash's outdated stub
            value=self.value,
            multi=self.multi,
            clearable=self.clearable,
            placeholder=self.placeholder,
            style=style,
            **self.kwargs,
        )
        return cast(Component, dd)
