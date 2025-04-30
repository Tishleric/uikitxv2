from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseComponent(ABC):
    """All wrapped UI controls inherit from this."""

    @abstractmethod
    def render(self) -> Any:  # Dash Component, but keep generic to avoid heavy import
        """Return a Dash element ready for `app.layout`."""
