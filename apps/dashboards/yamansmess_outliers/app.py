from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Mapping, Tuple, cast

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import plotly.express as px  # type: ignore[import-untyped]
import plotly.graph_objects as go  # type: ignore[import-untyped]
from dash import Dash, dcc, html
from dash.dependencies import Input, Output


DATA_PATH = (
    Path(__file__).resolve().parents[3]
    / "lib"
    / "trading"
    / "bond_future_options"
    / "data_validation"
    / "yamansmess"
    / "yamansmess_outliers_aggregated.csv"
)


def _load_data(csv_path: Path) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """Load CSV and return (dataframe, resolved_column_map).

    Column names are normalized to lowercase for access. Required columns are
    validated and coerced to numeric. Adds an "abs_error" column.
    """
    df = pd.read_csv(csv_path)
    # Normalize column names to lowercase for robust access
    df.columns = [c.strip().lower() for c in df.columns]

    # Map expected fields (allowing possible variations)
    required_map: Dict[str, List[str]] = {
        "error": ["error"],
        "del_f": ["del_f"],
        "del_c": ["del_c"],
        "del_t": ["del_t"],
        "del_iv": ["del_iv"],
        "vtexp": ["vtexp"],
        "moneyness": ["moneyness"],
    }

    resolved: Dict[str, str] = {}
    for key, candidates in required_map.items():
        found = None
        for cand in candidates:
            if cand in df.columns:
                found = cand
                break
        if not found:
            raise KeyError(f"Required column not found for {key}: tried {candidates}")
        resolved[key] = found

    # Coerce to numeric and build abs_error
    for col in resolved.values():
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=[resolved["error"]]).copy()
    df["abs_error"] = df[resolved["error"]].abs()
    return df, resolved


def _quantile_curve(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    *,
    bins: int = 40,
    q: float = 0.95,
) -> pd.DataFrame:
    """Compute a binned quantile curve for overlay.

    Returns a DataFrame with columns `x` (bin centers) and `y` (quantile).
    """
    xs_raw = pd.to_numeric(df[x_col], errors="coerce")
    ys_raw = pd.to_numeric(df[y_col], errors="coerce")
    mask = np.isfinite(xs_raw.to_numpy()) & np.isfinite(ys_raw.to_numpy())
    xs = xs_raw[mask]
    ys = ys_raw[mask]
    if xs.empty or ys.empty:
        return pd.DataFrame({"x": [], "y": []})
    xmin, xmax = float(xs.min()), float(xs.max())
    if not np.isfinite(xmin) or not np.isfinite(xmax) or xmin == xmax:
        return pd.DataFrame({"x": [], "y": []})

    edges = np.linspace(xmin, xmax, bins + 1)
    cuts = pd.cut(xs, edges, include_lowest=True)
    grouped = pd.DataFrame({"bin": cuts, "y": ys}).groupby("bin", observed=True)
    yq = grouped.quantile(q)["y"].dropna()
    centers: List[float] = []
    for inter in yq.index.categories:
        centers.append(float((inter.left + inter.right) / 2))
    # Align lengths in case of empty bins
    return pd.DataFrame({"x": centers[: len(yq)], "y": yq.to_numpy()})


def _build_figure(
    df: pd.DataFrame,
    feature_col: str,
    *,
    orientation: str = "feature",
    log_y: bool = False,
    clip_p99: bool = True,
    threshold: float | None = None,
    title: str,
) -> go.Figure:
    data = df
    if clip_p99:
        abs_arr = df["abs_error"].to_numpy(dtype=float, copy=False)
        finite_mask = np.isfinite(abs_arr)
        if finite_mask.sum() >= 5:
            cap = float(np.nanquantile(abs_arr[finite_mask], 0.99))
            data = df[df["abs_error"] <= cap]
        else:
            data = df

    # Color points above threshold (if any)
    if threshold is not None:
        mask = data["abs_error"] >= threshold
        data = data.assign(above=mask)
        color = "above"
        color_map = {False: "#4c78a8", True: "#e45756"}
    else:
        color = None
        color_map = None

    if orientation == "feature":
        x, y = feature_col, "abs_error"
    else:
        x, y = "abs_error", feature_col

    fig = px.scatter(
        data,
        x=x,
        y=y,
        color=color,
        color_discrete_map=cast(Dict[Any, str], color_map) if color_map is not None else None,
        opacity=0.5,
        render_mode="webgl",
        height=350,
    )

    # Overlay q95 curve when abs_error is on Y (orientation="feature")
    if orientation == "feature":
        curve = _quantile_curve(data, feature_col, "abs_error", bins=40, q=0.95)
        if not curve.empty:
            fig.add_scatter(x=curve["x"], y=curve["y"], mode="lines", name="q95")

    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), title=title)
    if log_y and orientation == "feature":
        fig.update_yaxes(type="log")
    return fig


