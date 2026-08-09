#!/usr/bin/env python3
"""
Generate Figures 3-8 of the QHR-V2X paper from the benchmark output.

    QHR-V2X: A Quantum-Heuristic Routing Framework for Efficient V2X Path
    Discovery. IEEE Open J. Commun. Soc., vol. 7, 2026, pp. 211-220.

Figure map:

    Fig. 3  Estimated RDT, 40% obstacle density   dense  / estimated_ms
    Fig. 4  RDM, 40% obstacle density             dense  / msgs
    Fig. 5  PL, 40% obstacle density              dense  / path_len
    Fig. 6  Estimated RDT, 20% obstacle density   sparse / estimated_ms
    Fig. 7  RDM, 20% obstacle density             sparse / msgs
    Fig. 8  PL, 20% obstacle density              sparse / path_len

Each figure reads one column for all three algorithms, so the metric named on the
axis is the metric plotted for every series. `estimated_ms` is `msgs * 0.001`, as
defined in tests/test_pathfinding_all.py.

For every other view of the same data - log scales, bar charts, overview panels,
a colour-vision-safe palette - see `all_figures.py`.

Usage:
    make reproduce                                  # produce the CSVs first
    python experiments/analysis/paper_figures.py

Outputs to experiments/results/paper_figures/.
"""
from __future__ import annotations

import argparse

import matplotlib.pyplot as plt

from figure_style import (METRIC_BY_KEY, PALETTES, RESULTS, SERIES, TIME_MODELS,
                          add_legend, apply_axes_style, estimated_time, load_all,
                          rel, save)

OUT = RESULTS / "paper_figures"

# (figure number, mode, metric key, caption as printed in the paper)
FIGURES = [
    (3, "dense",  "estimated_ms",
     "Estimated Route Discovery Time (RDT) under 40% obstacle density."),
    (4, "dense",  "msgs",
     "Route Discovery Messages (RDM) under 40% obstacle density."),
    (5, "dense",  "path_len",
     "Path Length (PL) under 40% obstacle density."),
    (6, "sparse", "estimated_ms",
     "Estimated Route Discovery Time (RDT) under sparse topology with 20% obstacle density."),
    (7, "sparse", "msgs",
     "Route Discovery Messages (RDM) under sparse topology with 20% obstacle density."),
    (8, "sparse", "path_len",
     "Path Length (PL) under sparse topology with 20% obstacle density."),
]


def series_values(sub, metric_key: str, time_model: str):
    """The y-values for one algorithm. Estimated RDT follows the chosen model;
    every other metric is the raw column. The same rule applies to all series."""
    if metric_key == "estimated_ms":
        return estimated_time(sub, time_model)
    return sub[metric_key]


def y_label(metric_key: str, time_model: str) -> str:
    if metric_key == "estimated_ms":
        return TIME_MODELS[time_model][2]
    return METRIC_BY_KEY[metric_key].axis


def draw(df, number: int, mode: str, metric_key: str, dpi: int, time_model: str):
    palette = PALETTES["paper"]
    suffix = "" if time_model == "messages" else f"_{time_model}"

    fig, ax = plt.subplots(figsize=(3.6, 2.7))
    for s in SERIES:
        sub = df[df.algorithm == s.key].sort_values("grid_size")
        if sub.empty:
            print(f"  note: Fig. {number} - no rows for '{s.key}', series omitted")
            continue
        ax.plot(sub.grid_size, series_values(sub, metric_key, time_model),
                marker=s.marker, color=palette[s.key], markersize=3.5,
                linewidth=1.1, label=s.label, markeredgewidth=0)

    apply_axes_style(ax, "Grid Size", y_label(metric_key, time_model))
    add_legend(ax)
    fig.tight_layout(pad=0.3)
    return save(fig, OUT / f"Figure_{number}_{metric_key}_{mode}{suffix}.png", dpi)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dpi", type=int, default=600, help="output resolution (default 600)")
    ap.add_argument("--time-model", choices=sorted(TIME_MODELS), default="messages",
                    help="how Estimated RDT is derived: 'messages' (RDM x 0.001, the "
                         "published definition) or 'hops' (path length x per-hop delay). "
                         "Applies to every algorithm alike.")
    args = ap.parse_args()

    frames = load_all()

    print(f"Generating paper Figures 3-8  (estimated-RDT model: {args.time_model})\n")
    for number, mode, metric_key, caption in FIGURES:
        path = draw(frames[mode], number, mode, metric_key, args.dpi, args.time_model)
        print(f"  Fig. {number}  {caption}")
        print(f"            -> {rel(path)}")

    # Print every plotted value so each point on each figure is checkable.
    print("\nPlotted values\n")
    for number, mode, metric_key, _ in FIGURES:
        df = frames[mode]
        sizes = sorted(df.grid_size.unique())
        print(f"Fig. {number}  {mode}, {metric_key} ({y_label(metric_key, args.time_model)})")
        print(f"  {'grid':>8} " + " ".join(f"{s:>10}" for s in sizes))
        for s in SERIES:
            sub = df[df.algorithm == s.key].sort_values("grid_size").set_index("grid_size")
            if sub.empty:
                continue
            vals = series_values(sub, metric_key, args.time_model)
            print(f"  {s.label:>8} " + " ".join(f"{vals.loc[sz]:>10.2f}" for sz in sizes))
        print()

    print(f"6 figures written to {rel(OUT)}")


if __name__ == "__main__":
    main()
