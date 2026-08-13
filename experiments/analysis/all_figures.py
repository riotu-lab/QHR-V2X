#!/usr/bin/env python3
"""
Generate every figure the QHR-V2X benchmark data supports.

Six of them are the paper's Figures 3-8 and are written by `paper_figures.py`;
this script emits those plus every other view of the same CSVs:

    line/        4 metrics x 2 modes            8   (6 of these are Figs. 3-8)
    log/         3 wide-range metrics x 2 modes 6   log-y, for order-of-magnitude gaps
    bar/         4 metrics x 2 modes            8   per-grid-size comparison
    overview/    all 4 metrics, 1 panel x mode  2   one-glance summary
    relative/    each algorithm / A*, x mode    2   normalised overhead
    accessible/  4 metrics x 2 modes            8   colour-vision-safe variant

    total                                      34

Every series in every figure reads its own algorithm's row for the stated metric,
so one figure always means one metric. `estimated_ms` is `msgs * 0.001`, as defined
in tests/test_pathfinding_all.py.

Usage:
    make reproduce                                   # produce the CSVs first
    python experiments/analysis/all_figures.py
    python experiments/analysis/all_figures.py --dpi 300

Outputs to experiments/results/all_figures/ plus a MANIFEST.md describing each file.
"""
from __future__ import annotations

import argparse

import matplotlib.pyplot as plt
import numpy as np

from figure_style import (LINE_STYLES, METRICS, MODE_LABEL, MODES,
                          PALETTES, RESULTS, SERIES, add_legend, apply_axes_style,
                          load_all, plot_measured, rel, save)

OUT = RESULTS / "all_figures"

# The six published figures, as (number, mode, metric).
PAPER_MAP = {
    ("dense", "estimated_ms"): 3, ("dense", "msgs"): 4, ("dense", "path_len"): 5,
    ("sparse", "estimated_ms"): 6, ("sparse", "msgs"): 7, ("sparse", "path_len"): 8,
}

manifest: list[tuple[str, str]] = []


def note(path, description: str) -> None:
    manifest.append((rel(path), description))


LINE_STYLE = "straight"   # set from --line-style in main()


def _plot_series(ax, df, metric_key, palette, *, marker_size=3.5, line_width=1.1):
    for s in SERIES:
        sub = df[df.algorithm == s.key].sort_values("grid_size")
        if sub.empty:
            continue
        plot_measured(ax, sub.grid_size, sub[metric_key], color=palette[s.key],
                      marker=s.marker, label=s.label, style=LINE_STYLE,
                      markersize=marker_size, linewidth=line_width)


# --------------------------------------------------------------------------- line

def line_figures(frames, dpi, palette_name="paper", subdir="line", tag=""):
    palette = PALETTES[palette_name]
    for mode in MODES:
        for m in METRICS:
            fig, ax = plt.subplots(figsize=(3.6, 2.7))
            _plot_series(ax, frames[mode], m.key, palette)
            apply_axes_style(ax, "Grid Size", m.axis)
            add_legend(ax)
            fig.tight_layout(pad=0.3)

            number = PAPER_MAP.get((mode, m.key))
            stem = f"Figure_{number}_" if number and not tag else ""
            path = OUT / subdir / f"{stem}{m.key}_{mode}{tag}.png"
            save(fig, path, dpi)
            what = f"{m.title} vs grid size, {MODE_LABEL[mode]}"
            note(path, what + (f" - paper Figure {number}" if number else "")
                 + (" - Okabe-Ito palette" if tag else ""))


# ---------------------------------------------------------------------------- log

def log_figures(frames, dpi):
    for mode in MODES:
        for m in (x for x in METRICS if x.log_worthy):
            fig, ax = plt.subplots(figsize=(3.6, 2.7))
            _plot_series(ax, frames[mode], m.key, PALETTES["paper"])
            ax.set_yscale("log")
            apply_axes_style(ax, "Grid Size", m.axis + " - log scale")
            add_legend(ax, loc="lower right")
            fig.tight_layout(pad=0.3)
            path = OUT / "log" / f"log_{m.key}_{mode}.png"
            save(fig, path, dpi)
            note(path, f"{m.title}, log-y, {MODE_LABEL[mode]} - separates curves that "
                       "overlap near the origin on a linear axis")


# ---------------------------------------------------------------------------- bar

def bar_figures(frames, dpi):
    palette = PALETTES["paper"]
    for mode in MODES:
        df = frames[mode]
        sizes = sorted(df.grid_size.unique())
        x = np.arange(len(sizes))
        # Leave a visible gap between adjacent bars rather than butting them together.
        slot = 0.8 / len(SERIES)
        width = slot * 0.88
        for m in METRICS:
            fig, ax = plt.subplots(figsize=(4.4, 2.8))
            for i, s in enumerate(SERIES):
                sub = df[df.algorithm == s.key].sort_values("grid_size").set_index("grid_size")
                if sub.empty:
                    continue
                ax.bar(x + i * slot, [sub.loc[sz, m.key] for sz in sizes],
                       width=width, color=palette[s.key], label=s.label, linewidth=0)
            ax.set_xticks(x + slot * (len(SERIES) - 1) / 2)
            ax.set_xticklabels(sizes)
            apply_axes_style(ax, "Grid Size", m.axis)
            add_legend(ax)
            fig.tight_layout(pad=0.3)
            path = OUT / "bar" / f"bar_{m.key}_{mode}.png"
            save(fig, path, dpi)
            note(path, f"{m.title} by grid size, {MODE_LABEL[mode]} - grouped bars")


