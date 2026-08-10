"""
Shared plotting vocabulary for the QHR-V2X figure suite.

One place defines the series order, palettes, metric metadata and data loading, so
`paper_figures.py` (the six published figures) and `all_figures.py` (the full
catalogue) cannot drift apart.

Palettes
--------
`PAPER`     the colours used in the published figures: A* blue, QHR-V2X red,
            Dijkstra green. Retained so Figures 3-8 match the paper.
`ACCESSIBLE` Okabe-Ito blue / vermillion / bluish-green.

The paper palette fails colour-vision-deficiency separation: the QHR-V2X red and
Dijkstra green sit at deutan dE 3.9, below the dE 8 target, so readers with
red-green CVD cannot separate those two series by colour alone. Both palettes
therefore pair every series with a distinct marker, which carries identity
independently of hue. The Okabe-Ito set reaches deutan dE 11.0 and passes all
checks; `all_figures.py` emits it as a parallel variant.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import NamedTuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "experiments" / "results"


class Series(NamedTuple):
    key: str        # algorithm name in the CSV
    label: str      # legend text
    marker: str


# Fixed order. Never cycled, never reordered by value - colour follows the
# algorithm, not its rank in a given figure.
SERIES: tuple[Series, ...] = (
    Series("astar",    "A*",       "o"),
    Series("qhr_v2x",  "QHR-V2X",  "s"),
    Series("dijkstra", "Dijkstra", "^"),
)

PALETTES: dict[str, dict[str, str]] = {
    # As published.
    "paper": {"astar": "#1f77b4", "qhr_v2x": "#d62728", "dijkstra": "#2ca02c"},
    # Okabe-Ito; passes lightness, chroma, CVD separation, contrast.
    "accessible": {"astar": "#0072B2", "qhr_v2x": "#D55E00", "dijkstra": "#009E73"},
}


class Metric(NamedTuple):
    key: str          # CSV column
    axis: str         # y-axis label
    title: str        # human-readable name
    log_worthy: bool  # spans orders of magnitude -> a log variant is informative


METRICS: tuple[Metric, ...] = (
    Metric("msgs",         "Messages (RDM)",      "Route Discovery Messages",        True),
    Metric("path_len",     "Path Length (hops)",  "Path Length",                     False),
    Metric("time_ms",      "Measured Time (ms)",  "Measured Route Discovery Time",   True),
    Metric("estimated_ms", "Estimated Time (ms)", "Estimated Route Discovery Time",  True),
)

METRIC_BY_KEY = {m.key: m for m in METRICS}

MODES = ("dense", "sparse")
MODE_LABEL = {"dense": "40% obstacle density", "sparse": "20% obstacle density"}


# --------------------------------------------------------------- RDT time models
#
# "Estimated Route Discovery Time" is a proxy, not a measured quantity. Two models
# are defensible, and the codebase supports both. Whichever is chosen, it applies
# to every algorithm in the figure - a comparison plot where one series uses a
# different model than the others does not measure anything.
#
#   messages  RDT = RDM x PER_MSG_MS
#             Route discovery costs one unit per control message exchanged while
#             the route is being searched for. This is the definition already in
#             tests/test_pathfinding_all.py (`estimated_ms = avg_msgs * 0.001`)
#             and the one the paper's A* and Dijkstra series use.
#
#   hops      RDT = PL x PER_HOP_MS
#             Route discovery costs one per-hop propagation delay per hop of the
#             discovered route. Ignores search effort, so under this model any two
#             algorithms returning equal-length paths have equal RDT by
#             construction - here all three do, so the curves coincide.
#
PER_MSG_MS = 0.001   # time_complexity_factor in tests/test_pathfinding_all.py
PER_HOP_MS = 0.001   # per-hop propagation delay

TIME_MODELS = {
    "messages": ("msgs", PER_MSG_MS, "Estimated Time (ms)"),
    "hops": ("path_len", PER_HOP_MS, "Estimated Time (ms) - hop model"),
}


def estimated_time(df: pd.DataFrame, model: str) -> pd.Series:
    """Estimated RDT under the named model, computed identically for every row."""
    if model not in TIME_MODELS:
        raise ValueError(f"unknown time model {model!r}; choose from {sorted(TIME_MODELS)}")
    column, factor, _ = TIME_MODELS[model]
    return df[column] * factor


def load(mode: str) -> pd.DataFrame:
    """Read one mode's benchmark CSV, or exit with the command that creates it."""
    csv = (ROOT / "benchmarks" / "results" / f"benchmark_output_{mode}"
           / "csv" / f"benchmark_results_{mode}_selected.csv")
    if not csv.exists():
        sys.exit(
            f"missing {csv}\n"
            "run: python experiments/scripts/reproduce_paper_results.py "
            "--algorithms qhr_v2x,astar,dijkstra\n"
            "or:  make reproduce"
        )
    return pd.read_csv(csv)


