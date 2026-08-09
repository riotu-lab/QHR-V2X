#!/usr/bin/env python3
"""
Generate A* / QHR-V2X / Dijkstra comparison charts.
======================================================

Produces the three metrics reported in the QHR-V2X paper -- Route Discovery
Time (RDT), Route Discovery Messages (RDM) and Path Length (PL) -- plus the
node-expansion count Ne that Eq. 12 makes a claim about.

Why this script does not call ``tests/test_pathfinding_all.py``
--------------------------------------------------------------
The three algorithms in ``src/`` do not agree on what they count, so their
return values cannot be plotted on shared axes:

* ``astar_u.astar_u_heap``   counts heap pops only.
* ``dijkstra_grid_u``        counts non-stale heap pops only.
* ``qhr_v2x.qhr_v2x``        counts heap pops *and* heap pushes.

On the same 15x15 instance that is 174 / 174 / 347 for identical search
behaviour. Charting those side by side compares three different quantities.
This script therefore re-implements all three searches over one shared
instrumentation so that every metric has a single definition, and generates the
grids at their nominal obstacle density (the harness in ``tests/`` seeds
``int(size * density)`` obstacles rather than ``int(size * size * density)``,
which yields 1.6% coverage at 100x100 instead of 40%).

Metric definitions, applied identically to every algorithm
----------------------------------------------------------
expansions  Ne. Distinct nodes finalised (removed from the open set and closed).
messages    RDM. One control message per node selection, plus one per accepted
            edge relaxation -- i.e. one RREQ per hop explored and one update per
            improved cost estimate.
path_len    PL, in hops.
time_ms     RDT, measured wall-clock time for the search call.

Usage
-----
    python experiments/scripts/generate_comparison_charts.py
    python experiments/scripts/generate_comparison_charts.py --seeds 20 --eta 0.3
"""

from __future__ import annotations

import argparse
import csv
import heapq
import math
import statistics
import sys
import time
from collections import deque
from pathlib import Path
from typing import Callable, Dict, List, Sequence, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

Coord = Tuple[int, int]
SearchResult = Tuple[List[Coord], int, int]  # (path, expansions, messages)

SHIFTS = ((-1, 0), (1, 0), (0, -1), (0, 1))


# --------------------------------------------------------------------------
# Instance generation
# --------------------------------------------------------------------------


def make_grid(size: int, density: float, rng: np.random.Generator) -> np.ndarray:
    """Uniformly random obstacles at the requested *fraction of cells*.

    Start (0,0) and goal (size-1,size-1) are always free. The obstacle count is
    ``round(size * size * density)``, so the realised density is the nominal
    density at every grid size.
    """
    total = size * size
    n_obstacles = int(round(total * density))

    start, goal = 0, total - 1
    choices = rng.choice(total, size=total, replace=False)
    blocked = [c for c in choices if c != start and c != goal][:n_obstacles]

    grid = np.zeros(total, dtype=bool)
    grid[blocked] = True
    return grid.reshape((size, size))


def _bfs_reachable(grid: np.ndarray, source: Coord) -> Tuple[List[Coord], Coord]:
    """Flood-fill from ``source``; return the reachable cells and the farthest one."""
    rows, cols = grid.shape
    seen = np.zeros_like(grid)
    seen[source] = True
    queue = deque([source])
    reached: List[Coord] = []
    farthest = source
    while queue:
        cell = queue.popleft()
        reached.append(cell)
        farthest = cell  # BFS order means the last cell dequeued is at max depth
        r, c = cell
        for dr, dc in SHIFTS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and not grid[nr, nc] and not seen[nr, nc]:
                seen[nr, nc] = True
                queue.append((nr, nc))
    return reached, farthest


def corner_to_corner_solvable(grid: np.ndarray) -> bool:
    """Whether a path exists between opposite corners of this grid."""
    size = grid.shape[0]
    start, goal = (0, 0), (size - 1, size - 1)
    if grid[start] or grid[goal]:
        return False
    reached, _ = _bfs_reachable(grid, start)
    return goal in set(reached)


def make_instance(size: int, density: float, seed: int) -> Tuple[np.ndarray, Coord, Coord]:
    """Build one solvable routing instance at the nominal obstacle density.

    Corner-to-corner queries cannot be used at the paper's 40% density: for
    uniform random obstacles the free-cell fraction of 0.60 sits barely above
    the 2D site-percolation threshold p_c ~ 0.5927, so opposite corners are
    almost never connected once the grid is large. Instead of quietly lowering
    the density to make corners reachable, this picks the query endpoints inside
    the largest connected free component, using a BFS double sweep so start and
    goal are an approximate-diameter pair. Every instance is solvable by
    construction and the route is as long as the component allows.
    """
    rng = np.random.default_rng(seed * 100_003 + 17)
    grid = make_grid(size, density, rng)

    rows, cols = grid.shape
    unassigned = ~grid
    best_component: List[Coord] = []
    for r in range(rows):
        for c in range(cols):
            if unassigned[r, c]:
                component, _ = _bfs_reachable(grid, (r, c))
                for cell in component:
                    unassigned[cell] = False
                if len(component) > len(best_component):
                    best_component = component

    if len(best_component) < 2:
        raise RuntimeError(f"{size}x{size} grid at density {density} has no traversable component")

    # Double sweep: farthest point from an arbitrary node, then farthest from that.
    _, first = _bfs_reachable(grid, best_component[0])
    _, second = _bfs_reachable(grid, first)
    return grid, first, second


