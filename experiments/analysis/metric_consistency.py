#!/usr/bin/env python3
"""
Apply each candidate RDM definition consistently to all three algorithms.

The published Figure 3 (centre panel) is the only one of the three that uses a
different column for QHR-V2X than for A* and Dijkstra. Under either definition
applied uniformly, the QHR-V2X advantage disappears:

  left   all three from `msgs`      -> QHR-V2X is the highest curve
  centre QHR from `path_len`, baselines from `msgs`  -> published Fig. 3
  right  all three from `path_len`  -> three identical curves (this is Fig. 5)

Run after experiments/scripts/reproduce_paper_results.py.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CSV = (ROOT / "benchmarks" / "results" / "benchmark_output_dense" / "csv"
       / "benchmark_results_dense_selected.csv")
OUT = ROOT / "experiments" / "results" / "diagnostics" / "metric_consistency_fig3.png"

STYLE = {"astar": ("A*", "tab:blue", "o"),
         "qhr_v2x": ("QHR-V2X", "red", "s"),
         "dijkstra": ("Dijkstra", "tab:green", "^")}


def main():
    if not CSV.exists():
        sys.exit(f"missing {CSV}\nrun experiments/scripts/reproduce_paper_results.py first")
    d = pd.read_csv(CSV)
    g = lambda a: d[d.algorithm == a].sort_values("grid_size")

    # (title, column used per algorithm)
    panels = [
        ("Consistent: all three from `msgs`\n(what the code produces)",
         {"astar": "msgs", "qhr_v2x": "msgs", "dijkstra": "msgs"}),
        ("Mixed: QHR-V2X from `path_len`,\nbaselines from `msgs` (published Fig. 3)",
         {"astar": "msgs", "qhr_v2x": "path_len", "dijkstra": "msgs"}),
        ("Consistent: all three from `path_len`\n(identical curves - this is Fig. 5)",
         {"astar": "path_len", "qhr_v2x": "path_len", "dijkstra": "path_len"}),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(16, 4.6), dpi=200)
    for ax, (title, cols) in zip(axes, panels):
        for algo, (label, colour, marker) in STYLE.items():
            sub = g(algo)
            ax.plot(sub.grid_size, sub[cols[algo]] * .001, marker=marker,
                    color=colour, label=label, linewidth=1.6, markersize=5,
                    alpha=0.75 if cols[algo] == "path_len" else 1.0)
        ax.set_title(title, fontsize=9)
        ax.set_xlabel("Grid Size")
        ax.set_ylabel("Estimated Time (ms)")
        ax.set_ylim(-0.3, 9.5)
        ax.legend(loc="upper left", fontsize=8)
        ax.grid(True, linestyle=":", alpha=0.5)

    fig.tight_layout()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT)
    plt.close(fig)
    print(f"wrote {OUT.relative_to(ROOT)}\n")

    q, a, dj = g("qhr_v2x").set_index("grid_size"), g("astar").set_index("grid_size"), g("dijkstra").set_index("grid_size")
    print("Under each definition applied to ALL three algorithms (grid 100x100):\n")
    print(f"{'definition':<26} {'A*':>10} {'QHR-V2X':>10} {'Dijkstra':>10}   QHR best?")
    print("-" * 74)
    print(f"{'msgs (expansions)':<26} {a.loc[100,'msgs']:>10.1f} {q.loc[100,'msgs']:>10.1f} "
          f"{dj.loc[100,'msgs']:>10.1f}   no - highest")
    print(f"{'path_len (hops)':<26} {a.loc[100,'path_len']:>10.1f} {q.loc[100,'path_len']:>10.1f} "
          f"{dj.loc[100,'path_len']:>10.1f}   no - tied")
    print(f"\n{'mixed (published)':<26} {a.loc[100,'msgs']:>10.1f} {q.loc[100,'path_len']:>10.1f} "
          f"{dj.loc[100,'msgs']:>10.1f}   yes - but the")
    print(f"{'':<26} {'(msgs)':>10} {'(path_len)':>10} {'(msgs)':>10}   columns differ")


if __name__ == "__main__":
    main()
