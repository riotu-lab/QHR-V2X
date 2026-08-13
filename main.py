#!/usr/bin/env python3
"""
Pathfinding Algorithm Comparison Project
======================================

A comprehensive comparison of classical and quantum-enhanced pathfinding algorithms.

Usage:
    poetry run python main.py [command] [options]

Commands:
    demo          Run interactive demo
    test          Test basic algorithms (Dijkstra + A*)
    quantum       Test quantum algorithms
    benchmark     Run full benchmarking (all algorithms)
    selective     Run benchmark with selected algorithms
    compare       Compare specific algorithms
    help          Show this help message

Examples:
    poetry run python main.py test                    # Test basic algorithms
    poetry run python main.py quantum                 # Test quantum algorithms
    poetry run python main.py benchmark               # Run full benchmark
    poetry run python main.py selective dijkstra astar astar_quantum  # Selective benchmark
    poetry run python main.py compare dijkstra dijkstra_quantum       # Compare algorithms

This CLI is for exploring the algorithms interactively. The paper's figures come
from `make figures SEED=paper` -- see REPRODUCE.md.
"""

import sys
import argparse
import time
import numpy as np
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import algorithms
from dijkstra_grid_u import dijkstra_grid
from astar_u import astar_u_heap
from astar_u_quantum import astar_u_quantum
from dijkstra_quantum_enhanced import dijkstra_grid_quantum
from cqw_quantum import cqw_quantum
from cqw_vectorized import cqw_vectorized
from grover_classic import grover_classic
from grover_quantum_bfs import grover_quantum_bfs
from qhr_v2x import qhr_v2x, qhr_v2x_classical_baseline

# Algorithm registry
ALGORITHMS = {
    "dijkstra": ("Dijkstra's Algorithm (Classical)", dijkstra_grid),
    "astar": ("A* Search (Classical)", astar_u_heap),
    "astar_quantum": ("A* Search (Quantum)", astar_u_quantum),
    "dijkstra_quantum": ("Dijkstra (Quantum)", dijkstra_grid_quantum),
    "qhr_v2x": ("QHR-V2X (Quantum-Heuristic Routing)", qhr_v2x),
    "qhr_v2x_classical": ("QHR-V2X Classical Baseline", qhr_v2x_classical_baseline),
    "cqw_quantum": ("Continuous Quantum Walk", cqw_quantum),
    "cqw_vectorized": ("Vectorized CQW", cqw_vectorized),
    "grover_classic": ("Grover Classic", grover_classic),
    "grover_quantum_bfs": ("Quantum Grover BFS", grover_quantum_bfs)
}

def create_test_grid(size=5, density=0.3):
    """Create a test grid with obstacles."""
    grid = np.zeros((size, size), dtype=bool)
    
    # Add random obstacles
    rng = np.random.default_rng(42)  # Fixed seed for reproducibility
    num_obstacles = int(size * size * density)
    
    for _ in range(num_obstacles):
        r, c = rng.integers(size), rng.integers(size)
        # Don't block start (0,0) or goal (size-1, size-1)
        if (r, c) != (0, 0) and (r, c) != (size-1, size-1):
            grid[r, c] = True
    
    return grid

def print_grid(grid, path=None):
    """Print the grid with path visualization."""
    size = len(grid)
    print(f"Grid size: {size}x{size}")
    print("Grid layout (S=start, G=goal, █=obstacle, .=free, *=path):")
    
    for r in range(size):
        row = ""
        for c in range(size):
            if (r, c) == (0, 0):
                row += "S "
            elif (r, c) == (size-1, size-1):
                row += "G "
            elif path and (r, c) in path:
                row += "* "
            elif grid[r, c]:
                row += "█ "
            else:
                row += ". "
        print(row)

