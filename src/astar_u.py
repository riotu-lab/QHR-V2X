import heapq
from typing import List, Tuple

import numpy as np

def astar_u_heap(
    input_map: np.ndarray,  # True = obstacle
    start_coords: Tuple[int, int],
    dest_coords: Tuple[int, int],
) -> Tuple[List[Tuple[int, int]], int]:
    """
    A* on a 4-neighbor grid using a binary heap (Manhattan heuristic).

    Returns (path, num_expanded), where num_expanded counts heap pops.
    """
    rows, cols = input_map.shape
    # Validate inputs
    for pt in (start_coords, dest_coords):
        r, c = pt
        if not (0 <= r < rows and 0 <= c < cols):
            raise ValueError(f"Coordinate {pt} out of bounds")
        if input_map[r, c]:  # obstacle
            return [], 0

    # Local helpers and constants
    def idx(r: int, c: int) -> int:
        return r * cols + c
    def rc(i: int) -> Tuple[int, int]:
        return divmod(i, cols)
    shifts = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    dest_r, dest_c = dest_coords

    start = idx(*start_coords)
    dest  = idx(*dest_coords)

    # Pure-Python storage for performance
    INF = float('inf')
    dist    = [INF] * (rows * cols)
    parent  = [-1]  * (rows * cols)
    visited = [False] * (rows * cols)

    dist[start] = 0.0

    # Priority queue of (f_score, node)
    frontier = []
    # initial heuristic
    start_h = abs(start_coords[0] - dest_r) + abs(start_coords[1] - dest_c)
    heapq.heappush(frontier, (start_h, start))

    num_expanded = 0

    # Heuristic function closing over dest_r, dest_c
    def h(i: int) -> float:
        r, c = rc(i)
        return abs(r - dest_r) + abs(c - dest_c)

    while frontier:
        f, u = heapq.heappop(frontier)
        # count this pop as expansion
        num_expanded += 1
        # goal check (includes counting the goal pop)
        if u == dest:
            break
        # skip if already visited
        if visited[u]:
            continue

        visited[u] = True
        ur, uc = rc(u)

        # relax neighbors
        g_u = dist[u]
        for dr, dc in shifts:
            nr, nc = ur + dr, uc + dc
            if not (0 <= nr < rows and 0 <= nc < cols):
                continue
            if input_map[nr, nc]:
                continue
            v = idx(nr, nc)
            if visited[v]:
                continue
            g_v = g_u + 1
            if g_v < dist[v]:
                dist[v] = g_v
                parent[v] = u
                heapq.heappush(frontier, (g_v + h(v), v))

    # Reconstruct path
    path: List[Tuple[int, int]] = []
    if dist[dest] < INF:
        cur = dest
        while cur != -1:
            path.append(rc(cur))
            cur = parent[cur]
        path.reverse()

    return path, num_expanded
