"""UIKitX v2 – Basic Usage
=========================

Run this file with

    python examples/basic_usage.py

and open the printed http URL to see every wrapper rendered in a dark‑themed
Bootstrap grid.
"""

from __future__ import annotations

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

from uikitxv2.components import Button, ComboBox, Graph, Grid, ListBox, RadioButton, Tabs

# ---------------------------------------------------------------------------
# 1 • Instantiate each wrapper component
# ---------------------------------------------------------------------------

confirm_btn = Button("Submit")

city_dd = ComboBox(["New York", "London", "Tokyo"], placeholder="Choose a city")

colour_radio = RadioButton(["Red", "Green", "Blue"], value="Red")

flavours_box = ListBox(["Vanilla", "Chocolate", "Pistachio"], values=["Chocolate"])

sample_fig = go.Figure(data=[go.Bar(x=["A", "B", "C"], y=[3, 1, 2])])
chart_main = Graph(sample_fig)
chart_tab = Graph(sample_fig)

info_tabs = Tabs([
    ("Home", Button("Welcome!")),
    ("Chart", chart_tab),
])

# ---------------------------------------------------------------------------
# 2 • Arrange them in a responsive Grid
# ---------------------------------------------------------------------------

layout_grid = Grid([
    confirm_btn,
    city_dd,
    colour_radio,
    flavours_box,
    chart_main,
    info_tabs,
])

# ---------------------------------------------------------------------------
# 3 • Build and run the Dash app
# ---------------------------------------------------------------------------

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = layout_grid.render()

if __name__ == "__main__":
    app.run(debug=True)
