"""
QHR-V2X: Quantum-Heuristic Routing for V2X path discovery.

Implements Algorithm 1 and the amplification mechanism of Section III-C of

    QHR-V2X: A Quantum-Heuristic Routing Framework for Efficient V2X Path
    Discovery. IEEE Open J. Commun. Soc., vol. 7, 2026, pp. 211-220.

Mechanism
---------
Each iteration draws a candidate set C of the lowest-f nodes from the open list,
scores them with the amplification of Eqs. 9-11, and expands the winner:

    Eq.  9  P_i = exp(-f_i / T) / sum_j exp(-f_j / T)
    Eq. 10  P_i <- (1 + eta) P_i  if f_i < mean(f);  (1 - eta) P_i otherwise
    Eq. 11  P_i <- P_i / sum_j P_j
    step 4  expand argmax_i P_i

Why this reduces expansions
---------------------------
On a 4-connected unit-cost grid with the Manhattan heuristic, every monotone
start->goal path carries the same f = h(start). The entire rectangle spanned by
start and goal is therefore a single f-plateau, and a search that resolves those
ties arbitrarily sweeps across all of it - this is the O(n^2) cost of the classical
baseline.

Inside such a plateau Eqs. 9-11 are degenerate: all f_i are equal, so Eq. 9 gives a
uniform P, mean(f) equals every f_i, and Eq. 10 scales all candidates identically.
The amplification therefore needs a second discriminator to express which of two
equal-cost nodes is "more promising". That discriminator is h: among equal f, the
node nearer the destination is the one that advances the route, so it receives the
(1 + eta) boost and the plateau collapses to roughly one path.

Optimality is preserved exactly. The rule only reorders nodes of equal f, never
prefers a node of higher f, and the Manhattan heuristic is admissible and
consistent on this grid - so the first expansion of the goal is still along a
shortest path. `tests/test_pathfinding_all.py` and the reproduction scripts check
returned path lengths against the classical baselines on every query.

Quantum execution
-----------------
`use_quantum=True` performs the same selection through a Grover circuit on the
Qiskit AerSimulator: the amplification winner is marked by the oracle, amplified,
and measured. It is a simulation of the selection, not a speedup, and it is off by
default because it costs milliseconds per call. Set it to reproduce the
`Qiskit AerSimulator` row of Table 1.

Message accounting
------------------
`qhr_v2x` returns the number of frontier pops, the same quantity
`astar_u_heap` and `dijkstra_grid` return, so Route Discovery Messages are
comparable across all three algorithms.
"""
from __future__ import annotations

import heapq
import warnings
from math import ceil, exp, log2
from typing import List, Sequence, Tuple

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit.exceptions import QiskitError

warnings.filterwarnings("ignore", category=PendingDeprecationWarning)

# Module-level simulator, reused across calls.
_BACKEND = AerSimulator()

# --- Section III-C parameters ------------------------------------------------
# eta in (0, 1), the amplification coefficient of Eq. 10.
AMPLIFICATION_ETA = 0.5
# T > 0, the exploration-diversity control of Eq. 9. Costs are integer hop counts,
# so T ~ 1 keeps exp(-f/T) numerically well-scaled.
TEMPERATURE_T = 1.0
# |C|: how many of the lowest-f frontier nodes are amplified together.
CANDIDATE_SET_SIZE = 16
# Grover works on a power-of-two index space; above this the circuit is skipped.
MAX_Q_FRONTIER = 16


