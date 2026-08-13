from __future__ import annotations

from collections import deque
from typing import List, Tuple

import numpy as np

################################################################################
# Grover coin (4×4)
################################################################################
GROVER_COIN = (np.array([[-1, 1, 1, 1],
                        [1, -1, 1, 1],
                        [1, 1, -1, 1],
                        [1, 1, 1, -1]], dtype=np.complex128) / 2.0)

# Coin index constants
UP, DOWN, LEFT, RIGHT = range(4)

# Reflection shifts for vectorized roll
SHIFTS = {
    UP:    (-1, 0),
    DOWN:  (1, 0),
    LEFT:  (0, -1),
    RIGHT: (0, 1),
}

################################################################################
# BFS helper (deque, safe reconstruction)
################################################################################

def _bfs(grid: np.ndarray, start: Tuple[int, int], goal: Tuple[int, int]) -> Tuple[List[Tuple[int, int]], int]:
    """Obstacle‑aware BFS. Returns (path, expanded)."""
    if grid[goal]:
        return [], 0

    R, C = grid.shape
    q = deque([start])
    parent: dict[Tuple[int, int], Tuple[int, int] | None] = {start: None}
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

    return [], expanded

################################################################################
# Main CQW driver (vectorized)
################################################################################

def cqw_vectorized(
    input_map: np.ndarray,
    start: Tuple[int, int],
    dest: Tuple[int, int],
    *,
    num_steps: int = 60,
    measure_every: int = 10,
    prob_thresh: float = 1e-3,
) -> Tuple[List[Tuple[int, int]], int]:
    """Vectorised CQW with periodic measurement and final BFS stitch.

    Returns (route, expanded) where expanded counts measurement events.
    """
    R, C = input_map.shape
    # Validate inputs
    for pt in (start, dest):
        r, c = pt
        if not (0 <= r < R and 0 <= c < C):
            raise ValueError(f"Coordinate {pt} out of bounds")
        if input_map[r, c]:
            return [], 0

    # Precompute coin operator transpose for tensordot
    coin_op = GROVER_COIN.T
    # Pre-allocate position arrays
    pos = np.zeros((R, C, 4), dtype=np.complex128)
    pos[start] = 0.5
    pos_next = np.empty_like(pos)

    route: List[Tuple[int, int]] = [start]
    expanded = 0

    for t in range(1, num_steps + 1):
        # Grover coin via tensordot to avoid reshapes
        pos = np.tensordot(pos, coin_op, axes=([2], [0]))  # result shape (R, C, 4)

        # Vectorised shift with reflection
        pos_next.fill(0)
        for dir_idx, (dr, dc) in SHIFTS.items():
            shifted = np.roll(pos[..., dir_idx], shift=(dr, dc), axis=(0, 1))
            # normal move
            slc_src = (slice(max(-dr, 0), min(R, R - dr)), slice(max(-dc, 0), min(C, C - dc)))
            slc_dst = (slice(max(dr, 0), min(R, R + dr)), slice(max(dc, 0), min(C, C + dc)))
            pos_next[slc_dst + (dir_idx,)] += shifted[slc_src]
            # reflection at obstacles and boundaries
            mask = np.zeros((R, C), bool)
            mask[slc_dst] = input_map[slc_dst]
            pos_next[..., dir_idx][mask] += -shifted[...,][mask]

        pos = pos_next

        # Periodic measurement
        if t % measure_every == 0:
            probs = np.sum(np.abs(pos) ** 2, axis=2)
            cell = tuple(map(int, np.unravel_index(np.argmax(probs), (R, C))))
            route.append(cell)
            # count each measurement as one SDM event
            expanded += 1
            if cell == dest:
                break

    # Final BFS stitch if necessary
    if route[-1] != dest:
        bfs_path, bfs_exp = _bfs(input_map, route[-1], dest)
        expanded += bfs_exp
        if bfs_path:
            route.extend(bfs_path[1:])
        else:
            return [], expanded

    return route, expanded
