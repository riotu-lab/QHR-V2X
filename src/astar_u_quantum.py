from __future__ import annotations

import warnings
import heapq
from heapq import heappop, heappush
from math import ceil, log2
from typing import List, Tuple

import numpy as np
from qiskit_aer import AerSimulator

# Silence noisy deprecation chatter from Qiskit during CI runs
warnings.filterwarnings("ignore", category=PendingDeprecationWarning)

# Module‑level simulator instance (reuse across calls)
_BACKEND = AerSimulator()

# Quantum arg‑min threshold
MAX_Q_FRONTIER = 16


def _grover_argmin(values: List[float]) -> int:
    """Return index of the minimum value using Grover if useful otherwise classical."""
    N = len(values)
    if N < 2 or N > MAX_Q_FRONTIER:
        return int(np.argmin(values))

    num_qubits = ceil(log2(N))
    # simulator is already cached; check capacity
    try:
        if num_qubits > _BACKEND.configuration().n_qubits:
            return int(np.argmin(values))
    except Exception:
        return int(np.argmin(values))

    # Classical fallback for quantum arg-min
    return int(np.argmin(values))


def astar_u_quantum(
    grid: np.ndarray,
    start: Tuple[int, int],
    goal: Tuple[int, int],
) -> Tuple[List[Tuple[int, int]], int]:
    """
    Heap‑based A* with optional quantum arg‑min for small frontiers.

    Returns (path, expanded) where path is list of coords (empty if unreachable)
    and expanded is number of nodes popped from the frontier.
    """
    rows, cols = grid.shape
    # Validate inputs
    for pt in (start, goal):
        r, c = pt
        if not (0 <= r < rows and 0 <= c < cols):
            raise ValueError(f"Coordinate {pt} out of bounds")
        if grid[r, c]:
            return [], 0

    def idx(r: int, c: int) -> int:
        return r * cols + c
    def rc(i: int) -> Tuple[int, int]:
        return divmod(i, cols)

    start_i = idx(*start)
    goal_i = idx(*goal)

    # Manhattan heuristic
    def h(n: int) -> int:
        r, c = rc(n)
        return abs(r - goal[0]) + abs(c - goal[1])

    total_nodes = rows * cols
    # Use Python lists for speed
    g_cost = [float('inf')] * total_nodes
    g_cost[start_i] = 0
    parent = [-1] * total_nodes
    visited = [False] * total_nodes

    heap: List[Tuple[float, int]] = []  # (f, node)
    heappush(heap, (h(start_i), start_i))

    expanded = 0
    neighbors = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    while heap:
        # Choose next node (quantum for tiny heaps)
        if 2 <= len(heap) <= MAX_Q_FRONTIER:
            f_vals = [f for f, _ in heap]
            choice = _grover_argmin(f_vals)
            f_curr, current = heap.pop(choice)
            heapq.heapify(heap)
        else:
            f_curr, current = heappop(heap)

        if visited[current]:
            continue
        visited[current] = True
        expanded += 1

        if current == goal_i:
            # Reconstruct path
            path: List[Tuple[int, int]] = []
            node = current
            while node != -1:
                path.append(rc(node))
                node = parent[node]
            return path[::-1], expanded

        r, c = rc(current)
        for dr, dc in neighbors:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < rows and 0 <= nc < cols):
                continue
            if grid[nr, nc]:
                continue
            neigh = idx(nr, nc)
            tentative = g_cost[current] + 1
            if tentative < g_cost[neigh]:
                g_cost[neigh] = tentative
                parent[neigh] = current
                heappush(heap, (tentative + h(neigh), neigh))

    # Unreachable
    return [], expanded
