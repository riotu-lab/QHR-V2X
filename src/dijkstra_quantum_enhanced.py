from __future__ import annotations

import functools
from heapq import heappop, heappush, heapify
from math import ceil, log2
from typing import List, Tuple

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

# ---------------------------------------------------------------------------
# Global backend and template/oracle caches
# ---------------------------------------------------------------------------

_BACKEND = AerSimulator()
_MAX_Q   = _BACKEND.configuration().n_qubits
_SHOTS   = 8
_MAX_Q_HEAP = 8

@functools.lru_cache(maxsize=32)
def _cached_full_grover(q: int, target_idx: int) -> QuantumCircuit:
    """Returns a transpiled Grover circuit for given qubit count and target."""
    # Build oracle
    oc = QuantumCircuit(q, name="oracle")
    bits = format(target_idx, f"0{q}b")[::-1]
    for i, b in enumerate(bits):
        if b == '0': oc.x(i)
    if q > 1:
        oc.mcx(list(range(q-1)), q-1)
    else:
        oc.z(0)
    for i, b in enumerate(bits):
        if b == '0': oc.x(i)

    # Build template
    tpl = QuantumCircuit(q, q, name="grover_tpl")
    tpl.h(range(q))
    # diffusion
    tpl.h(range(q))
    tpl.x(range(q))
    tpl.h(q-1)
    tpl.mcx(list(range(q-1)), q-1)
    tpl.h(q-1)
    tpl.x(range(q))
    tpl.h(range(q))
    tpl.measure(range(q), range(q))

    # Compose and transpile
    full = oc.compose(tpl, qubits=range(q))
    return transpile(full, _BACKEND)

# ---------------------------------------------------------------------------
# Hybrid Dijkstra on a unit-cost grid with occasional Grover pop
# ---------------------------------------------------------------------------

def dijkstra_grid_quantum(
    grid: np.ndarray,  # True = obstacle
    start: Tuple[int, int],
    goal: Tuple[int, int],
) -> Tuple[List[Tuple[int, int]], int]:
    # Validate inputs
    rows, cols = grid.shape
    for pt in (start, goal):
        r, c = pt
        if not (0 <= r < rows and 0 <= c < cols):
            raise ValueError(f"Coordinate {pt} out of bounds")
        if grid[r, c]:
            return [], 0

    # Localize helpers and constants
    idx = lambda r, c: r * cols + c
    rc  = lambda i: divmod(i, cols)
    shifts = [(-1,0),(1,0),(0,-1),(0,1)]
    MAX_Q_HEAP = _MAX_Q_HEAP
    SHOTS = _SHOTS
    MAX_Q = _MAX_Q

    s = idx(*start)
    g = idx(*goal)
    if s == g:
        return [start], 0

    BIG = 2**31 - 1
    # Pure-Python lists for speed
    dist = [BIG] * (rows * cols)
    parent = [-1] * (rows * cols)
    dist[s] = 0

    # Heap and parallel cost list for quick access
    heap: List[Tuple[int,int]] = [(0, s)]
    costs = [0]
    nexp = 0

    while heap:
        k = len(heap)
        # choose pop method
        if 2 <= k <= MAX_Q_HEAP:
            # quantum arg-min on costs
            q = ceil(log2(k))
            if 2 <= q <= MAX_Q:
                # fetch transpiled circuit
                full = _cached_full_grover(q, int(np.argmin(costs)))
                counts = _BACKEND.run(full, shots=SHOTS).result().get_counts()
                valid = {int(s.replace(' ','') ,2):v for s,v in counts.items() if int(s,2) < k}
                choice = max(valid, key=valid.get) if valid else int(np.argmin(costs))
            else:
                choice = int(np.argmin(costs))
            cost, u = heap.pop(choice)
            costs.pop(choice)
            heapify(heap)
        else:
            cost, u = heappop(heap)
            costs.pop(0)

        # skip outdated
        if cost != dist[u]:
            continue
        nexp += 1
        if u == g:
            break

        ur, uc = rc(u)
        for dr, dc in shifts:
            nr, nc = ur+dr, uc+dc
            if 0 <= nr < rows and 0 <= nc < cols and not grid[nr,nc]:
                v = idx(nr, nc)
                alt = cost + 1
                if alt < dist[v]:
                    dist[v] = alt
                    parent[v] = u
                    heappush(heap, (alt, v))
                    costs.append(alt)

    # Reconstruct path
    route: List[Tuple[int,int]] = []
    if dist[g] != BIG:
        node = g
        while node != -1:
            route.append(rc(node))
            node = parent[node]
        route.reverse()

    return route, nexp