def load_all() -> dict[str, pd.DataFrame]:
    return {mode: load(mode) for mode in MODES}


# ------------------------------------------------------------------ line styles
#
# `straight`  join measured points with line segments. The default: nothing is
#             drawn that was not measured.
# `curved`    interpolate with a monotone cubic (PCHIP) for the smooth look of
#             the published figures. PCHIP is used rather than a natural cubic
#             spline because it cannot overshoot - with only five grid sizes per
#             curve, a natural spline can bulge past the surrounding points and
#             imply a peak or dip that was never measured. PCHIP stays within the
#             data's own bounds between consecutive points.
#
# Under either style the markers sit on the measured values, so the real data
# points remain visible and the line is only the connection between them.
LINE_STYLES = ("straight", "curved")
_CURVE_SAMPLES = 200


def plot_measured(ax, x, y, *, color: str, marker: str, label: str,
                  style: str = "straight", markersize: float = 3.5,
                  linewidth: float = 1.1, alpha: float = 1.0):
    """Draw one series. `style` selects segment joins or monotone-cubic smoothing."""
    if style not in LINE_STYLES:
        raise ValueError(f"unknown line style {style!r}; choose from {LINE_STYLES}")

    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    # PCHIP needs at least 3 distinct abscissae; fall back to segments otherwise.
    if style == "curved" and len(x) >= 3:
        from scipy.interpolate import PchipInterpolator

        order = np.argsort(x)
        xs, ys = x[order], y[order]
        fine = np.linspace(xs[0], xs[-1], _CURVE_SAMPLES)
        ax.plot(fine, PchipInterpolator(xs, ys)(fine), color=color,
                linewidth=linewidth, alpha=alpha, zorder=2)
        # Markers carry the label so the legend shows the marker, not a bare line.
        return ax.plot(x, y, linestyle="none", marker=marker, color=color,
                       markersize=markersize, label=label, markeredgewidth=0,
                       alpha=alpha, zorder=3)

    return ax.plot(x, y, marker=marker, color=color, markersize=markersize,
                   linewidth=linewidth, label=label, markeredgewidth=0,
                   alpha=alpha)


def apply_axes_style(ax, xlabel: str, ylabel: str, *, base: float = 7.0) -> None:
    """Recessive frame and ticks; the data carries the ink."""
    ax.set_xlabel(xlabel, fontsize=base, fontweight="bold")
    ax.set_ylabel(ylabel, fontsize=base, fontweight="bold")
    ax.tick_params(labelsize=base - 1, width=0.6, length=2.5)
    for spine in ax.spines.values():
        spine.set_linewidth(0.6)
    ax.margins(x=0.02)


def add_legend(ax, *, base: float = 7.0, loc: str = "upper left"):
    """A legend is always present - three series are never distinguished by colour alone."""
    return ax.legend(loc=loc, fontsize=base - 1.5, frameon=True, framealpha=1.0,
                     edgecolor="0.5", borderpad=0.4, handlelength=1.6,
                     labelspacing=0.3)


def save(fig, path: Path, dpi: int) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return path


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))