def solvability_rate(size: int, density: float, trials: int) -> float:
    """Fraction of uniform-random grids at this density with a corner-to-corner path."""
    solvable = 0
    for trial in range(trials):
        rng = np.random.default_rng(size * 7919 + trial)
        if corner_to_corner_solvable(make_grid(size, density, rng)):
            solvable += 1
    return solvable / trials


# --------------------------------------------------------------------------
# Searches -- one shared skeleton, one shared counter
# --------------------------------------------------------------------------


def _reconstruct(parent: Sequence[int], goal_idx: int, cols: int) -> List[Coord]:
    path: List[Coord] = []
    cur = goal_idx
    while cur != -1:
        path.append(divmod(cur, cols))
        cur = parent[cur]
    path.reverse()
    return path


def _best_first(
    grid: np.ndarray,
    start: Coord,
    goal: Coord,
    heuristic: Callable[[int, int], float],
    select: Callable[[List[Tuple[float, int]]], Tuple[float, int]] | None = None,
) -> SearchResult:
    """Uniform best-first search skeleton.

    ``heuristic`` returning 0 gives Dijkstra; Manhattan gives A*. ``select``
    overrides plain argmin-f frontier selection, which is where QHR-V2X's
    amplification mechanism plugs in.
    """
    rows, cols = grid.shape
    n = rows * cols
    start_idx = start[0] * cols + start[1]
    goal_idx = goal[0] * cols + goal[1]

    inf = math.inf
    g_cost = [inf] * n
    parent = [-1] * n
    closed = [False] * n
    g_cost[start_idx] = 0.0

    frontier: List[Tuple[float, int]] = [(heuristic(start_idx, goal_idx), start_idx)]

    expansions = 0
    messages = 0

    while frontier:
        if select is None:
            _, current = heapq.heappop(frontier)
        else:
            _, current = select(frontier)

        if closed[current]:
            continue
        closed[current] = True
        expansions += 1
        messages += 1  # one RREQ per node selection

        if current == goal_idx:
            return _reconstruct(parent, goal_idx, cols), expansions, messages

        r, c = divmod(current, cols)
        for dr, dc in SHIFTS:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < rows and 0 <= nc < cols) or grid[nr, nc]:
                continue
            neighbour = nr * cols + nc
            if closed[neighbour]:
                continue
            tentative = g_cost[current] + 1.0
            if tentative < g_cost[neighbour]:
                g_cost[neighbour] = tentative
                parent[neighbour] = current
                heapq.heappush(frontier, (tentative + heuristic(neighbour, goal_idx), neighbour))
                messages += 1  # one update per accepted relaxation

    return [], expansions, messages


def _manhattan_factory(cols: int) -> Callable[[int, int], float]:
    def h(node: int, goal_idx: int) -> float:
        nr, nc = divmod(node, cols)
        gr, gc = divmod(goal_idx, cols)
        return float(abs(nr - gr) + abs(nc - gc))

    return h


def _zero_heuristic(node: int, goal_idx: int) -> float:
    return 0.0


def dijkstra(grid: np.ndarray, start: Coord, goal: Coord) -> SearchResult:
    return _best_first(grid, start, goal, _zero_heuristic)


def astar(grid: np.ndarray, start: Coord, goal: Coord) -> SearchResult:
    return _best_first(grid, start, goal, _manhattan_factory(grid.shape[1]))


def _amplified_probabilities(
    f_values: Sequence[float], temperature: float, eta: float
) -> np.ndarray:
    """Paper Eqs. (9)-(11): softmax, amplify against the mean, renormalise."""
    f = np.asarray(f_values, dtype=float)

    # Eq. 9, shifted for numerical stability (does not change the distribution).
    logits = -(f - f.min()) / max(temperature, 1e-12)
    p = np.exp(logits)
    p /= p.sum()

    # Eq. 10: reinforce below-mean cost, attenuate the rest.
    p = np.where(f < f.mean(), (1.0 + eta) * p, (1.0 - eta) * p)

    # Eq. 11.
    total = p.sum()
    return p / total if total > 0 else np.full(f.size, 1.0 / f.size)


