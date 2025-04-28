from uikitxv2.components.button import Button
from uikitxv2.components.grid import Grid


def test_grid_render():
    g = Grid([Button("A"), Button("B"), Button("C")]).render()

    assert g.id.startswith("grid-")
    assert len(g.children) == 3

    # Each child is a dbc.Col and has width 4 for 12-column grid with 3 items.
    widths = [col.width for col in g.children]
    assert all(w == 4 for w in widths)