def create_app() -> Dash:
    """Build and return the Dash application instance."""
    df, cols = _load_data(DATA_PATH)

    # Controls
    abs_vals = pd.to_numeric(df["abs_error"], errors="coerce").to_numpy(dtype=float, copy=False)
    finite_abs = abs_vals[np.isfinite(abs_vals)]
    if finite_abs.size == 0:
        thr_max = 1.0
        thr_marks = {0.0: "0", 1.0: "1"}
    else:
        thr_max = float(np.quantile(finite_abs, 0.99))
        if not np.isfinite(thr_max) or thr_max <= 0:
            thr_max = float(np.max(finite_abs)) if np.max(finite_abs) > 0 else 1.0
        marks_vals = np.linspace(0.0, thr_max, 5)
        thr_marks = {float(v): f"{v:.0f}" for v in marks_vals}
    controls = html.Div(
        [
            html.Label("Y-axis scale (when feature on X):"),
            dcc.Checklist(id="log-y", options=("log",), value=[], inline=True),
            dcc.Checklist(id="clip-p99", options=("clip",), value=["clip"], inline=True),
            html.Label("Orientation:"),
            dcc.RadioItems(id="orientation", options=("feature", "error"), value="feature", inline=True),
            html.Label("Highlight |error| ≥ threshold:"),
            dcc.Slider(
                id="threshold",
                min=0,
                max=thr_max,
                step=None,
                value=0,
                updatemode="drag",
                tooltip={"always_visible": True, "placement": "bottom"},
                marks=cast(Any, thr_marks),
            ),
        ],
        style={"marginBottom": "10px"},
    )

    graph_defs = [
        ("g_del_f", cols["del_f"], "del_f vs |error|"),
        ("g_del_c", cols["del_c"], "del_c vs |error|"),
        ("g_del_t", cols["del_t"], "del_t vs |error|"),
        ("g_del_iv", cols["del_iv"], "del_iv vs |error|"),
        ("g_vtexp", cols["vtexp"], "vtexp vs |error|"),
        ("g_mny", cols["moneyness"], "moneyness vs |error|"),
    ]
    graphs = [
        html.Div(dcc.Graph(id=i, figure=_build_figure(df, c, title=t)), style={"width": "50%"})
        for i, c, t in graph_defs
    ]

    app = Dash(__name__)
    rows = []
    for i in range(0, len(graphs), 2):
        rows.append(html.Div(graphs[i : i + 2], style={"display": "flex", "gap": "10px", "marginBottom": "10px"}))

    # Short descriptions
    desc = html.Ul(
        [
            html.Li("del_f: sensitivity of price error to underlying future price (∆F)."),
            html.Li("del_c: sensitivity of price error to call option delta (∆C)."),
            html.Li("del_t: sensitivity of price error to time to expiry (∆T)."),
            html.Li("del_iv: sensitivity of price error to implied volatility (∆IV)."),
            html.Li("vtexp: time to expiry in years used in pricing."),
            html.Li("moneyness: standardized distance of strike from underlying price."),
        ],
        style={"marginBottom": "10px", "color": "#444"},
    )

    app.layout = html.Div(
        [html.H2("Yamansmess Outliers – Error Diagnostics"), desc, controls, html.Div(rows)],
        style={"padding": "10px"},
    )

    # Interactive updates for all graphs
    @app.callback(
        [Output(i, "figure") for i, _, _ in graph_defs],
        [
            Input("orientation", "value"),
            Input("log-y", "value"),
            Input("clip-p99", "value"),
            Input("threshold", "value"),
        ],
    )
    def _update_all(orientation_v: str, logy_v: List[str], clipp_v: List[str], thr_v: float) -> List[go.Figure]:
        log_y = "log" in (logy_v or [])
        clip_p99 = "clip" in (clipp_v or [])
        threshold = float(thr_v) if thr_v is not None else None
        figs: List[go.Figure] = []
        for _, c, t in graph_defs:
            figs.append(
                _build_figure(
                    df,
                    c,
                    orientation=orientation_v,
                    log_y=log_y,
                    clip_p99=clip_p99,
                    threshold=threshold,
                    title=t,
                )
            )
        return figs

    return app


def main() -> None:
    """Run the Dash development server on localhost:8050."""
    app = create_app()
    app.run(debug=False)


if __name__ == "__main__":
    main()


