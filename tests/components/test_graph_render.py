from components import Graph
from components.themes import default_theme


def test_graph_render() -> None:
    """Render Graph component with default settings."""
    g = Graph({}).render()  # empty figure dict

    assert g.id.startswith("graph-")
    assert g.figure["layout"]["paper_bgcolor"] == default_theme.panel_bg
    assert g.config["responsive"] is True
