from __future__ import annotations

import uuid
from typing import Any, Mapping, Sequence, TypedDict, Union, cast

import dash_bootstrap_components as dbc
from dash.development.base_component import Component

from uikitxv2.core.base_component import BaseComponent
from uikitxv2.utils.colour_palette import Theme, default_theme


class _Option(TypedDict):
    label: str
    value: str


class RadioButton(BaseComponent):
    """Dark-theme wrapper around `dbc.RadioItems`."""

    def __init__(
        self,
        options: Sequence[Union[str, Mapping[str, str]]],
        *,
        value: str | None = None,
        inline: bool = True,
        id: str | None = None,
        theme: Theme = default_theme,
        **radio_kwargs: Any,
    ) -> None:
        if not options:
            raise ValueError("RadioButton requires a non-empty options list.")

        norm: list[_Option] = []
        for o in options:
            if isinstance(o, str):
                norm.append({"label": o, "value": o})
            else:
                if "label" not in o or "value" not in o:
                    raise KeyError("Each option dict needs 'label' and 'value'.")
                norm.append({"label": o["label"], "value": o["value"]})
        self._options = norm

        self.value = value
        self.inline = inline
        self.id = id or f"radio-{uuid.uuid4().hex[:8]}"
        self.theme = theme
        self.kwargs = radio_kwargs

    # -------------------------------------------------------------- #
    def render(self) -> Component:
        style: dict[str, str] = {
            "color": self.theme.text_light,
        }
        radios = dbc.RadioItems(
            id=self.id,
            options=self._options,
            value=self.value,
            inline=self.inline,
            input_checked_style={"backgroundColor": self.theme.primary},
            label_checked_style={"color": self.theme.primary},
            style=style,
            **self.kwargs,
        )
        return cast(Component, radios)
