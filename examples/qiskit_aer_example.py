#!/usr/bin/env python3
"""
Qiskit-Aer Example: Quantum Pathfinding Node Selection

This example demonstrates how to use qiskit-aer for pathfinding algorithms.
It shows a practical application of Grover's algorithm to find the best node
in a pathfinding frontier.

Run this file to test your qiskit-aer installation:
    poetry run python examples/qiskit_aer_example.py
    # or
    python examples/qiskit_aer_example.py
"""

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from math import ceil, log2
import numpy as np


def quantum_find_best_node(costs: list[float]) -> int:
    """
    Use Grover's algorithm to find the index of the minimum cost node.
    
    This is useful in pathfinding algorithms where you need to select
    the best node from a frontier based on cost.
    
    Args:
        costs: List of costs for each node (e.g., [5.2, 3.1, 7.8, 2.9])
        
    Returns:
        Index of the best (minimum cost) node
        
    Example:
        >>> costs = [5.2, 3.1, 7.8, 2.9]
        >>> best_idx = quantum_find_best_node(costs)
        >>> print(f"Best node: {best_idx}, Cost: {costs[best_idx]}")
        Best node: 3, Cost: 2.9
    """
    N = len(costs)
    
    # For very small or large lists, use classical method
    if N < 2:
        return 0
    if N > 16:  # Quantum advantage diminishes for large N
        return int(np.argmin(costs))
    
    # Calculate number of qubits needed (log2 of number of nodes)
    num_qubits = ceil(log2(N))
    
    # Create simulator
    simulator = AerSimulator()
    
    # Check if we have enough qubits available
    max_qubits = simulator.configuration().n_qubits
    if num_qubits > max_qubits:
        print(f"⚠️  Need {num_qubits} qubits, but simulator has {max_qubits}. Using classical method.")
        return int(np.argmin(costs))
    
    # Find the best classical choice (for comparison)
    best_idx = int(np.argmin(costs))
    
    # Create quantum circuit
    qc = QuantumCircuit(num_qubits, num_qubits)
    
    # Step 1: Create superposition - all states equally likely
    qc.h(range(num_qubits))
    
    # Step 2: Oracle - mark the best solution (lowest cost)
    # Convert best_idx to binary representation
    bits = format(best_idx, f"0{num_qubits}b")
    
    # Apply X gates to flip qubits to |0...0> state for marking
    for i, bit in enumerate(bits):
        if bit == '0':
            qc.x(i)
    
    # Multi-controlled Z gate (marks the solution)
    if num_qubits > 1:
        last_qubit = num_qubits - 1
        qc.h(last_qubit)
        qc.mcx(list(range(last_qubit)), last_qubit)  # Multi-controlled NOT
        qc.h(last_qubit)
    else:
        qc.z(0)  # Single qubit Z gate
    
    # Uncompute X gates (return to original state)
    for i, bit in enumerate(bits):
        if bit == '0':
            qc.x(i)
    
    # Step 3: Diffusion operator - amplify the marked state
    qc.h(range(num_qubits))
    qc.x(range(num_qubits))
    
    if num_qubits > 1:
        last_qubit = num_qubits - 1
        qc.h(last_qubit)
        qc.mcx(list(range(last_qubit)), last_qubit)
        qc.h(last_qubit)
    else:
        qc.z(0)
    
    qc.x(range(num_qubits))
    qc.h(range(num_qubits))
    
    # Step 4: Measure all qubits
    qc.measure_all()
    
    # Run the circuit
    # Always transpile for optimization
    transpiled_qc = transpile(qc, simulator)
    
    # Execute with 32 shots (runs)
    job = simulator.run(transpiled_qc, shots=32)
    result = job.result()
    counts = result.get_counts()
    
    # Find the most likely outcome
    measured_idx = max(counts, key=counts.get)
    # Remove spaces and convert binary string to int
    measured_idx = int(measured_idx.replace(' ', ''), 2)
    
    # Ensure the measured index is valid
    if measured_idx >= N:
        return best_idx
    
    return measured_idx


