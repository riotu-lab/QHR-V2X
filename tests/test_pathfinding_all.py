import os
import time
import warnings
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from dijkstra_grid_u import dijkstra_grid
from dijkstra_quantum_enhanced import dijkstra_grid_quantum
from astar_u import astar_u_heap
# from theta_star import theta_star
# from gbfs_u_opt import gbfs
# from bellman_ford_u_opt import bellman_ford_u_opt
from cqw_quantum import cqw_quantum
from astar_u_quantum import astar_u_quantum
from cqw_vectorized import cqw_vectorized
from grover_classic import grover_classic
from grover_quantum_bfs import grover_quantum_bfs
from qhr_v2x import qhr_v2x, qhr_v2x_classical_baseline


# Seed used for the grids behind the published figures. Passing this reproduces
# the paper's exact numbers; by default a fresh seed is drawn per run.
PAPER_SEED = 12345


def resolve_seed(seed=None) -> int:
    """
    Resolve the RNG seed for a benchmark run.

    `None` (the default) draws a fresh seed from system entropy, so successive
    runs explore different obstacle layouts. The drawn value is returned and
    recorded alongside the results, so any run can be replayed exactly by
    passing it back in.

    Accepts an int, the string "paper" for `PAPER_SEED`, or "random"/None.
    """
    if seed is None or seed == "random":
        return int(np.random.SeedSequence().entropy % (2 ** 32))
    if seed == "paper":
        return PAPER_SEED
    return int(seed)


