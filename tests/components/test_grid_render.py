from components.button import Button
from components.grid import Grid


def test_grid_even_split():
    g = Grid([Button("A"), Button("B"), Button("C")]).render()
    assert [c.width for c in g.children] == [4, 4, 4]


def test_grid_custom_widths():
    g = Grid(
        [Button("Left"), Button("Right")],
        col_widths=[3, 9],
    ).render()
    assert [c.width for c in g.children] == [3, 9]
