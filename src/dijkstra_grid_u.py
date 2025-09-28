import heapq
import numpy as np
from typing import List, Tuple

def dijkstra_grid(
    input_map: np.ndarray,  # True = obstacle
    start_coords: Tuple[int, int],
    dest_coords: Tuple[int, int],
) -> Tuple[List[Tuple[int, int]], int]:
    """Classical Dijkstra on a 4-neighbor unit-cost grid.

    Returns (path, num_expanded) where num_expanded counts frontier pops.
    """
    rows, cols = input_map.shape
    # Validate inputs
    for pt in (start_coords, dest_coords):
        r, c = pt
        if not (0 <= r < rows and 0 <= c < cols):
            raise ValueError(f"Coordinate {pt} out of bounds")
        if input_map[r, c]:
            return [], 0

    # Local helpers and constants
    def idx(r: int, c: int) -> int:
        return r * cols + c
    def rc(i: int) -> Tuple[int, int]:
        return divmod(i, cols)
    shifts = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    start = idx(*start_coords)
    dest  = idx(*dest_coords)

    # Pure-Python lists for performance
    INF = float('inf')
    dist    = [INF] * (rows * cols)
    parent  = [-1]  * (rows * cols)
    visited = [False]* (rows * cols)

    dist[start] = 0

    # Frontier heap: (distance, node)
    frontier = [(0, start)]
    num_expanded = 0

    while frontier:
        d, u = heapq.heappop(frontier)
        # skip outdated
        if d != dist[u]:
            continue
        # count this pop as expansion
        num_expanded += 1
        # early exit including goal pop
        if u == dest:
            break

        # relax neighbors
        ur, uc = rc(u)
        for dr, dc in shifts:
            nr, nc = ur + dr, uc + dc
            if 0 <= nr < rows and 0 <= nc < cols and not input_map[nr, nc]:
                v = idx(nr, nc)
                if visited[v]:
                    continue
                nd = d + 1
                if nd < dist[v]:
                    dist[v] = nd
                    parent[v] = u
                    heapq.heappush(frontier, (nd, v))
        visited[u] = True

    # Reconstruct path
    path: List[Tuple[int, int]] = []
    if dist[dest] < INF:
        cur = dest
        while cur != -1:
            path.append(rc(cur))
            cur = parent[cur]
        path.reverse()

    return path, num_expanded