def build_grid(size: int, mode: str, seed: int) -> np.ndarray:
    """
    Construct one benchmark grid. True marks an obstacle.

    Dense mode scatters obstacle blobs using `seed`. Sparse mode is deterministic
    by construction - it writes a partial wall into column `size // 3` - so `seed`
    does not affect it.
    """
    density = 0.4 if mode == "dense" else 0.2
    grid = np.zeros((size, size), dtype=bool)
    goal = (size - 1, size - 1)

    if mode == "dense":
        rng = np.random.default_rng(seed)
        for _ in range(int(size * density)):
            r, c = rng.integers(size), rng.integers(size)
            if (r, c) != (0, 0) and (r, c) != goal:
                grid[r, c] = True
            for _ in range(4):
                rr = r + rng.integers(-1, 2)
                cc = c + rng.integers(-1, 2)
                if 0 <= rr < size and 0 <= cc < size:
                    if (rr, cc) != (0, 0) and (rr, cc) != goal:
                        grid[rr, cc] = True
    else:
        width = int(np.ceil(size * density))
        for r in range(size):
            if r % 3 == 0:
                start_col = max(0, r - width + 1)
                end_col = r + 1
                # Keep the start and goal columns traversable.
                if start_col < size // 3 < end_col:
                    if start_col < size // 3:
                        grid[max(0, r - width + 1):size // 3, size // 3] = True
                    if size // 3 + 1 < end_col:
                        grid[size // 3 + 1:r + 1, size // 3] = True
                else:
                    grid[max(0, r - width + 1):r + 1, size // 3] = True

    return grid


def get_benchmark_output_dir(mode: str) -> str:
    """
    Centralized function to ensure ALL benchmark outputs go to the organized directory structure.
    This prevents any hardcoded paths from creating outputs in the wrong places.
    """
    # ALWAYS use the organized benchmarks/results structure
    base_dir = os.path.join("benchmarks", "results", f"benchmark_output_{mode}")
    
    # Create the directory structure if it doesn't exist
    csv_dir = os.path.join(base_dir, 'csv')
    fig_dir = os.path.join(base_dir, 'figures')
    
    for d in (base_dir, csv_dir, fig_dir):
        os.makedirs(d, exist_ok=True)
    
    # Safety check: Ensure we're not accidentally outputting to root
    if os.path.basename(base_dir).startswith("benchmark_output_"):
        print(f"✅ Benchmark output directory: {base_dir}")
    else:
        raise ValueError(f"❌ Invalid benchmark output directory: {base_dir}")
    
    return base_dir


def generate_compiled_results(mode: str, csv_path: str, compiled_path: str = None):
    """
    Generate a Markdown file compiling the CSV summary and all figures for the given mode,
    placing the compiled markdown alongside the CSV and figures directories.
    """
    # Determine directories
    csv_dir = os.path.dirname(csv_path)
    base_dir = os.path.dirname(csv_dir)
    fig_dir = os.path.join(base_dir, 'figures')

    # Decide compiled markdown path alongside csv and figures
    if compiled_path is None:
        compiled_path = os.path.join(base_dir, f"benchmark_compiled_results_{mode}.md")

    # Read CSV into markdown table
    df = pd.read_csv(csv_path)
    table_md = df.to_markdown(index=False)

    # Collect figure files
    patterns = [os.path.join(fig_dir, f"Fig_*_*_{mode}.png"),
                os.path.join(fig_dir, f"Bar_*_*_{mode}.png")]
    figures = []
    for pattern in patterns:
        figures.extend(sorted(glob.glob(pattern)))

    # Write compiled markdown report
    with open(compiled_path, 'w') as f:
        f.write(f"# Benchmark Compiled Results: {mode.title()} Mode\n\n")
        f.write(f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## Summary Table\n\n")
        f.write(table_md + "\n\n")
        f.write("## Figures\n\n")
        for fig in figures:
            fname = os.path.basename(fig)
            rel_path = os.path.join('figures', fname)
            f.write(f"### {fname}\n")
            f.write(f"![{fname}]({rel_path})\n\n")

    print(f"Compiled results saved to {compiled_path}")


def run_all(
    mode: str = "dense",
    show_zoom: bool = True,
    export_csv: bool = True,
    suppress_warnings: bool = True,
    export_compiled_results: bool = True,
    csv_path: str = None,
    compiled_path: str = None,
    seed=None
) -> dict:
    """
    Run benchmarks and optionally export CSV and a compiled markdown results file,
    all organized under mode-specific folders.

    Args:
        seed: RNG seed for the dense obstacle layout. None (default) draws a
            fresh seed per run; pass "paper" or 12345 for the published grids.
            The resolved value is printed and written to the CSV.

    Returns a dict mapping algorithm -> metrics dict.
    """
    if suppress_warnings:
        warnings.filterwarnings('ignore')

    assert mode in ["dense", "sparse"], "Mode must be 'dense' or 'sparse'"

    run_seed = resolve_seed(seed)
    origin = "paper" if run_seed == PAPER_SEED else ("fixed" if seed is not None else "random")
    print(f"🎲 Seed: {run_seed} ({origin})"
          + ("  — sparse mode is deterministic, seed unused" if mode == "sparse" else ""))

    # Setup directories under organized benchmarks structure
    base_dir = os.path.join("benchmarks", "results", f"benchmark_output_{mode}")
    csv_dir = os.path.join(base_dir, 'csv')
    fig_dir = os.path.join(base_dir, 'figures')
    for d in (csv_dir, fig_dir):
        os.makedirs(d, exist_ok=True)

    # Determine CSV output path
    if export_csv and csv_path is None:
        csv_path = os.path.join(csv_dir, f"benchmark_results_{mode}.csv")

    # Grid sizes & density
    sizes = [10, 25, 50, 75, 100] if mode == "dense" else [10, 20, 30, 40, 50]
    time_complexity_factor = 0.001

    # Algorithm registry
    config = {
        "astar": astar_u_heap,
        "astar_quantum": astar_u_quantum,
        "qhr_v2x": qhr_v2x,
        "qhr_v2x_classical": qhr_v2x_classical_baseline,
        "cqw_vectorized": cqw_vectorized,
        "cqw_quantum": cqw_quantum,
        "dijkstra": dijkstra_grid,
        "dijkstra_quantum": dijkstra_grid_quantum,
        "grover_classic": grover_classic,
        "grover_quantum_bfs": grover_quantum_bfs,
    }

    # Initialize results structure
    results = {algo: {"size": [], "msgs": [], "path_len": [], "time": [], "estimated_ms": []}
               for algo in config}

    # Benchmarking loop
    for size in sizes:
        grid = build_grid(size, mode, run_seed)
        dest = (size-1, size-1)

        for name, func in sorted(config.items()):
            total_msgs = total_path = total_time = 0.0
            for row in range(size):
                t0 = time.perf_counter()
                route, msgs = func(grid, (row, 0), dest)
                dt = (time.perf_counter() - t0) * 1000
                total_msgs += msgs
                total_path += max(len(route)-1, 0)
                total_time += dt

            avg_msgs = total_msgs / size
            avg_path = total_path / size
            avg_time = total_time / size
            est_ms = avg_msgs * time_complexity_factor

            res = results[name]
            res["size"].append(size)
            res["msgs"].append(avg_msgs)
            res["path_len"].append(avg_path)
            res["time"].append(avg_time)
            res["estimated_ms"].append(est_ms)

    # Export CSV
    if export_csv:
        rows = []
        for algo, data in results.items():
            for i, sz in enumerate(data["size"]):
                rows.append({
                    "algorithm": algo,
                    "mode": mode,
                    "seed": run_seed,
                    "grid_size": sz,
                    "msgs": data["msgs"][i],
                    "path_len": data["path_len"][i],
                    "time_ms": data["time"][i],
                    "estimated_ms": data["estimated_ms"][i],
                })
        pd.DataFrame(rows).to_csv(csv_path, index=False)
        print(f"Results saved to {csv_path}")

    # Plotting
    metrics = [
        ("msgs", "Route Discovery Messages", 'o', '-'),
        ("path_len", "Average Path Length", 's', '--'),
        ("time", "Discovery Time (ms)", '^', '-.'),
        ("estimated_ms", "Estimated Time (ms)", 'd', ':'),
    ]
    for idx, (key, ylabel, marker, linestyle) in enumerate(metrics, start=1):
        fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
        for algo, data in results.items():
            ax.plot(data['size'], data[key], marker=marker,
                    linestyle=linestyle, linewidth=2, markersize=6,
                    label=algo.replace('_',' ').title())
        ax.set_xlabel("Grid Size")
        ax.set_ylabel(ylabel)
        ax.set_title(f"{ylabel} vs Grid Size ({mode.title()} Mode)")
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize='small')
        plt.tight_layout()
        fig_path = os.path.join(fig_dir, f"Fig_{idx:02d}_{key}_{mode}.png")
        fig.savefig(fig_path, dpi=600)
        plt.close(fig)

    # Bar charts
    algos = list(results.keys())
    x = np.arange(len(sizes))
    width = 0.8 / len(algos)
    for idx, (key, ylabel, _, _) in enumerate(metrics, start=1):
        fig, ax = plt.subplots(figsize=(12, 8), dpi=300)
        for i, algo in enumerate(algos):
            ax.bar(x + i*width, results[algo][key], width=width,
                   label=algo.replace('_',' ').title())
        ax.set_xlabel("Grid Size")
        ax.set_ylabel(ylabel)
        ax.set_title(f"{ylabel} Comparison ({mode.title()} Mode)")
        ax.set_xticks(x + width*(len(algos)-1)/2)
        ax.set_xticklabels(sizes)
        ax.grid(axis='y', linestyle='--', alpha=0.5)
        ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize='small')
        plt.tight_layout()
        bar_path = os.path.join(fig_dir, f"Bar_{idx:02d}_{key}_{mode}.png")
        fig.savefig(bar_path, dpi=600)
        plt.close(fig)

    # Compiled results export
    if export_compiled_results:
        generate_compiled_results(mode, csv_path, compiled_path)

    return results


def run_selected_algorithms(
    algorithms: list,
    mode: str = "dense",
    show_zoom: bool = True,
    export_csv: bool = True,
    suppress_warnings: bool = True,
    export_compiled_results: bool = True,
    csv_path: str = None,
    compiled_path: str = None,
    seed=None
) -> dict:
    """
    Run benchmarks with only selected algorithms.

    Args:
        algorithms: List of algorithm names to test (e.g., ["dijkstra", "astar"])
        mode: "dense" or "sparse"
        seed: RNG seed for the dense obstacle layout. None (default) draws a
            fresh seed per run; pass "paper" or 12345 for the published grids.
            The resolved value is printed and written to the CSV.
        ... (other params same as run_all)
    """
    if suppress_warnings:
        warnings.filterwarnings('ignore')

    assert mode in ["dense", "sparse"], "Mode must be 'dense' or 'sparse'"
    
    # Validate algorithm names
    valid_algorithms = {
        "astar": astar_u_heap,
        "astar_quantum": astar_u_quantum,
        "qhr_v2x": qhr_v2x,
        "qhr_v2x_classical": qhr_v2x_classical_baseline,
        "cqw_vectorized": cqw_vectorized,
        "cqw_quantum": cqw_quantum,
        "dijkstra": dijkstra_grid,
        "dijkstra_quantum": dijkstra_grid_quantum,
        "grover_classic": grover_classic,
        "grover_quantum_bfs": grover_quantum_bfs,
    }
    
    # Filter to only selected algorithms
    selected_config = {name: func for name, func in valid_algorithms.items() 
                      if name in algorithms}
    
    if not selected_config:
        raise ValueError(f"No valid algorithms found. Available: {list(valid_algorithms.keys())}")
    
    run_seed = resolve_seed(seed)
    origin = "paper" if run_seed == PAPER_SEED else ("fixed" if seed is not None else "random")
    print(f"🎯 Running benchmark with selected algorithms: {list(selected_config.keys())}")
    print(f"🎲 Seed: {run_seed} ({origin})"
          + ("  — sparse mode is deterministic, seed unused" if mode == "sparse" else ""))

    # Setup directories under organized benchmarks structure
    base_dir = os.path.join("benchmarks", "results", f"benchmark_output_{mode}")
    csv_dir = os.path.join(base_dir, 'csv')
    fig_dir = os.path.join(base_dir, 'figures')
    for d in (csv_dir, fig_dir):
        os.makedirs(d, exist_ok=True)

    # Determine CSV output path
    if export_csv and csv_path is None:
        csv_path = os.path.join(csv_dir, f"benchmark_results_{mode}_selected.csv")

    # Grid sizes & density
    sizes = [10, 25, 50, 75, 100] if mode == "dense" else [10, 20, 30, 40, 50]
    time_complexity_factor = 0.001

    # Initialize results structure for selected algorithms only
    results = {algo: {"size": [], "msgs": [], "path_len": [], "time": [], "estimated_ms": []}
               for algo in selected_config}

    # Benchmarking loop (same logic as run_all but with selected_config)
    for size in sizes:
        grid = build_grid(size, mode, run_seed)
        dest = (size-1, size-1)

        for name, func in sorted(selected_config.items()):
            total_msgs = total_path = total_time = 0.0
            for row in range(size):
                t0 = time.perf_counter()
                route, msgs = func(grid, (row, 0), dest)
                dt = (time.perf_counter() - t0) * 1000
                total_msgs += msgs
                total_path += max(len(route)-1, 0)
                total_time += dt

            avg_msgs = total_msgs / size
            avg_path = total_path / size
            avg_time = total_time / size
            est_ms = avg_msgs * time_complexity_factor

            res = results[name]
            res["size"].append(size)
            res["msgs"].append(avg_msgs)
            res["path_len"].append(avg_path)
            res["time"].append(avg_time)
            res["estimated_ms"].append(est_ms)

    # Export CSV
    if export_csv:
        rows = []
        for algo, data in results.items():
            for i, sz in enumerate(data["size"]):
                rows.append({
                    "algorithm": algo,
                    "mode": mode,
                    "seed": run_seed,
                    "grid_size": sz,
                    "msgs": data["msgs"][i],
                    "path_len": data["path_len"][i],
                    "time_ms": data["time"][i],
                    "estimated_ms": data["estimated_ms"][i],
                })
        pd.DataFrame(rows).to_csv(csv_path, index=False)
        print(f"Results saved to {csv_path}")

    # Plotting (same as run_all but with selected algorithms)
    metrics = [
        ("msgs", "Route Discovery Messages", 'o', '-'),
        ("path_len", "Average Path Length", 's', '--'),
        ("time", "Discovery Time (ms)", '^', '-.'),
        ("estimated_ms", "Estimated Time (ms)", 'd', ':'),
    ]
    for idx, (key, ylabel, marker, linestyle) in enumerate(metrics, start=1):
        fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
        for algo, data in results.items():
            ax.plot(data['size'], data[key], marker=marker,
                    linestyle=linestyle, linewidth=2, markersize=6,
                    label=algo.replace('_',' ').title())
        ax.set_xlabel("Grid Size")
        ax.set_ylabel(ylabel)
        ax.set_title(f"{ylabel} vs Grid Size ({mode.title()} Mode) - Selected Algorithms")
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize='small')
        plt.tight_layout()
        fig_path = os.path.join(fig_dir, f"Fig_{idx:02d}_{key}_{mode}_selected.png")
        fig.savefig(fig_path, dpi=600)
        plt.close(fig)

    # Bar charts
    algos = list(results.keys())
    x = np.arange(len(sizes))
    width = 0.8 / len(algos)
    for idx, (key, ylabel, _, _) in enumerate(metrics, start=1):
        fig, ax = plt.subplots(figsize=(12, 8), dpi=300)
        for i, algo in enumerate(algos):
            ax.bar(x + i*width, results[algo][key], width=width,
                   label=algo.replace('_',' ').title())
        ax.set_xlabel("Grid Size")
        ax.set_ylabel(ylabel)
        ax.set_title(f"{ylabel} Comparison ({mode.title()} Mode) - Selected Algorithms")
        ax.set_xticks(x + width*(len(algos)-1)/2)
        ax.set_xticklabels(sizes)
        ax.grid(axis='y', linestyle='--', alpha=0.5)
        ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize='small')
        plt.tight_layout()
        bar_path = os.path.join(fig_dir, f"Bar_{idx:02d}_{key}_{mode}_selected.png")
        fig.savefig(bar_path, dpi=600)
        plt.close(fig)

    # Compiled results export
    if export_compiled_results:
        generate_compiled_results(mode, csv_path, compiled_path)

    return results


if __name__ == "__main__":
    print("🚀 Starting Pathfinding Algorithm Benchmark...")
    print("=" * 50)
    
    # Run dense mode benchmark
    print("\n📊 Running Dense Mode Benchmark...")
    try:
        results_dense = run_all(mode="dense", export_csv=True, export_compiled_results=True)
        print("✅ Dense mode benchmark completed successfully!")
    except Exception as e:
        print(f"❌ Dense mode benchmark failed: {e}")
    
    # Run sparse mode benchmark
    print("\n📊 Running Sparse Mode Benchmark...")
    try:
        results_sparse = run_all(mode="sparse", export_csv=True, export_compiled_results=True)
        print("✅ Sparse mode benchmark completed successfully!")
    except Exception as e:
        print(f"❌ Sparse mode benchmark failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 All benchmarks completed!")
    print("📁 Check the 'benchmarks/results/benchmark_output_dense' and 'benchmarks/results/benchmark_output_sparse' directories for results.")