def _make_qhr_selector(
    candidate_size: int,
    temperature: float,
    eta: float,
    rng: np.random.Generator | None,
) -> Callable[[List[Tuple[float, int]]], Tuple[float, int]]:
    """QHR-V2X frontier selection.

    Pops the ``candidate_size`` lowest-f entries to form the candidate set C,
    applies Eqs. (9)-(11), selects one, and returns the unselected entries to
    the heap. With ``rng=None`` selection is argmax over the amplified
    probabilities, exactly as Algorithm 1 step 4 specifies; with an ``rng`` it
    samples from them instead.
    """

    def select(frontier: List[Tuple[float, int]]) -> Tuple[float, int]:
        k = min(candidate_size, len(frontier))
        candidates = [heapq.heappop(frontier) for _ in range(k)]

        if k == 1:
            return candidates[0]

        probs = _amplified_probabilities([f for f, _ in candidates], temperature, eta)
        choice = int(np.argmax(probs)) if rng is None else int(rng.choice(k, p=probs))

        for i, entry in enumerate(candidates):
            if i != choice:
                heapq.heappush(frontier, entry)
        return candidates[choice]

    return select


def make_qhr_v2x(
    candidate_size: int, temperature: float, eta: float, stochastic: bool = False, seed: int = 0
) -> Callable[[np.ndarray, Coord, Coord], SearchResult]:
    def run(grid: np.ndarray, start: Coord, goal: Coord) -> SearchResult:
        rng = np.random.default_rng(seed) if stochastic else None
        selector = _make_qhr_selector(candidate_size, temperature, eta, rng)
        return _best_first(grid, start, goal, _manhattan_factory(grid.shape[1]), selector)

    return run


def load_repo_implementation() -> Callable[[np.ndarray, Coord, Coord], SearchResult] | None:
    """Adapt ``src/qhr_v2x.qhr_v2x`` to the (path, expansions, messages) shape.

    The shipped implementation exposes only (path, messages), and its message
    counter is not comparable with the others, so callers should read wall-clock
    time from this series and nothing else. Returns ``None`` when Qiskit is
    unavailable.
    """
    src = Path(__file__).resolve().parents[2] / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    try:
        from qhr_v2x import qhr_v2x as shipped  # type: ignore[import-not-found]
    except Exception:
        return None

    def run(grid: np.ndarray, start: Coord, goal: Coord) -> SearchResult:
        path, messages = shipped(grid, start, goal)
        return path, 0, messages

    return run


# --------------------------------------------------------------------------
# Measurement
# --------------------------------------------------------------------------

MODES = {
    "sparse": {"density": 0.20, "sizes": [10, 20, 30, 40, 50]},
    "dense": {"density": 0.40, "sizes": [10, 25, 50, 75, 100]},
}

# Plot order and styling. Keys must match the algorithm dict built in main().
STYLE = {
    "Dijkstra": {"color": "#c0392b", "marker": "s", "linestyle": "-"},
    "A*": {"color": "#2471a3", "marker": "o", "linestyle": "--"},
    "QHR-V2X": {"color": "#1e8449", "marker": "^", "linestyle": "-."},
    "QHR-V2X (sampled)": {"color": "#8e44ad", "marker": "v", "linestyle": ":"},
    "QHR-V2X (repo, Qiskit)": {"color": "#d68910", "marker": "D", "linestyle": ":"},
}


def coincident_series(
    stats: Dict[str, Dict[int, Tuple[float, float]]], series: Sequence[str]
) -> List[Tuple[str, str]]:
    """Find series pairs whose means agree at every grid size.

    Perfectly overlapping curves are invisible on a chart, so callers annotate
    the pairs this reports rather than leaving a reader to guess which line is
    hidden underneath another.
    """
    pairs: List[Tuple[str, str]] = []
    present = [name for name in series if name in stats]
    for i, first in enumerate(present):
        for second in present[i + 1 :]:
            sizes = sorted(set(stats[first]) & set(stats[second]))
            if not sizes:
                continue
            if all(
                math.isclose(stats[first][s][0], stats[second][s][0], rel_tol=1e-12, abs_tol=1e-12)
                for s in sizes
            ):
                pairs.append((first, second))
    return pairs


def underlaid_series(
    stats: Dict[str, Dict[int, Tuple[float, float]]], series: Sequence[str]
) -> set[str]:
    """Series that a later-drawn curve will completely cover.

    Drawing these wider leaves a visible halo around the covering curve, so an
    exact overlap reads as an overlap rather than as a missing line.
    """
    return {first for first, _ in coincident_series(stats, series)}


