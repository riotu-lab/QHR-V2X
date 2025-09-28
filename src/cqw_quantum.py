from __future__ import annotations
import os
import logging
import heapq
import hashlib
from typing import List, Tuple, Optional, Dict
import functools

import numpy as np
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, transpile
from qiskit.circuit.library import PermutationGate
from qiskit_aer import AerSimulator
from qiskit.exceptions import QiskitError

# Default resources (override via env‑var)
_DEFAULT_MAX_QPOS = int(os.getenv("CQW_MAX_QPOS", "20"))    # max pos qubits
_DEFAULT_SHOT_CAP = int(os.getenv("CQW_SHOT_CAP", "256"))   # max simulator shots

# Logger
_logger = logging.getLogger(__name__)
_logger.setLevel(os.getenv("CQW_LOG_LEVEL", "WARNING").upper())

# Backend
_BACKEND = AerSimulator()

@functools.lru_cache(maxsize=16)
def _get_transpiled_body(
    mapping_hash: str,
    n_pos: int,
    dir_maps: Tuple[Optional[Tuple[int, ...]], ...],
    num_steps: int,
    reflect: bool,
) -> QuantumCircuit:
    """Builds & caches the walk circuit body based on map fingerprint."""
    n_coin = 2
    base_reflect = PermutationGate([1, 0, 3, 2])
    qr_coin = QuantumRegister(n_coin, name="coin")
    qr_pos  = QuantumRegister(n_pos, name="pos")
    cr_pos  = ClassicalRegister(n_pos, name="creg")
    body = QuantumCircuit(qr_coin, qr_pos, cr_pos)

    for _ in range(num_steps):
        body.h(qr_coin)
        for state, mapping in enumerate(dir_maps):
            if mapping is None:
                if not reflect:
                    continue
                gate = base_reflect.control(num_ctrl_qubits=n_coin, ctrl_state=state)
            else:
                gate = PermutationGate(list(mapping)).control(
                    num_ctrl_qubits=n_coin, ctrl_state=state
                )
            body.append(gate, qr_coin[:] + qr_pos[:])
        body.barrier()

    body.measure(qr_pos, cr_pos)
    return transpile(body, _BACKEND)


def _astar_count(
    grid: np.ndarray,
    start: Tuple[int, int],
    goal: Tuple[int, int],
) -> Tuple[List[Tuple[int, int]], int]:
    """A* that returns (path, expansions) in O(N log N)."""
    R, C = grid.shape
    if grid[start] or grid[goal]:
        raise ValueError("Start or goal on obstacle")
    h = lambda r, c: abs(r - goal[0]) + abs(c - goal[1])
    g: Dict[Tuple[int,int], int] = {start: 0}
    f: Dict[Tuple[int,int], int] = {start: h(*start)}
    parent: Dict[Tuple[int,int], Tuple[int,int]] = {}
    visited: set[Tuple[int,int]] = set()
    heap: List[Tuple[int, Tuple[int,int]]] = []
    heapq.heappush(heap, (f[start], start))
    nbrs = ((1,0),(-1,0),(0,1),(0,-1))
    expansions = 0

    while heap:
        _, current = heapq.heappop(heap)
        if current in visited:
            continue
        visited.add(current)
        expansions += 1
        if current == goal:
            path = [current]
            while current in parent:
                current = parent[current]
                path.append(current)
            return path[::-1], expansions
        r, c = current
        for dr, dc in nbrs:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < R and 0 <= nc < C) or grid[nr,nc]:
                continue
            tg = g[current] + 1
            nbr = (nr,nc)
            if tg < g.get(nbr, float('inf')):
                parent[nbr] = current
                g[nbr] = tg
                f_val = tg + h(nr,nc)
                heapq.heappush(heap, (f_val, nbr))
                f[nbr] = f_val
    raise ValueError("Goal unreachable")


def cqw_quantum(
    input_map: np.ndarray,
    start_coords: Tuple[int, int],
    dest_coords: Tuple[int, int],
    *,
    num_steps: int = 6,
    shots: int = 2048,
    max_qubits: Optional[int] = None,
    shot_cap: Optional[int] = None,
    reflect: bool = False,
    logger: Optional[logging.Logger] = None,
) -> Tuple[List[Tuple[int, int]], int]:
    log = logger or _logger

    # Validate coordinates
    rows, cols = input_map.shape
    for coord in (start_coords, dest_coords):
        r,c = coord
        if not (0 <= r < rows and 0 <= c < cols):
            raise ValueError(f"Coordinate {coord} out of bounds")

    # Obstacle fallback
    if input_map[start_coords] or input_map[dest_coords]:
        log.warning("Start or goal on obstacle; immediate fallback.")
        try:
            return _astar_count(input_map, start_coords, dest_coords)
        except ValueError:
            return [], 0

    # Trivial
    if start_coords == dest_coords:
        return [start_coords], 0

    # Shots & qubit guard
    shots = max(1, min(shots, shot_cap or _DEFAULT_SHOT_CAP))
    nrows, ncols = rows, cols
    N = nrows * ncols
    idx = lambda r,c: r * ncols + c
    rc  = lambda f: divmod(f, ncols)
    s = idx(*start_coords)
    n_pos = int(np.ceil(np.log2(N)))

    if n_pos > (max_qubits or _DEFAULT_MAX_QPOS):
        log.warning("CQW skipped: %d qubits > threshold", n_pos)
        try:
            return _astar_count(input_map, start_coords, dest_coords)
        except ValueError:
            return [], 0

    # Build & fingerprint mappings
    dir_maps: List[Optional[Tuple[int,...]]] = []
    for state in range(4):
        mapping = list(range(N))
        for p in range(N):
            r,c = rc(p)
            if input_map[r,c]:
                continue
            if state==0 and r>0: mapping[p]=idx(r-1,c)
            elif state==1 and r<nrows-1: mapping[p]=idx(r+1,c)
            elif state==2 and c>0: mapping[p]=idx(r,c-1)
            elif state==3 and c<ncols-1: mapping[p]=idx(r,c+1)
        dir_maps.append(tuple(mapping) if len(set(mapping))==N else None)

    # Fingerprint based on packed input_map
    mapping_hash = hashlib.sha256(np.packbits(input_map).tobytes()).hexdigest()

    # Build circuit
    qr_coin = QuantumRegister(2, name="coin")
    qr_pos  = QuantumRegister(n_pos, name="pos")
    cr_pos  = ClassicalRegister(n_pos, name="creg")
    qc = QuantumCircuit(qr_coin, qr_pos, cr_pos)

    for i, bit in enumerate(reversed(f"{s:0{n_pos}b}")): 
        if bit=='1': qc.x(qr_pos[i])

    body = _get_transpiled_body(
        mapping_hash, n_pos, tuple(dir_maps), num_steps, reflect
    )
    qc = qc.compose(body, front=False)

    try:
        result = _BACKEND.run(qc, shots=shots).result()
        counts = result.get_counts()
        end_flat = int(max(counts, key=counts.get).replace(" ",""), 2)
        measured = rc(end_flat)
        return [start_coords, measured], shots

    except QiskitError as exc:
        log.warning("CQW failed (%s); using A*.", exc)
        try:
            return _astar_count(input_map, start_coords, dest_coords)
        except ValueError:
            return [], 0

# Alias
cqw = cqw_quantum
