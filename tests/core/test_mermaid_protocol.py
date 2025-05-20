from core.mermaid_protocol import MermaidProtocol


class DummyMermaid(MermaidProtocol):  # type: ignore[misc]
    """Minimal concrete implementation for testing."""

    def render(self, id: str, graph_definition: str, **kwargs) -> dict[str, object]:
        return {"id": id, "graph": graph_definition, "kwargs": kwargs}

    def apply_theme(self, theme_config: dict[str, object]) -> dict[str, object]:
        return {"applied": theme_config}


def test_dummy_mermaid_render() -> None:
    """DummyMermaid.render returns expected structure."""
    dummy = DummyMermaid()
    result = dummy.render("d1", "graph TD; A-->B", extra=1)
    assert result == {"id": "d1", "graph": "graph TD; A-->B", "kwargs": {"extra": 1}}


def test_dummy_mermaid_apply_theme() -> None:
    """DummyMermaid.apply_theme echoes configuration."""
    dummy = DummyMermaid()
    config = {"theme": "dark"}
    assert dummy.apply_theme(config) == {"applied": config}