def measure(
    algorithms: Dict[str, Callable[[np.ndarray, Coord, Coord], SearchResult]],
    mode: str,
    seeds: int,
    repeats: int,
) -> List[dict]:
    """Run every algorithm on every (size, seed) instance and collect metrics."""
    density = MODES[mode]["density"]
    sizes = MODES[mode]["sizes"]
    rows: List[dict] = []

    for size in sizes:
        print(f"  {mode} {size}x{size} (density {density:.0%}) ", end="", flush=True)

        for seed in range(seeds):
            grid, start, goal = make_instance(size, density, seed)
            optimal_hops = None

            for name, fn in algorithms.items():
                # Warm-up call, discarded: excludes first-call overhead from RDT.
                fn(grid, start, goal)

                best_ms = math.inf
                path, expansions, messages = [], 0, 0
                for _ in range(repeats):
                    t0 = time.perf_counter()
                    path, expansions, messages = fn(grid, start, goal)
                    best_ms = min(best_ms, (time.perf_counter() - t0) * 1000.0)

                if not path:
                    raise RuntimeError(f"{name} failed on a solvable {size}x{size} grid")

                hops = len(path) - 1
                if name == "Dijkstra":
                    optimal_hops = hops

                rows.append(
                    {
                        "mode": mode,
                        "grid_size": size,
                        "density": density,
                        "seed": seed,
                        "algorithm": name,
                        "expansions": expansions,
                        "messages": messages,
                        "path_len": hops,
                        "time_ms": best_ms,
                        "optimal_hops": optimal_hops,
                    }
                )
            print(".", end="", flush=True)
        print(" done")

    return rows


def aggregate(rows: List[dict], metric: str) -> Dict[str, Dict[int, Tuple[float, float]]]:
    """Return {algorithm: {size: (mean, half-width of 95% CI)}}."""
    grouped: Dict[str, Dict[int, List[float]]] = {}
    for row in rows:
        grouped.setdefault(row["algorithm"], {}).setdefault(row["grid_size"], []).append(
            float(row[metric])
        )

    out: Dict[str, Dict[int, Tuple[float, float]]] = {}
    for algo, by_size in grouped.items():
        out[algo] = {}
        for size, values in sorted(by_size.items()):
            mean = statistics.fmean(values)
            if len(values) > 1:
                half = 1.96 * statistics.stdev(values) / math.sqrt(len(values))
            else:
                half = 0.0
            out[algo][size] = (mean, half)
    return out


# --------------------------------------------------------------------------
# Charts
# --------------------------------------------------------------------------

METRICS = [
    ("time_ms", "Route Discovery Time (ms)", "RDT", "Measured wall-clock search time"),
    ("messages", "Route Discovery Messages", "RDM", "Control messages (selections + updates)"),
    ("path_len", "Path Length (hops)", "PL", "Discovered path length"),
    ("expansions", "Node Expansions $N_e$", "Ne", "Distinct nodes finalised"),
]


def _apply_axes_style(ax, xlabel: str, ylabel: str, title: str) -> None:
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.legend(frameon=False)


