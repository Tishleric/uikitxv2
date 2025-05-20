import pytest

from core.base_component import BaseComponent
from utils.colour_palette import default_theme


class DummyComponent(BaseComponent):  # type: ignore[misc]
    """Minimal subclass for testing BaseComponent."""

    def render(self) -> dict[str, object]:
        return {"id": self.id, "theme": self.theme}


def test_base_component_requires_id() -> None:
    """BaseComponent must raise when id is missing."""
    with pytest.raises(ValueError):
        DummyComponent(id=None)


def test_base_component_default_theme() -> None:
    """Components default to the global theme."""
    comp = DummyComponent("dummy")
    assert comp.theme is default_theme

