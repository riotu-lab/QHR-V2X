import numpy as np
from collections import deque
from typing import List, Tuple


def _bfs_route(grid: np.ndarray, start: Tuple[int,int], dest: Tuple[int,int]) -> Tuple[List[Tuple[int,int]], int]:
    """Efficient BFS stitching using parent pointers."""
    nrows, ncols = grid.shape
    # Early obstacle guard
    if grid[dest]:
        return [], 0

    idx = lambda r, c: r * ncols + c
    rc  = lambda i: divmod(i, ncols)

    total = nrows * ncols
    visited = [False] * total
    parent = [-1] * total

    s = idx(*start)
    d = idx(*dest)
    visited[s] = True
    dq = deque([s])
    expansions = 0

    while dq:
        u = dq.popleft()
        expansions += 1
        if u == d:
            break
        r, c = rc(u)
        for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < nrows and 0 <= nc < ncols and not grid[nr, nc]:
                v = idx(nr, nc)
                if not visited[v]:
                    visited[v] = True
                    parent[v] = u
                    dq.append(v)

    # Reconstruct path
    if not visited[d]:
        return [], expansions
    path = []
    cur = d
    while cur != -1:
        path.append(rc(cur))
        if cur == s:
            break
        cur = parent[cur]
    return path[::-1], expansions


def grover_classic(
    grid: np.ndarray,
    start: Tuple[int, int],
    dest: Tuple[int, int],
    *,
    shots: int = 5,
    seed: int = 42,
) -> Tuple[List[Tuple[int, int]], int]:
    """
    Simulated Grover: uniform random guesses + BFS stitch on success.
    Returns (route, nexp) where nexp = shots + BFS expansions.
    """
    nrows, ncols = grid.shape
    # Validate inputs
    for pt in (start, dest):
        r, c = pt
        if not (0 <= r < nrows and 0 <= c < ncols):
            raise ValueError(f"Coordinate {pt} out of bounds")
        if grid[r, c]:
            return [], 0

    N = nrows * ncols
    dest_idx = np.ravel_multi_index(dest, (nrows, ncols))

    # Seeded RNG for reproducibility
    rng = np.random.default_rng(seed)
    guesses = rng.choice(N, size=shots)

    # Count distinct outcomes? No: use total shots for SDM
    nexp = shots

    counts = {}
    for g in guesses:
        counts[g] = counts.get(g, 0) + 1

    measured = max(counts, key=counts.get)

    if measured == dest_idx:
        route, bfs_exp = _bfs_route(grid, start, dest)
        nexp += bfs_exp
    else:
        route = [start]

    return route, nexp