def plot_metric(
    rows: List[dict],
    metric: str,
    ylabel: str,
    short: str,
    description: str,
    mode: str,
    seeds: int,
    out_dir: Path,
    series: Sequence[str],
    suffix: str = "",
    logy: bool = False,
) -> Path:
    stats = aggregate(rows, metric)
    density = MODES[mode]["density"]

    hidden = underlaid_series(stats, series)

    fig, ax = plt.subplots(figsize=(7.0, 4.6), dpi=150)
    for name in series:
        if name not in stats:
            continue
        sizes = sorted(stats[name])
        means = [stats[name][s][0] for s in sizes]
        errs = [stats[name][s][1] for s in sizes]
        covered = name in hidden
        ax.errorbar(
            sizes,
            means,
            yerr=errs,
            label=name,
            capsize=3,
            linewidth=6.0 if covered else 1.8,
            markersize=12 if covered else 6,
            alpha=0.45 if covered else 1.0,
            **STYLE.get(name, {}),
        )

    if logy:
        ax.set_yscale("log")

    _apply_axes_style(
        ax,
        "Grid size (cells per side)",
        ylabel,
        f"{description} under {density:.0%} obstacle density",
    )

    caption = (
        f"Mean of {seeds} independent seeds; error bars are 95% CI. "
        "Uniform random obstacles; identical metric definition for all algorithms."
    )
    for first, second in coincident_series(stats, series):
        caption += f"\n{first} and {second} coincide exactly at every grid size."

    fig.text(0.01, 0.01, caption, fontsize=7, color="#555555")
    fig.tight_layout(rect=(0, 0.035 * (1 + caption.count("\n")), 1, 1))

    path = out_dir / f"Fig_{short}_{mode}{suffix}.png"
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_summary(
    rows: List[dict], mode: str, seeds: int, out_dir: Path, series: Sequence[str]
) -> Path:
    density = MODES[mode]["density"]
    fig, axes = plt.subplots(2, 2, figsize=(11.5, 8.0), dpi=150)

    for ax, (metric, ylabel, _short, description) in zip(axes.ravel(), METRICS):
        stats = aggregate(rows, metric)
        hidden = underlaid_series(stats, series)
        for name in series:
            if name not in stats:
                continue
            sizes = sorted(stats[name])
            means = [stats[name][s][0] for s in sizes]
            errs = [stats[name][s][1] for s in sizes]
            covered = name in hidden
            ax.errorbar(
                sizes,
                means,
                yerr=errs,
                label=name,
                capsize=3,
                linewidth=5.0 if covered else 1.8,
                markersize=11 if covered else 6,
                alpha=0.45 if covered else 1.0,
                **STYLE.get(name, {}),
            )
        _apply_axes_style(ax, "Grid size (cells per side)", ylabel, description)

        # Overlapping curves are invisible, so name them inside the panel they
        # belong to rather than in a figure-wide caption.
        pairs = coincident_series(stats, series)
        if pairs:
            note = "\n".join(f"{a} = {b} exactly" for a, b in pairs)
            ax.text(
                0.98,
                0.02,
                note,
                transform=ax.transAxes,
                fontsize=7,
                va="bottom",
                ha="right",
                color="#555555",
            )

    fig.suptitle(
        f"QHR-V2X vs A* vs Dijkstra -- {mode} topology, {density:.0%} obstacle density",
        fontsize=13,
    )
    fig.text(
        0.01,
        0.01,
        f"Mean of {seeds} independent seeds; error bars are 95% CI. "
        "RDM counts node selections plus accepted relaxations for every algorithm alike.",
        fontsize=8,
        color="#555555",
    )
    fig.tight_layout(rect=(0, 0.03, 1, 0.96))

    path = out_dir / f"Fig_summary_{mode}.png"
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_implementation_cost(
    core_rows: List[dict],
    repo_rows: List[dict],
    mode: str,
    seeds: int,
    repo_seeds: int,
    out_dir: Path,
) -> Path:
    """Chart RDT only, adding the shipped Qiskit implementation.

    Wall-clock time is the one metric that compares across implementations, so
    this figure isolates what the Aer circuits cost given that their results are
    discarded.
    """
    density = MODES[mode]["density"]
    stats = aggregate(core_rows + repo_rows, "time_ms")
    series = ["A*", "QHR-V2X", "QHR-V2X (repo, Qiskit)"]

    fig, ax = plt.subplots(figsize=(7.0, 4.6), dpi=150)
    for name in series:
        if name not in stats:
            continue
        sizes = sorted(stats[name])
        ax.errorbar(
            sizes,
            [stats[name][s][0] for s in sizes],
            yerr=[stats[name][s][1] for s in sizes],
            label=name,
            capsize=3,
            linewidth=1.8,
            markersize=6,
            **STYLE.get(name, {}),
        )

    ax.set_yscale("log")
    _apply_axes_style(
        ax,
        "Grid size (cells per side)",
        "Route Discovery Time (ms, log scale)",
        f"Cost of the amplification machinery under {density:.0%} obstacle density",
    )
    fig.text(
        0.01,
        0.01,
        f"Error bars are 95% CI over {seeds} seeds, or {repo_seeds} for the shipped "
        "implementation. All three return the same path, so the separation is overhead alone.\n"
        "'QHR-V2X (repo, Qiskit)' is src/qhr_v2x.py unmodified, whose circuit results are "
        "discarded by a measurement-parsing error.",
        fontsize=7,
        color="#555555",
    )
    fig.tight_layout(rect=(0, 0.07, 1, 1))

    path = out_dir / f"Fig_implementation_cost_{mode}.png"
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return path


# The constant the paper's harness uses to turn a message count into a
# "time": tests/test_pathfinding_all.py sets time_complexity_factor = 0.001.
PAPER_TIME_FACTOR = 0.001

# Colours and markers matching Figs. 3 and 6 of the paper, so the regenerated
# version can be laid beside the published one.
PAPER_STYLE = {
    "A*": {"color": "#1f6fb4", "marker": "o"},
    "QHR-V2X": {"color": "#d62728", "marker": "s"},
    "Dijkstra": {"color": "#2ca02c", "marker": "^"},
}


