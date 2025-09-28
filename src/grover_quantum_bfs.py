from __future__ import annotations

import functools
from collections import deque
from math import ceil, log2
from typing import List, Tuple

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

# Module‑level simulator instance (reuse across calls)
_BACKEND = AerSimulator()

# Quantum‑only goal finder plus classical BFS connector
MAX_Q_FRONTIER = 16  # threshold for Grover use (illustrative)


def _bfs(grid: np.ndarray, start: Tuple[int, int], goal: Tuple[int, int]) -> Tuple[List[Tuple[int, int]], int]:
    """Classical BFS to stitch path from start to goal."""
    R, C = grid.shape
    # Early obstacle guard
    if grid[goal]:
        return [], 0

    q = deque([start])
    parent: dict[Tuple[int,int], Tuple[int,int] | None] = {start: None}
    nbrs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    expanded = 0

    while q:
        r, c = q.popleft()
        expanded += 1
        if (r, c) == goal:
            path: List[Tuple[int, int]] = []
            node = goal
            while node is not None:
                path.append(node)
                node = parent[node]
            return path[::-1], expanded

        for dr, dc in nbrs:
            nr, nc = r + dr, c + dc
            if 0 <= nr < R and 0 <= nc < C and not grid[nr, nc]:
                nxt = (nr, nc)
                if nxt not in parent:
                    parent[nxt] = (r, c)
                    q.append(nxt)

    return [], expanded  # unreachable


@functools.lru_cache(maxsize=8)
def _get_transpiled_grover(n_qubits: int, dest_bits: Tuple[int, ...]) -> QuantumCircuit:
    """
    Build and transpile the Grover circuit for a single marked item defined by dest_bits.
    Caches up to 8 recent circuits.
    """
    qc = QuantumCircuit(n_qubits)
    qc.h(range(n_qubits))

    # Phase oracle for target index
    for i, b in enumerate(dest_bits):
        if b == 0:
            qc.x(i)
    qc.h(n_qubits - 1)
    qc.mcx(list(range(n_qubits - 1)), n_qubits - 1)
    qc.h(n_qubits - 1)
    for i, b in enumerate(dest_bits):
        if b == 0:
            qc.x(i)

    # Diffusion operator
    qc.h(range(n_qubits))
    qc.x(range(n_qubits))
    qc.h(n_qubits - 1)
    qc.mcx(list(range(n_qubits - 1)), n_qubits - 1)
    qc.h(n_qubits - 1)
    qc.x(range(n_qubits))
    qc.h(range(n_qubits))

    qc.measure_all()
    return transpile(qc, _BACKEND)


def grover_quantum_bfs(
    grid: np.ndarray,
    start: Tuple[int, int],
    dest: Tuple[int, int],
    *,
    shots: int = 32,
) -> Tuple[List[Tuple[int, int]], int]:
    """Return (route, expanded) compatible with the benchmark harness.

    - route: list from start to dest (empty if unreachable)
    - expanded: shots + bfs_expanded
    """
    nrows, ncols = grid.shape

    # Validate coordinates and obstacles
    for pt in (start, dest):
        r, c = pt
        if not (0 <= r < nrows and 0 <= c < ncols):
            raise ValueError(f"Coordinate {pt} out of bounds")
        if grid[r, c]:
            return [], shots

    N = nrows * ncols
    dest_idx = np.ravel_multi_index(dest, (nrows, ncols))
    n_qubits = ceil(log2(N))

    # Qubit capacity guard
    if n_qubits > _BACKEND.configuration().n_qubits:
        return [], shots

    # Prepare Grover circuit and run
    dest_bits = tuple((dest_idx >> i) & 1 for i in range(n_qubits))
    qc = _get_transpiled_grover(n_qubits, dest_bits)
    res = _BACKEND.run(qc, shots=shots).result()

    # Efficient count parsing
    counts = {
        idx: cnt
        for bitstr, cnt in res.get_counts().items()
        for idx in (int(bitstr.replace(" ",""), 2),)
        if idx < N
    }
    if not counts:
        return [], shots

    measured_idx = max(counts, key=counts.get)
    measured_coord = divmod(measured_idx, ncols)

    # Stitch path via BFS
    path, bfs_expanded = _bfs(grid, start, measured_coord)

    # Final check: must reach actual dest
    if not path or measured_coord != dest:
        return [], shots + bfs_expanded

    return path, shots + bfs_expanded
