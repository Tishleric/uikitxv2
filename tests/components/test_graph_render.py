from components.graph import Graph
from utils.colour_palette import default_theme


def test_graph_render():
    g = Graph({}).render()  # empty figure dict

    assert g.id.startswith("graph-")
    assert g.figure["layout"]["paper_bgcolor"] == default_theme.panel_bg
    assert g.config["responsive"] is True