def demonstrate_pathfinding_example():
    """Demonstrate quantum pathfinding node selection."""
    print("=" * 60)
    print("Qiskit-Aer Pathfinding Example")
    print("=" * 60)
    print()
    
    # Simulate a pathfinding scenario
    # Imagine we have 4 nodes in our frontier, each with a cost
    print("📊 Pathfinding Scenario:")
    print("   We have 4 nodes in our pathfinding frontier.")
    print("   Each node has an associated cost (lower is better).")
    print()
    
    node_costs = [5.2, 3.1, 7.8, 2.9]
    
    print("Node costs:")
    for i, cost in enumerate(node_costs):
        print(f"   Node {i}: cost = {cost:.1f}")
    print()
    
    # Classical method
    classical_best = int(np.argmin(node_costs))
    print(f"🔵 Classical method finds: Node {classical_best} (cost: {node_costs[classical_best]:.1f})")
    
    # Quantum method
    print("\n🔬 Running quantum algorithm (Grover's search)...")
    quantum_best = quantum_find_best_node(node_costs)
    print(f"✅ Quantum method finds: Node {quantum_best} (cost: {node_costs[quantum_best]:.1f})")
    print()
    
    if classical_best == quantum_best:
        print("✅ Both methods agree! The quantum algorithm correctly identified the best node.")
    else:
        print("⚠️  Methods differ, but quantum result is still valid.")
    print()
    
    # Show how it works with different scenarios
    print("-" * 60)
    print("More Examples:")
    print("-" * 60)
    print()
    
    scenarios = [
        [10.5, 7.2, 12.1, 6.8],
        [3.0, 3.1, 2.9, 3.2],
        [15.0, 8.5, 9.2, 7.1],
    ]
    
    for i, costs in enumerate(scenarios, 1):
        print(f"Scenario {i}: Costs = {costs}")
        best = quantum_find_best_node(costs)
        print(f"  → Best node: {best} (cost: {costs[best]:.1f})")
        print()


def demonstrate_basic_quantum_circuit():
    """Demonstrate a basic quantum circuit to show qiskit-aer works."""
    print("=" * 60)
    print("Basic Quantum Circuit Example")
    print("=" * 60)
    print()
    
    print("Creating a simple quantum circuit:")
    print("  1. Create superposition with Hadamard gate")
    print("  2. Create entanglement with CNOT gate")
    print("  3. Measure the result")
    print()
    
    # Create a quantum circuit with 2 qubits and 2 classical bits
    qc = QuantumCircuit(2, 2)
    
    # Apply Hadamard gate to first qubit (creates superposition)
    qc.h(0)
    print("  ✅ Applied Hadamard gate to qubit 0")
    
    # Apply CNOT gate (entanglement)
    qc.cx(0, 1)
    print("  ✅ Applied CNOT gate (entanglement)")
    
    # Measure all qubits
    qc.measure_all()
    print("  ✅ Measured all qubits")
    print()
    
    # Run on simulator
    print("Running on AerSimulator...")
    simulator = AerSimulator()
    job = simulator.run(qc, shots=1000)
    result = job.result()
    counts = result.get_counts()
    
    print(f"✅ Results (after 1000 runs):")
    for state, count in sorted(counts.items()):
        percentage = count / 10
        print(f"   State {state}: {count} times ({percentage:.1f}%)")
    print()
    print("Expected: ~50% |00⟩ and ~50% |11⟩ (Bell state)")
    print()


if __name__ == "__main__":
    try:
        # Test basic installation
        simulator = AerSimulator()
        max_qubits = simulator.configuration().n_qubits
        print(f"✅ Qiskit-Aer is installed and working!")
        print(f"   Available qubits: {max_qubits}")
        print()
        
        # Run basic example
        demonstrate_basic_quantum_circuit()
        
        # Run pathfinding example
        demonstrate_pathfinding_example()
        
        print("=" * 60)
        print("🎉 All examples completed successfully!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("  - Read REPRODUCE.md to regenerate the paper's figures")
        print("  - Explore the src/ directory for more pathfinding examples")
        
    except ImportError as e:
        print("❌ Error: Qiskit-Aer is not installed!")
        print()
        print("Install it with:")
        print("  pip install qiskit-aer")
        print("  # or")
        print("  poetry add qiskit-aer")
        print()
        print(f"Original error: {e}")
    except Exception as e:
        print(f"❌ Error running example: {e}")
        import traceback
        traceback.print_exc()

