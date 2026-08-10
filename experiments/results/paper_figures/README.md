# Paper Figures 3–8

Committed so the figures can be viewed without running anything. Regenerated with:

```bash
make figures SEED=paper
```

`SEED=paper` is the obstacle layout behind the published figures. Add
`STYLE=curved` for the paper's smooth line style; those land beside these with a
`_curved` suffix and are not tracked. Every point is a live algorithm run — see
[REPRODUCE.md](../../../REPRODUCE.md).

| File | Paper figure |
| --- | --- |
| `Figure_3_estimated_ms_dense.png` | Fig. 3 — Estimated RDT, 40% obstacle density |
| `Figure_4_msgs_dense.png` | Fig. 4 — RDM, 40% obstacle density |
| `Figure_5_path_len_dense.png` | Fig. 5 — PL, 40% obstacle density |
| `Figure_6_estimated_ms_sparse.png` | Fig. 6 — Estimated RDT, 20% obstacle density |
| `Figure_7_msgs_sparse.png` | Fig. 7 — RDM, 20% obstacle density |
| `Figure_8_path_len_sparse.png` | Fig. 8 — PL, 20% obstacle density |

Other views of the same data (log scales, bar charts, overview panels,
colour-vision-safe palette) are not tracked; generate them with
`make figures-all SEED=paper`.