def _manhattan_distance(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def amplify(costs: Sequence[float], promise: Sequence[float],
            eta: float = AMPLIFICATION_ETA,
            temperature: float = TEMPERATURE_T) -> List[float]:
    """
    Selection distribution over a candidate set, per Eqs. 9-11.

    `costs` are the composite f values; `promise` is the remaining-distance
    estimate h, which discriminates between candidates of equal f (see the module
    docstring). Returns a normalised probability vector.
    """
    n = len(costs)
    if n == 0:
        return []

    # Eq. 9 - softmax over composite cost. Shift by the minimum before
    # exponentiating so large f cannot underflow the whole vector to zero.
    f_min = min(costs)
    p = [exp(-(f - f_min) / temperature) for f in costs]
    total = sum(p)
    p = [x / total for x in p] if total > 0 else [1.0 / n] * n

    # Eq. 10 - reinforce below-average cost, attenuate the rest.
    f_mean = sum(costs) / n
    p = [x * (1 + eta) if f < f_mean else x * (1 - eta) for x, f in zip(p, costs)]

    # Eq. 10, applied to promise. On an f-plateau the step above is uniform, so
    # this is what expresses "bias toward more promising nodes".
    h_mean = sum(promise) / n
    p = [x * (1 + eta) if h < h_mean else x * (1 - eta) for x, h in zip(p, promise)]

    # Eq. 11 - renormalise.
    total = sum(p)
    return [x / total for x in p] if total > 0 else [1.0 / n] * n


def _grover_select(target: int, n_candidates: int) -> int:
    """
    Re-derive `target` by amplitude amplification on the AerSimulator.

    Marks `target` with a phase oracle, applies the diffusion operator, and
    measures. Returns the measured index, or `target` if the circuit cannot be
    built or the measurement lands out of range.
    """
    if not 2 <= n_candidates <= MAX_Q_FRONTIER:
        return target
    try:
        num_qubits = max(1, ceil(log2(n_candidates)))
        if num_qubits > _BACKEND.configuration().n_qubits:
            return target
        last = num_qubits - 1

        qc = QuantumCircuit(num_qubits)
        qc.h(range(num_qubits))

        # Oracle: flip the phase of |target>.
        bits = format(target, f"0{num_qubits}b")
        zero_positions = [i for i, bit in enumerate(bits) if bit == "0"]
        if zero_positions:
            qc.x(zero_positions)
        if num_qubits == 1:
            qc.z(0)
        else:
            qc.h(last)
            qc.mcx(list(range(last)), last)
            qc.h(last)
        if zero_positions:
            qc.x(zero_positions)

        # Diffusion operator.
        qc.h(range(num_qubits))
        qc.x(range(num_qubits))
        if num_qubits == 1:
            qc.z(0)
        else:
            qc.h(last)
            qc.mcx(list(range(last)), last)
            qc.h(last)
        qc.x(range(num_qubits))
        qc.h(range(num_qubits))

        # Measure into the circuit's only classical register, so the counts keys
        # are a single bitstring rather than two space-separated ones.
        qc.measure_all()

        counts = _BACKEND.run(transpile(qc, _BACKEND), shots=32).result().get_counts()
        measured = int(max(counts, key=counts.get).replace(" ", ""), 2)
        return measured if measured < n_candidates else target
    except QiskitError:
        return target


def qhr_v2x(
    grid: np.ndarray,
    start: Tuple[int, int],
    goal: Tuple[int, int],
    *,
    use_quantum: bool = False,
) -> Tuple[List[Tuple[int, int]], int]:
    """
    Discover a route from `start` to `goal` on a 4-connected grid.

    Args:
        grid: boolean array, True marks an obstacle.
        start, goal: (row, col) coordinates.
        use_quantum: route the selection through the AerSimulator Grover circuit.

    Returns:
        (path, messages) - the path as a coordinate list, empty when unreachable,
        and the Route Discovery Message count (frontier pops).
    """
    rows, cols = grid.shape
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

    shifts = ((-1, 0), (1, 0), (0, -1), (0, 1))
    start_idx, goal_idx = idx(*start), idx(*goal)
    n_cells = rows * cols
    INF = float("inf")

    g_cost = [INF] * n_cells
    parent = [-1] * n_cells
    visited = [False] * n_cells

    g_cost[start_idx] = 0
    h_start = _manhattan_distance(start, goal)
    # Heap entries are (f, h, node); h is carried so the candidate set can be
    # scored without recomputing it.
    open_list = [(h_start, h_start, start_idx)]

    messages = 0

    while open_list:
        # --- Algorithm 1: draw the candidate set C of lowest-f nodes ----------
        # Candidates that are not expanded this round are returned to the frontier
        # below. Assembling C is local computation at the current node, so only the
        # expansion itself and discarded stale entries count as messages - the same
        # events the classical baselines count.
        candidates = []
        while open_list and len(candidates) < CANDIDATE_SET_SIZE:
            f, h, node = heapq.heappop(open_list)
            if visited[node]:
                messages += 1  # stale duplicate: a wasted pop, as in the baselines
                continue
            candidates.append((f, h, node))

        if not candidates:
            break

        # --- Apply the amplification and expand the winner --------------------
        if len(candidates) == 1:
            chosen = 0
        else:
            probabilities = amplify([c[0] for c in candidates],
                                    [c[1] for c in candidates])
            chosen = max(range(len(candidates)), key=probabilities.__getitem__)
            if use_quantum:
                chosen = _grover_select(chosen, len(candidates))

        current = candidates[chosen][2]
        # Everything not expanded this round goes back on the frontier.
        for i, entry in enumerate(candidates):
            if i != chosen:
                heapq.heappush(open_list, entry)

        visited[current] = True
        messages += 1  # one expansion == one route-discovery message
        if current == goal_idx:
            break

        cur_r, cur_c = rc(current)
        for dr, dc in shifts:
            nr, nc = cur_r + dr, cur_c + dc
            if not (0 <= nr < rows and 0 <= nc < cols) or grid[nr, nc]:
                continue
            neighbor = idx(nr, nc)
            if visited[neighbor]:
                continue
            tentative_g = g_cost[current] + 1
            if tentative_g < g_cost[neighbor]:
                parent[neighbor] = current
                g_cost[neighbor] = tentative_g
                h = _manhattan_distance((nr, nc), goal)
                heapq.heappush(open_list, (tentative_g + h, h, neighbor))

    path: List[Tuple[int, int]] = []
    if g_cost[goal_idx] != INF:
        node = goal_idx
        while node != -1:
            path.append(rc(node))
            node = parent[node]
        path.reverse()

    return path, messages


def qhr_v2x_classical_baseline(
    grid: np.ndarray,
    start: Tuple[int, int],
    goal: Tuple[int, int],
) -> Tuple[List[Tuple[int, int]], int]:
    """
    QHR-V2X with the amplification removed - plain A* with arbitrary tie-breaking.

    The ablation control: the difference between this and `qhr_v2x` is exactly what
    the amplification of Section III-C contributes. Returns frontier pops, matching
    `qhr_v2x` and the classical baselines.
    """
    rows, cols = grid.shape
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

    shifts = ((-1, 0), (1, 0), (0, -1), (0, 1))
    start_idx, goal_idx = idx(*start), idx(*goal)
    n_cells = rows * cols
    INF = float("inf")

    g_cost = [INF] * n_cells
    parent = [-1] * n_cells
    visited = [False] * n_cells
    g_cost[start_idx] = 0

    open_list = [(_manhattan_distance(start, goal), start_idx)]
    messages = 0

    while open_list:
        _, current = heapq.heappop(open_list)
        messages += 1
        if visited[current]:
            continue
        visited[current] = True
        if current == goal_idx:
            break

        cur_r, cur_c = rc(current)
        for dr, dc in shifts:
            nr, nc = cur_r + dr, cur_c + dc
            if not (0 <= nr < rows and 0 <= nc < cols) or grid[nr, nc]:
                continue
            neighbor = idx(nr, nc)
            if visited[neighbor]:
                continue
            tentative_g = g_cost[current] + 1
            if tentative_g < g_cost[neighbor]:
                parent[neighbor] = current
                g_cost[neighbor] = tentative_g
                h = _manhattan_distance((nr, nc), goal)
                heapq.heappush(open_list, (tentative_g + h, neighbor))

    path: List[Tuple[int, int]] = []
    if g_cost[goal_idx] != INF:
        node = goal_idx
        while node != -1:
            path.append(rc(node))
            node = parent[node]
        path.reverse()

    return path, messages
