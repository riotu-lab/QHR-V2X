#!/usr/bin/env python3
"""
Provenance check for the published QHR-V2X curve in Figures 3, 4, 6 and 7.

Draws the same benchmark run twice. Both panels use the same three algorithms,
the same CSV, the same grids and the same seed. The ONLY difference is which
column the red QHR-V2X series is taken from:

    left  panel : qhr_v2x.msgs      * 0.001   <- what the code produces
    right panel : qhr_v2x.path_len  * 0.001   <- reproduces published Fig. 3

A* and Dijkstra are drawn from `msgs` in both panels and are identical between
them. See VERIFICATION.md section 2.8.

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
OUT = ROOT / "experiments" / "results" / "diagnostics" / "hypothesis_check_fig3.png"

# Red points read off the published Figure 3.
PAPER_FIG3 = {10: 0.013, 25: 0.035, 50: 0.070, 75: 0.110, 100: 0.150}


def main():
    if not CSV.exists():
        sys.exit(f"missing {CSV}\nrun experiments/scripts/reproduce_paper_results.py first")
    d = pd.read_csv(CSV)
    g = lambda a: d[d.algorithm == a].sort_values("grid_size")

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.4), dpi=200)

    # Left: every series from the msgs column, as the metric intends.
    ax = axes[0]
    ax.plot(g("astar").grid_size, g("astar").msgs * .001, "o-", color="tab:blue", label="A*")
    ax.plot(g("qhr_v2x").grid_size, g("qhr_v2x").msgs * .001, "s-", color="red", label="QHR-V2X")
    ax.plot(g("dijkstra").grid_size, g("dijkstra").msgs * .001, "^-", color="tab:green", label="Dijkstra")
    ax.set_title("All three from the msgs column\n(what the code actually produces)", fontsize=10)

    # Right: identical, except QHR-V2X is taken from path_len.
    ax = axes[1]
    ax.plot(g("astar").grid_size, g("astar").msgs * .001, "o-", color="tab:blue", label="A*")
    ax.plot(g("qhr_v2x").grid_size, g("qhr_v2x").path_len * .001, "s-", color="red", label="QHR-V2X")
    ax.plot(g("dijkstra").grid_size, g("dijkstra").msgs * .001, "^-", color="tab:green", label="Dijkstra")
    ax.set_title("QHR-V2X taken from path_len instead\n(matches published Fig. 3)", fontsize=10)

    for ax in axes:
        ax.set_xlabel("Grid Size")
        ax.set_ylabel("Estimated Time (ms)")
        ax.set_ylim(-0.3, 9.5)
        ax.legend(loc="upper left", fontsize=9)
        ax.grid(True, linestyle=":", alpha=0.5)

    fig.tight_layout()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT)
    plt.close(fig)
    print(f"wrote {OUT.relative_to(ROOT)}")

    # Numeric side of the same check.
    q = g("qhr_v2x").set_index("grid_size")
    print(f"\n{'grid':>5} {'msgs*.001':>10} {'path_len*.001':>14} {'paper Fig.3':>12} {'rel.err':>9}")
    for s, paper in PAPER_FIG3.items():
        pl = q.loc[s, "path_len"] * .001
        print(f"{s:>5} {q.loc[s,'msgs']*.001:>10.4f} {pl:>14.4f} {paper:>12.3f} "
              f"{abs(pl-paper)/paper*100:>8.1f}%")


if __name__ == "__main__":
    main()
