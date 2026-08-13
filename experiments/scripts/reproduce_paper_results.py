#!/usr/bin/env python3
"""
Reproduce Paper Results Script
==============================

This script reproduces the exact experimental results from the QHR-V2X paper:
"QHR-V2X: A Quantum-Heuristic Routing Framework for Efficient V2X Path Discovery"

Usage:
    python experiments/scripts/reproduce_paper_results.py [--algorithms ALG1,ALG2] [--output-dir DIR]

Examples:
    # Reproduce all paper results
    python experiments/scripts/reproduce_paper_results.py
    
    # Reproduce specific algorithms only
    python experiments/scripts/reproduce_paper_results.py --algorithms qhr_v2x,dijkstra,astar
    
    # Custom output directory
    python experiments/scripts/reproduce_paper_results.py --output-dir experiments/results/paper_reproduction
"""

import sys
import argparse
import time
import warnings
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import benchmarking functions
from tests.test_pathfinding_all import run_selected_algorithms

def main():
    parser = argparse.ArgumentParser(
        description="Reproduce QHR-V2X paper experimental results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "--algorithms",
        type=str,
        default="qhr_v2x,qhr_v2x_classical,dijkstra,astar",
        help="Comma-separated list of algorithms to test (default: qhr_v2x,qhr_v2x_classical,dijkstra,astar)"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="experiments/results/paper_reproduction",
        help="Output directory for results (default: experiments/results/paper_reproduction)"
    )
    
    parser.add_argument(
        "--seed",
        type=str,
        default=None,
        help="RNG seed for the dense obstacle layout. Omit (the default) to draw a "
             "fresh seed each run; pass 'paper' for the seed behind the published "
             "figures, or any integer to replay a specific run. The seed used is "
             "printed and written to the results CSV. Sparse mode is deterministic "
             "by construction, so the seed does not affect it."
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

    args = parser.parse_args()

    # "paper" and "random" pass through as strings; anything else numeric is an int.
    seed = args.seed
    if seed is not None and seed not in ("paper", "random"):
        try:
            seed = int(seed)
        except ValueError:
            parser.error(f"--seed must be an integer, 'paper', or 'random' (got {seed!r})")
    
    # Parse algorithms
    algorithms = [alg.strip() for alg in args.algorithms.split(",")]
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("🔬 QHR-V2X Paper Results Reproduction")
    print("=" * 50)
    print(f"📊 Algorithms: {', '.join(algorithms)}")
    print(f"📁 Output directory: {output_dir}")
    print(f"🎲 Seed: {'fresh per run (default)' if seed is None else seed}")
    print(f"🕐 Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Suppress warnings for cleaner output
    if not args.verbose:
        warnings.filterwarnings('ignore')
    
    results = {}
    
    # Experiment 1: Dense Environment (40% obstacle density)
    print("📊 Experiment 1: Dense Environment (40% obstacles)")
    print("-" * 50)
    dense_results = run_selected_algorithms(
        algorithms=algorithms,
        mode="dense",
        export_csv=True,
        export_compiled_results=True,
        suppress_warnings=True,
        seed=seed
    )
    
    # Move results to experiment directory
    dense_csv = project_root / "benchmarks/results/benchmark_output_dense/csv/benchmark_results_dense_selected.csv"
    if dense_csv.exists():
        import shutil
        shutil.copy2(dense_csv, output_dir / "dense_results.csv")
    
    results["dense"] = dense_results
    print("✅ Dense environment completed")
    print()
    
    # Experiment 2: Sparse Environment (20% obstacle density)
    print("📊 Experiment 2: Sparse Environment (20% obstacles)")
    print("-" * 50)
    sparse_results = run_selected_algorithms(
        algorithms=algorithms,
        mode="sparse",
        export_csv=True,
        export_compiled_results=True,
        suppress_warnings=True,
        seed=seed
    )
    
    # Move results to experiment directory
    sparse_csv = project_root / "benchmarks/results/benchmark_output_sparse/csv/benchmark_results_sparse_selected.csv"
    if sparse_csv.exists():
        import shutil
        shutil.copy2(sparse_csv, output_dir / "sparse_results.csv")
    
    results["sparse"] = sparse_results
    print("✅ Sparse environment completed")
    print()
    
    # Generate summary report
    print("📋 Generating Summary Report")
    print("-" * 50)
    generate_summary_report(results, output_dir, algorithms)
    
    print("🎉 Paper reproduction completed!")
    print(f"📁 Results saved to: {output_dir}")
    print(f"🕐 Completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}")


def generate_summary_report(results, output_dir, algorithms):
    """Generate a summary report of the experimental results."""
    
    report_path = output_dir / "experiment_summary.md"
    
    with open(report_path, 'w') as f:
        f.write("# QHR-V2X Paper Reproduction Results\n\n")
        f.write(f"**Generated on**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Algorithms tested**: {', '.join(algorithms)}\n\n")
        
        f.write("## Experimental Setup\n\n")
        f.write("- **Grid sizes**: 10×10, 20×20, 30×30, 40×40, 50×50 (sparse) / 10×10, 25×25, 50×50, 75×75, 100×100 (dense)\n")
        f.write("- **Obstacle densities**: 20% (sparse), 40% (dense)\n")
        f.write("- **Performance metrics**: Route Discovery Time (RDT), Route Discovery Messages (RDM), Path Length (PL)\n")
        f.write("- **Simulation environment**: Python 3.11 + Qiskit\n\n")
        
        f.write("## Results Summary\n\n")
        
        for mode, mode_results in results.items():
            f.write(f"### {mode.title()} Environment Results\n\n")
            
            if mode_results:
                # Calculate average performance metrics
                for algo_name, algo_results in mode_results.items():
                    if algo_results and 'msgs' in algo_results:
                        avg_messages = sum(algo_results['msgs']) / len(algo_results['msgs'])
                        avg_path_len = sum(algo_results['path_len']) / len(algo_results['path_len'])
                        avg_time = sum(algo_results['time']) / len(algo_results['time'])
                        
                        f.write(f"**{algo_name}**:\n")
                        f.write(f"- Average RDM: {avg_messages:.2f}\n")
                        f.write(f"- Average PL: {avg_path_len:.2f}\n")
                        f.write(f"- Average RDT: {avg_time:.3f} ms\n\n")
            
            f.write("\n")
        
        f.write("## Files Generated\n\n")
        f.write("- `dense_results.csv`: Dense environment results\n")
        f.write("- `sparse_results.csv`: Sparse environment results\n")
        f.write("- `experiment_summary.md`: This summary report\n")
        f.write("- `figures/`: Generated visualization plots\n\n")
        
        f.write("## Reproducibility\n\n")
        f.write("To reproduce these results:\n\n")
        f.write("```bash\n")
        f.write("python experiments/scripts/reproduce_paper_results.py\n")
        f.write("```\n\n")
        f.write("For detailed analysis and visualization:\n\n")
        f.write("```bash\n")
        f.write("python experiments/analysis/analyze_results.py\n")
        f.write("```\n")


if __name__ == "__main__":
    main()