def plot_paper_formula_rdt(
    rows: List[dict], mode: str, seeds: int, out_dir: Path
) -> Path:
    """Rebuild the paper's RDT figure using the paper's own definition of RDT.

    Figs. 3 and 6 plot `estimated_ms = avg_msgs * 0.001` rather than a measured
    duration. This reproduces that construction exactly -- same formula, same
    axes, same series styling -- but feeds it message counts that are defined
    identically for all three algorithms. It is the like-for-like replacement
    for the published figure, so the two can be compared directly.
    """
    stats = aggregate(rows, "messages")
    density = MODES[mode]["density"]
    series = ["A*", "QHR-V2X", "Dijkstra"]  # paper's legend order

    hidden = underlaid_series(stats, series)

    fig, ax = plt.subplots(figsize=(7.0, 4.6), dpi=150)
    for name in series:
        if name not in stats:
            continue
        sizes = sorted(stats[name])
        covered = name in hidden
        ax.plot(
            sizes,
            [stats[name][s][0] * PAPER_TIME_FACTOR for s in sizes],
            label=name,
            linewidth=6.0 if covered else 1.8,
            markersize=13 if covered else 7,
            alpha=0.45 if covered else 1.0,
            **PAPER_STYLE[name],
        )

    _apply_axes_style(
        ax,
        "Grid Size",
        "Estimated Time (ms)",
        f"Estimated Route Discovery Time (RDT) under {density:.0%} obstacle density",
    )

    caption = (
        f"Rebuilt with the paper's own definition, estimated_ms = mean RDM x {PAPER_TIME_FACTOR}, "
        f"over {seeds} seeds per grid size.\nThe difference from the published figure is the "
        "message counter: here all three algorithms are counted identically."
    )
    for first, second in coincident_series(stats, series):
        caption += f"\n{first} and {second} coincide exactly, so one curve hides the other."

    fig.text(0.01, 0.01, caption, fontsize=7, color="#555555")
    fig.tight_layout(rect=(0, 0.035 * (1 + caption.count("\n")), 1, 1))

    path = out_dir / f"Fig_RDT_paper_formula_{mode}.png"
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_solvability(out_dir: Path, trials: int = 60) -> Path:
    """Chart how often a uniform-random grid admits a corner-to-corner route.

    This is the constraint that makes the paper's "40% randomly distributed
    obstacles" unusable as written, and it is why the harness in ``tests/``
    appears to work only because its generator produces ~2% coverage instead.
    """
    densities = [0.10, 0.20, 0.30, 0.35, 0.40, 0.45]
    sizes = [10, 25, 50]

    fig, ax = plt.subplots(figsize=(7.0, 4.6), dpi=150)
    markers = ["o", "s", "^"]
    for size, marker in zip(sizes, markers):
        rates = [100.0 * solvability_rate(size, d, trials) for d in densities]
        ax.plot(
            [100 * d for d in densities],
            rates,
            marker=marker,
            linewidth=1.8,
            markersize=6,
            label=f"{size}x{size}",
        )

    ax.axvline(
        100 * (1 - 0.592746),
        color="#c0392b",
        linestyle="--",
        linewidth=1.6,
        label="Site-percolation threshold (40.7% blocked)",
    )
    ax.axvline(40.0, color="#7f8c8d", linestyle=":", linewidth=1.6, label="Paper's dense setting")

    _apply_axes_style(
        ax,
        "Obstacle density (% of cells blocked)",
        "Instances with a corner-to-corner route (%)",
        "Solvability of uniform-random grids by obstacle density",
    )
    fig.text(
        0.01,
        0.01,
        f"{trials} random grids per point. At the paper's 40% dense setting the free-cell "
        "fraction sits just above p_c ~ 0.5927,\nso opposite corners are rarely connected once "
        "the grid is large -- routing queries must be drawn from a connected component instead.",
        fontsize=7,
        color="#555555",
    )
    fig.tight_layout(rect=(0, 0.07, 1, 1))

    path = out_dir / "Fig_solvability_vs_density.png"
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_equation12_check(
    rows: List[dict], mode: str, eta: float, out_dir: Path
) -> Path | None:
    """Chart the ratio N'e / Ne that Eq. 12 predicts should equal (1 - eta).

    This is also where the sampling reading of Eq. 11 appears, if it was measured.
    It is not a proposed method, so it is kept out of the main figures; it belongs
    here because it is the answer to "was the stochastic reading tried?".
    """
    stats = aggregate(rows, "expansions")
    if "A*" not in stats or "QHR-V2X" not in stats:
        return None

    sizes = sorted(stats["A*"])
    ratios = [stats["QHR-V2X"][s][0] / stats["A*"][s][0] for s in sizes]
    has_sampled = "QHR-V2X (sampled)" in stats

    fig, ax = plt.subplots(figsize=(7.0, 4.6), dpi=150)
    ax.plot(
        sizes,
        ratios,
        color=STYLE["QHR-V2X"]["color"],
        marker="^",
        linewidth=1.8,
        markersize=6,
        label="Measured $N'_e / N_e$",
    )
    if has_sampled:
        sampled = [stats["QHR-V2X (sampled)"][s][0] / stats["A*"][s][0] for s in sizes]
        ax.plot(
            sizes,
            sampled,
            color=STYLE["QHR-V2X (sampled)"]["color"],
            marker="v",
            linestyle=":",
            linewidth=1.8,
            markersize=6,
            label="Measured $N'_e / N_e$, sampling instead of argmax",
        )

    ax.axhline(
        1.0 - eta,
        color="#c0392b",
        linestyle="--",
        linewidth=1.6,
        label=f"Eq. 12 prediction $1-\\eta$ = {1 - eta:.2f}",
    )
    ax.axhline(1.0, color="#7f8c8d", linestyle="-", linewidth=1.0, label="Parity with A*")

    _apply_axes_style(
        ax,
        "Grid size (cells per side)",
        "Expansion ratio $N'_e / N_e$ (dimensionless)",
        f"Eq. 12 check under {MODES[mode]['density']:.0%} obstacle density",
    )
    caption = (
        "Argmax selection over Eqs. (9)-(11) reproduces A* exactly, so the ratio is 1.00 for every "
        "eta, T and candidate-set size."
    )
    if has_sampled:
        caption += (
            "\nSampling instead of taking the argmax is the only reading that departs from A*, "
            "and it costs expansions rather than saving them."
        )
    fig.text(0.01, 0.01, caption, fontsize=7, color="#555555")
    fig.tight_layout(rect=(0, 0.035 * (1 + caption.count("\n")), 1, 1))

    path = out_dir / f"Fig_Eq12_check_{mode}.png"
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return path