def test_algorithm(algorithm_name, grid, start, goal):
    """Test a single algorithm."""
    if algorithm_name not in ALGORITHMS:
        print(f"❌ Unknown algorithm: {algorithm_name}")
        return None
    
    name, func = ALGORITHMS[algorithm_name]
    print(f"\n🔍 Testing {name}...")
    
    try:
        start_time = time.perf_counter()
        path, messages = func(grid, start, goal)
        end_time = time.perf_counter()
        
        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        if path:
            print(f"✅ {name}: Path found! Length: {len(path)-1}, Messages: {messages}, Time: {execution_time:.3f}ms")
            print(f"   Path: {path}")
            return {
                "algorithm": algorithm_name,
                "path_length": len(path) - 1,
                "messages": messages,
                "time_ms": execution_time,
                "path": path
            }
        else:
            print(f"❌ {name}: No path found")
            return None
            
    except Exception as e:
        print(f"❌ {name}: Error - {e}")
        return None

def run_demo():
    """Run an interactive demo."""
    print("🚀 Pathfinding Algorithm Demo")
    print("=" * 50)
    
    # Create a simple test grid
    grid = create_test_grid(5, 0.3)
    start = (0, 0)
    goal = (4, 4)
    
    print_grid(grid)
    
    # Test basic algorithms
    results = []
    for algo in ["dijkstra", "astar"]:
        result = test_algorithm(algo, grid, start, goal)
        if result:
            results.append(result)
    
    # Show comparison
    if results:
        print("\n📊 Demo Results Summary:")
        print(f"{'Algorithm':<20} {'Path Length':<12} {'Messages':<10} {'Time (ms)':<10}")
        print("-" * 55)
        for result in results:
            print(f"{result['algorithm']:<20} {result['path_length']:<12} {result['messages']:<10} {result['time_ms']:<10.3f}")

def run_basic_test():
    """Test basic algorithms (Dijkstra + A*)."""
    print("🧪 Testing Basic Algorithms")
    print("=" * 50)
    
    grid = create_test_grid(5, 0.3)
    start = (0, 0)
    goal = (4, 4)
    
    print_grid(grid)
    
    results = []
    for algo in ["dijkstra", "astar"]:
        result = test_algorithm(algo, grid, start, goal)
        if result:
            results.append(result)
    
    if results:
        print("\n📊 Basic Test Results:")
        print(f"{'Algorithm':<20} {'Path Length':<12} {'Messages':<10} {'Time (ms)':<10}")
        print("-" * 55)
        for result in results:
            print(f"{result['algorithm']:<20} {result['path_length']:<12} {result['messages']:<10} {result['time_ms']:<10.3f}")

def run_quantum_test():
    """Test quantum algorithms."""
    print("🔬 Testing Quantum Algorithms")
    print("=" * 50)
    
    grid = create_test_grid(4, 0.25)  # Smaller grid for quantum algorithms
    start = (0, 0)
    goal = (3, 3)
    
    print_grid(grid)
    
    results = []
    quantum_algorithms = ["grover_classic", "cqw_vectorized", "dijkstra_quantum"]
    
    for algo in quantum_algorithms:
        result = test_algorithm(algo, grid, start, goal)
        if result:
            results.append(result)
    
    if results:
        print("\n📊 Quantum Test Results:")
        print(f"{'Algorithm':<25} {'Path Length':<12} {'Messages':<10} {'Time (ms)':<10}")
        print("-" * 60)
        for result in results:
            print(f"{result['algorithm']:<25} {result['path_length']:<12} {result['messages']:<10} {result['time_ms']:<10.3f}")

def run_benchmark():
    """Run full benchmarking suite."""
    print("📊 Running Full Benchmark Suite")
    print("=" * 50)
    
    try:
        from tests.test_pathfinding_all import run_all
        print("Running dense mode benchmark...")
        run_all(mode="dense", export_csv=True, export_compiled_results=True)
        print("✅ Dense mode completed")
        
        print("Running sparse mode benchmark...")
        run_all(mode="sparse", export_csv=True, export_compiled_results=True)
        print("✅ Sparse mode completed")
        
        print("\n🎉 All benchmarks completed!")
        print("📁 Results saved in benchmarks/results/ directory")
        
    except ImportError as e:
        print(f"❌ Error importing benchmark: {e}")