# ----------------------------------------------------------------------- overview

def overview_figures(frames, dpi):
    for mode in MODES:
        fig, axes = plt.subplots(2, 2, figsize=(7.2, 5.0))
        for ax, m in zip(axes.ravel(), METRICS):
            _plot_series(ax, frames[mode], m.key, PALETTES["paper"], marker_size=3.0)
            apply_axes_style(ax, "Grid Size", m.axis, base=6.5)
        add_legend(axes[0, 0], base=6.5)
        fig.suptitle(f"QHR-V2X benchmark overview - {MODE_LABEL[mode]}",
                     fontsize=8.5, fontweight="bold")
        fig.tight_layout(pad=0.4, rect=(0, 0, 1, 0.96))
        path = OUT / "overview" / f"overview_{mode}.png"
        save(fig, path, dpi)
        note(path, f"All four metrics for {MODE_LABEL[mode]} in one panel")


# ----------------------------------------------------------------------- relative

def relative_figures(frames, dpi):
    """Each algorithm's message count as a multiple of A*'s, so overhead reads directly."""
    palette = PALETTES["paper"]
    for mode in MODES:
        df = frames[mode]
        base = df[df.algorithm == "astar"].sort_values("grid_size").set_index("grid_size")["msgs"]
        if base.empty:
            continue
        fig, ax = plt.subplots(figsize=(3.6, 2.7))
        for s in SERIES:
            sub = df[df.algorithm == s.key].sort_values("grid_size").set_index("grid_size")
            if sub.empty:
                continue
            plot_measured(ax, sub.index, sub["msgs"] / base.reindex(sub.index),
                          color=palette[s.key], marker=s.marker, label=s.label,
                          style=LINE_STYLE)
        ax.axhline(1.0, color="0.55", linewidth=0.7, linestyle="--", zorder=0)
        apply_axes_style(ax, "Grid Size", "RDM relative to A*  (x)")
        add_legend(ax)
        fig.tight_layout(pad=0.3)
        path = OUT / "relative" / f"relative_msgs_{mode}.png"
        save(fig, path, dpi)
        note(path, f"Route Discovery Messages as a multiple of A*, {MODE_LABEL[mode]} "
                   "- dashed line is A* itself at 1.0x")


# ----------------------------------------------------------------------- manifest

def write_manifest(dpi: int):
    path = OUT / "MANIFEST.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        f.write("# QHR-V2X figure catalogue\n\n")
        f.write(f"{len(manifest)} figures, {dpi} dpi, generated by "
                "`experiments/analysis/all_figures.py` from the benchmark CSVs.\n\n")
        f.write("Regenerate with `make figures-all`. Every point is a live "
                "algorithm run - nothing is hard-coded.\n\n")
        f.write("| File | Shows |\n| --- | --- |\n")
        for p, d in manifest:
            f.write(f"| `{p}` | {d} |\n")
        f.write("\n## Palettes\n\n")
        f.write("Figures use the published colours (A* blue, QHR-V2X red, Dijkstra "
                "green). That red/green pair sits at deuteranopia dE 3.9, below the "
                "dE 8 target, so `accessible/` repeats Figures 3-8 in Okabe-Ito "
                "(dE 11.0, all checks pass). Every figure also assigns a distinct "
                "marker per algorithm, so identity never rests on hue alone.\n")
    return path


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dpi", type=int, default=600, help="output resolution (default 600)")
    ap.add_argument("--line-style", choices=sorted(LINE_STYLES), default="straight",
                    help="how points are joined: 'straight' (default) draws only what "
                         "was measured; 'curved' smooths with a monotone cubic (PCHIP).")
    args = ap.parse_args()

    global LINE_STYLE
    LINE_STYLE = args.line_style

    frames = load_all()

    print("Generating full figure catalogue\n")
    line_figures(frames, args.dpi)
    log_figures(frames, args.dpi)
    bar_figures(frames, args.dpi)
    overview_figures(frames, args.dpi)
    relative_figures(frames, args.dpi)
    line_figures(frames, args.dpi, palette_name="accessible",
                 subdir="accessible", tag="_okabe_ito")

    for p, d in manifest:
        print(f"  {p}")
    mpath = write_manifest(args.dpi)
    print(f"\n  {rel(mpath)}")
    print(f"\n{len(manifest)} figures written to {rel(OUT)}")


if __name__ == "__main__":
    main()
