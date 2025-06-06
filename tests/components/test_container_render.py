from components import Button
from components import Container
from components.themes import default_theme


def test_container_single_child() -> None:
    """Container renders correctly with a single child."""
    container = Container(
        id="cont-1",
        children=Button(id="btn-1", label="OK")
    ).render()

    assert len(container.children) == 1
    assert container.children[0].id == "btn-1"
    assert container.style["backgroundColor"] == default_theme.panel_bg


def test_container_multiple_children() -> None:
    """Container renders multiple children in order."""
    container = Container(
        id="cont-2",
        children=[Button(id="btn-a"), Button(id="btn-b")]
    ).render()

    assert [c.id for c in container.children] == ["btn-a", "btn-b"]
    assert container.style["padding"] == "15px"


def test_container_nested_list_children() -> None:
    """Nested lists are flattened when rendering children."""
    container = Container(
        id="cont-3",
        children=[[Button(id="btn-x"), Button(id="btn-y")], Button(id="btn-z")]
    ).render()

    assert [c.id for c in container.children] == ["btn-x", "btn-y", "btn-z"]
    assert container.style["borderRadius"] == "4px"