def run_selective_benchmark(algorithms):
    """Run benchmark with selected algorithms."""
    print(f"🎯 Running Selective Benchmark: {', '.join(algorithms)}")
    print("=" * 50)
    
    try:
        from tests.test_pathfinding_all import run_selected_algorithms
        
        # Run dense mode
        print("Running dense mode benchmark...")
        run_selected_algorithms(
            algorithms=algorithms,
            mode="dense",
            export_csv=True,
            export_compiled_results=True
        )
        print("✅ Dense mode completed")
        
        # Run sparse mode
        print("Running sparse mode benchmark...")
        run_selected_algorithms(
            algorithms=algorithms,
            mode="sparse",
            export_csv=True,
            export_compiled_results=True
        )
        print("✅ Sparse mode completed")
        
        print("\n🎉 Selective benchmark completed!")
        print("📁 Results saved in benchmarks/results/ directory")
        
    except ImportError as e:
        print(f"❌ Error importing benchmark: {e}")

def run_compare(algorithms):
    """Compare specific algorithms side by side."""
    print(f"⚖️ Comparing Algorithms: {', '.join(algorithms)}")
    print("=" * 50)
    
    # Create test grid
    grid = create_test_grid(6, 0.3)
    start = (0, 0)
    goal = (5, 5)
    
    print_grid(grid)
    
    results = []
    for algo in algorithms:
        result = test_algorithm(algo, grid, start, goal)
        if result:
            results.append(result)
    
    if results:
        print("\n📊 Comparison Results:")
        print(f"{'Algorithm':<25} {'Path Length':<12} {'Messages':<10} {'Time (ms)':<10}")
        print("-" * 60)
        for result in results:
            print(f"{result['algorithm']:<25} {result['path_length']:<12} {result['messages']:<10} {result['time_ms']:<10.3f}")
        
        # Find best performer
        if results:
            best_time = min(results, key=lambda x: x['time_ms'])
            best_messages = min(results, key=lambda x: x['messages'])
            print("\n🏆 Best Performance:")
            print(f"   Fastest: {best_time['algorithm']} ({best_time['time_ms']:.3f}ms)")
            print(f"   Most Efficient: {best_messages['algorithm']} ({best_messages['messages']} messages)")

def show_help():
    """Show detailed help information."""
    print(__doc__)
    print("\n📁 Project Structure:")
    print("   src/           - Algorithm implementations")
    print("   tests/         - Test and benchmark scripts")
    print("   experiments/   - Reproduction pipeline and figures")
    print("   benchmarks/    - Benchmark results and outputs (generated)")
    print("   pyproject.toml - Poetry configuration and dependencies")
    print("   main.py        - Optional CLI entry point")

    print("\n🔧 Available Algorithms:")
    for name, (description, _) in ALGORITHMS.items():
        print(f"   {name:<20} - {description}")
    
    print("\n🎯 Examples:")
    print("   poetry run python main.py test")
    print("   poetry run python main.py quantum")
    print("   poetry run python main.py benchmark")
    print("   poetry run python main.py selective dijkstra astar astar_quantum")
    print("   poetry run python main.py compare dijkstra dijkstra_quantum")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Pathfinding Algorithm Comparison Project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "command",
        nargs="?",
        default="help",
        choices=["demo", "test", "quantum", "benchmark", "selective", "compare", "help"],
        help="Command to run"
    )
    
    parser.add_argument(
        "algorithms",
        nargs="*",
        help="Algorithm names for selective/compare commands"
    )
    
    args = parser.parse_args()
    
    # Execute command
    if args.command == "demo":
        run_demo()
    elif args.command == "test":
        run_basic_test()
    elif args.command == "quantum":
        run_quantum_test()
    elif args.command == "benchmark":
        run_benchmark()
    elif args.command == "selective":
        if not args.algorithms:
            print("❌ Please specify algorithms to test")
            print("Example: python main.py selective dijkstra astar astar_quantum")
            return
        run_selective_benchmark(args.algorithms)
    elif args.command == "compare":
        if len(args.algorithms) < 2:
            print("❌ Please specify at least 2 algorithms to compare")
            print("Example: python main.py compare dijkstra dijkstra_quantum")
            return
        run_compare(args.algorithms)
    else:
        show_help()

if __name__ == "__main__":
    main()
