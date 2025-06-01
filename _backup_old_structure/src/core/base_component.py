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
        # --- DIAGNOSTIC PRINT (Optional, can remove later) ---
        # print(f"--- BaseComponent.__init__ called for ID: {id} ---")
        # -------------------------------------------------------

        if id is None:
            # IDs are crucial for Dash, so enforce their presence.
            raise ValueError("Component ID cannot be None.")
        self.id = id
        # Assign the provided theme or use the default theme if none is given.
        self.theme = theme if theme is not None else default_theme

        # --- DIAGNOSTIC PRINT (Optional, can remove later) ---
        # print(f"--- BaseComponent.__init__ finished for ID: {id} ---")
        # -------------------------------------------------------


    @abstractmethod
    def render(self) -> Any:  # Dash Component, but keep generic to avoid heavy import
        """
        Abstract method that must be implemented by subclasses.
        Should return a Dash component (e.g., dcc.Input, dbc.Button, html.Div)
        or a dictionary representing one, ready to be included in app.layout.
        """
        pass # Subclasses must provide their rendering logic

