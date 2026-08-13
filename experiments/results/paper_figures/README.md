# Paper Figures 3–8 — as-published configuration

Committed so the figures can be viewed without running anything. Regenerated with:

```bash
make figures SEED=paper
```

`SEED=paper` selects the obstacle layout behind the published figures. Add
`STYLE=curved` for the paper's smooth line style; those land beside these with a
`_curved` suffix and are not tracked. Every point is a live algorithm run — see
[REPRODUCE.md](../../../REPRODUCE.md).

## Configuration

These come from the `tests/` benchmark harness, the configuration that produced the
published values.

| | |
| --- | --- |
| Obstacle density | `int(size × density)` obstacle seeds → **1.56–12.00%** realised (nominal 40% dense, 20% sparse) |
| Seeds | one layout per grid size |
| Endpoints | each row of the left column → bottom-right corner, averaged |
| Implementations | `src/astar_u.py`, `src/dijkstra_grid_u.py`, `src/qhr_v2x.py` |

**The realised density is not the density Table 1 states.** The obstacle count grows
linearly while the cell count grows quadratically, so coverage falls as the grid
grows. These figures are kept because they are the configuration under which the
published A* and Dijkstra values reproduce exactly.

## Files

| File | Paper figure |
| --- | --- |
| `Figure_3_estimated_ms_dense.png` | Fig. 3 — Estimated RDT, 40% obstacle density |
| `Figure_4_msgs_dense.png` | Fig. 4 — RDM, 40% obstacle density |
| `Figure_5_path_len_dense.png` | Fig. 5 — PL, 40% obstacle density |
| `Figure_6_estimated_ms_sparse.png` | Fig. 6 — Estimated RDT, 20% obstacle density |
| `Figure_7_msgs_sparse.png` | Fig. 7 — RDM, 20% obstacle density |
| `Figure_8_path_len_sparse.png` | Fig. 8 — PL, 20% obstacle density |

## Relationship to `figures/`

[`../figures/`](../figures/) contains the same six figures at the **nominal** Table 1
densities, averaged over 20 seeds, plus 11 supplementary charts. The two disagree:

| Dense RDM @ 100×100 | here | `figures/` |
| --- | --- | --- |
| Dijkstra | 8919.3 | 7081.9 |
| A* | 4771.3 | 5831.9 |
| QHR-V2X | 194.2 | 5826.4 |

These match the published *numbers*; those match the published *parameters*. Use
this directory to check reproduction of the published figures, and `figures/` to see
the comparison at the stated densities.

See [`../../../VERIFICATION.md`](../../../VERIFICATION.md) §2.5 and §2.9.

## Other views

`make figures-all` generates 34 further figures — log scales, bar charts, overview
panels, overhead relative to A*, and a colour-vision-safe palette — under
`../all_figures/`. That directory is not tracked; it is rebuilt from the algorithms
on each run.
