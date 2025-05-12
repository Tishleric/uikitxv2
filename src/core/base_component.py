# uikitxv2/src/core/base_component.py

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

# Import default_theme to use as a fallback
# Use relative import from core to utils
from ..utils.colour_palette import default_theme

class BaseComponent(ABC):
    """
    Abstract base class for all wrapped UI controls.
    Ensures components have an ID and a theme.
    """

    def __init__(self, id: str, theme: Any = None):
        """
        Initializes the base component.

        Args:
            id (str): The component's ID, required for Dash callbacks.
            theme (Any, optional): A theme object (like the one from colour_palette).
                                   Defaults to default_theme if None.
        """
        if id is None:
            raise ValueError("Component ID cannot be None.")
        self.id = id
        self.theme = theme if theme is not None else default_theme

    @abstractmethod
    def render(self) -> Any:
        """
        Abstract method that must be implemented by subclasses.
        Should return a Dash component (e.g., dcc.Input, dbc.Button, html.Div)
        or a dictionary representing one, ready to be included in app.layout.
        """
        pass