def write_csv(rows: List[dict], path: Path) -> None:
    fields = [
        "mode",
        "grid_size",
        "density",
        "seed",
        "algorithm",
        "expansions",
        "messages",
        "path_len",
        "time_ms",
        "optimal_hops",
    ]
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def summarise(rows: List[dict], mode: str, eta: float) -> str:
    lines: List[str] = []
    density = MODES[mode]["density"]
    lines.append(f"### {mode.title()} topology ({density:.0%} obstacles)\n")

    algos = sorted({r["algorithm"] for r in rows})
    header = f"| {'Algorithm':<20} | {'RDT (ms)':>10} | {'RDM':>10} | {'PL (hops)':>10} | {'Ne':>10} | {'Optimal':>8} |"
    lines.append(header)
    lines.append("|" + "|".join("-" * len(part) for part in header.split("|")[1:-1]) + "|")

    for algo in algos:
        subset = [r for r in rows if r["algorithm"] == algo]
        rdt = statistics.fmean(r["time_ms"] for r in subset)
        rdm = statistics.fmean(r["messages"] for r in subset)
        pl = statistics.fmean(r["path_len"] for r in subset)
        ne = statistics.fmean(r["expansions"] for r in subset)
        optimal = sum(1 for r in subset if r["path_len"] == r["optimal_hops"])
        lines.append(
            f"| {algo:<20} | {rdt:>10.3f} | {rdm:>10.1f} | {pl:>10.2f} | {ne:>10.1f} |"
            f" {optimal}/{len(subset):<6} |"
        )

    stats = aggregate(rows, "expansions")
    if "A*" in stats and "QHR-V2X" in stats:
        sizes = sorted(stats["A*"])
        ratios = [stats["QHR-V2X"][s][0] / stats["A*"][s][0] for s in sizes]
        lines.append(
            f"\nEq. 12 predicts N'e/Ne = {1 - eta:.2f}; measured "
            f"{min(ratios):.4f}-{max(ratios):.4f} across grid sizes.\n"
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--seeds", type=int, default=20, help="independent instances per grid size (default: 20)")
    parser.add_argument("--repeats", type=int, default=3, help="timing repeats per instance, best is kept (default: 3)")
    parser.add_argument("--eta", type=float, default=0.3, help="amplification coefficient eta in Eq. 10 (default: 0.3)")
    parser.add_argument("--temperature", type=float, default=1.0, help="control parameter T in Eq. 9 (default: 1.0)")
    parser.add_argument("--candidate-size", type=int, default=8, help="size of candidate set C (default: 8)")
    parser.add_argument(
        "--include-stochastic",
        action="store_true",
        help="also measure the sampling reading of Eq. 11; it appears only in the Eq. 12 diagnostic, "
        "never in the main RDT/RDM/PL/Ne figures, which always show exactly the paper's three "
        "algorithms",
    )
    parser.add_argument(
        "--include-repo-impl",
        action="store_true",
        help="add an RDT figure including src/qhr_v2x.py as shipped (requires Qiskit)",
    )
    parser.add_argument(
        "--repo-seeds",
        type=int,
        default=5,
        help="seeds for the shipped implementation, which is orders of magnitude slower (default: 5)",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("experiments/results/figures"),
        help="output directory (default: experiments/results/figures)",
    )
    args = parser.parse_args()

    if not 0.0 < args.eta < 1.0:
        parser.error("--eta must lie in (0, 1)")

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    algorithms: Dict[str, Callable[[np.ndarray, Coord, Coord], SearchResult]] = {
        "Dijkstra": dijkstra,
        "A*": astar,
        "QHR-V2X": make_qhr_v2x(args.candidate_size, args.temperature, args.eta),
    }

    # The main figures always show exactly the three algorithms the paper compares.
    # The sampling reading of Eq. 11 is not a proposed method -- it exists only to
    # answer "did you try sampling?" -- so it is confined to the Eq. 12 diagnostic.
    series = ["Dijkstra", "A*", "QHR-V2X"]

    if args.include_stochastic:
        algorithms["QHR-V2X (sampled)"] = make_qhr_v2x(
            args.candidate_size, args.temperature, args.eta, stochastic=True, seed=99
        )

    repo_impl = None
    if args.include_repo_impl:
        repo_impl = load_repo_implementation()
        if repo_impl is None:
            print("Qiskit unavailable; skipping the shipped-implementation figure.\n")

    print("Generating A* / QHR-V2X / Dijkstra comparison charts")
    print(f"  seeds={args.seeds}  repeats={args.repeats}  eta={args.eta}  T={args.temperature}  |C|={args.candidate_size}")
    print()

    written: List[Path] = []
    report: List[str] = []

    print("  charting solvability against obstacle density")
    written.append(plot_solvability(out_dir))
    print()

    for mode in ("sparse", "dense"):
        rows = measure(algorithms, mode, args.seeds, args.repeats)

        csv_path = out_dir.parent / f"comparison_{mode}.csv"
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        write_csv(rows, csv_path)
        written.append(csv_path)

        for metric, ylabel, short, description in METRICS:
            written.append(
                plot_metric(
                    rows, metric, ylabel, short, description, mode, args.seeds, out_dir, series
                )
            )
        # RDM and RDT span orders of magnitude across grid sizes; a log companion
        # keeps the small-grid behaviour legible.
        written.append(
            plot_metric(
                rows,
                "messages",
                "Route Discovery Messages (log scale)",
                "RDM",
                "Control messages",
                mode,
                args.seeds,
                out_dir,
                series,
                suffix="_log",
                logy=True,
            )
        )
        written.append(plot_paper_formula_rdt(rows, mode, args.seeds, out_dir))
        written.append(plot_summary(rows, mode, args.seeds, out_dir, series))

        eq12 = plot_equation12_check(rows, mode, args.eta, out_dir)
        if eq12 is not None:
            written.append(eq12)

        if repo_impl is not None:
            repo_seeds = min(args.repo_seeds, args.seeds)
            print(f"  measuring src/qhr_v2x.py as shipped ({repo_seeds} seeds)")
            repo_rows = measure({"QHR-V2X (repo, Qiskit)": repo_impl}, mode, repo_seeds, 1)
            written.append(
                plot_implementation_cost(
                    rows, repo_rows, mode, args.seeds, repo_seeds, out_dir
                )
            )

        report.append(summarise(rows, mode, args.eta))
        print()

    figure_index = "\n".join(
        f"- `{p.relative_to(out_dir.parent) if out_dir.parent in p.parents else p.name}`"
        for p in written
        if p.suffix == ".png"
    )

    invocation = " ".join(
        [
            "python experiments/scripts/generate_comparison_charts.py",
            f"--seeds {args.seeds}",
            f"--repeats {args.repeats}",
            f"--eta {args.eta}",
            f"--temperature {args.temperature}",
            f"--candidate-size {args.candidate_size}",
        ]
        + (["--include-stochastic"] if args.include_stochastic else [])
        + (["--include-repo-impl", f"--repo-seeds {args.repo_seeds}"] if repo_impl else [])
    )

    report_path = out_dir.parent / "comparison_summary.md"
    report_path.write_text(
        "# A* / QHR-V2X / Dijkstra comparison\n\n"
        f"Seeds per grid size: {args.seeds}. Timing repeats per instance: {args.repeats} "
        "(minimum kept). Amplification parameters: "
        f"eta={args.eta}, T={args.temperature}, |C|={args.candidate_size}.\n\n"
        "## Metric definitions\n\n"
        "All algorithms are measured through one shared search skeleton, so every metric has a "
        "single definition:\n\n"
        "- **RDT** - measured wall-clock search time in milliseconds.\n"
        "- **RDM** - control messages: one per node selection, plus one per accepted edge "
        "relaxation.\n"
        "- **PL** - discovered path length in hops.\n"
        "- **Ne** - distinct nodes finalised, the quantity Eq. 12 makes a claim about.\n\n"
        "## Instance generation\n\n"
        "Obstacles are uniform random at the nominal density, i.e. "
        "`round(size * size * density)` blocked cells. Corner-to-corner queries are not usable "
        "at the 40% dense setting: the resulting free-cell fraction of 0.60 sits just above the "
        "2D site-percolation threshold p_c ~ 0.5927, so opposite corners are rarely connected "
        "once the grid is large (see `figures/Fig_solvability_vs_density.png`). Endpoints are "
        "therefore drawn from the largest connected free component as an approximate-diameter "
        "pair, which keeps every instance solvable without silently lowering the density.\n\n"
        "## Which series appear where\n\n"
        "Every figure shows exactly the three algorithms the paper compares: Dijkstra, A* and "
        "QHR-V2X. QHR-V2X uses argmax selection over Eqs. (9)-(11), as Algorithm 1 step 4 "
        "specifies.\n\n"
        + (
            "`QHR-V2X (sampled)` is the alternative reading of Eq. 11 -- sampling from the "
            "amplified distribution rather than taking its argmax. It is not a proposed method "
            "and exists only to record that the reading was tried, so it is confined to the "
            "tables below and to `figures/Fig_Eq12_check_*.png`.\n\n"
            if args.include_stochastic
            else "Re-run with `--include-stochastic` to additionally measure the sampling reading "
            "of Eq. 11; it is excluded here.\n\n"
        )
        + "## Results\n\n" + "\n\n".join(report) + "\n\n"
        "## Figures\n\n" + figure_index + "\n\n"
        "## Reproduce\n\n```bash\n" + invocation + "\n```\n"
    )
    written.append(report_path)

    print("Wrote:")
    for path in written:
        print(f"  {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
