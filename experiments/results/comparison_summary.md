# A* / QHR-V2X / Dijkstra comparison

Seeds per grid size: 20. Timing repeats per instance: 3 (minimum kept). Amplification parameters: eta=0.3, T=1.0, |C|=8.

## Metric definitions

All algorithms are measured through one shared search skeleton, so every metric has a single definition:

- **RDT** - measured wall-clock search time in milliseconds.
- **RDM** - control messages: one per node selection, plus one per accepted edge relaxation.
- **PL** - discovered path length in hops.
- **Ne** - distinct nodes finalised, the quantity Eq. 12 makes a claim about.

## Instance generation

Obstacles are uniform random at the nominal density, i.e. `round(size * size * density)` blocked cells. Corner-to-corner queries are not usable at the 40% dense setting: the resulting free-cell fraction of 0.60 sits just above the 2D site-percolation threshold p_c ~ 0.5927, so opposite corners are rarely connected once the grid is large (see `figures/Supp_solvability_vs_density.png`). Endpoints are therefore drawn from the largest connected free component as an approximate-diameter pair, which keeps every instance solvable without silently lowering the density.

## Which series appear where

Every figure shows exactly the three algorithms the paper compares: Dijkstra, A* and QHR-V2X. QHR-V2X uses argmax selection over Eqs. (9)-(11), as Algorithm 1 step 4 specifies.

Re-run with `--include-stochastic` to additionally measure the sampling reading of Eq. 11; it is excluded here.

## Results

### Sparse topology (20% obstacles)

| Algorithm            |   RDT (ms) |        RDM |  PL (hops) |         Ne | Measured (ms) |  Optimal |
|----------------------|------------|------------|------------|------------|---------------|----------|
| A*                   |     0.4980 |      498.0 |      58.14 |      194.8 |         0.457 | 100/100    |
| Dijkstra             |     1.7515 |     1751.5 |      58.14 |      876.2 |         1.344 | 100/100    |
| QHR-V2X              |     0.4948 |      494.8 |      58.14 |      193.1 |         9.787 | 100/100    |

Eq. 12 predicts N'e/Ne = 0.70; measured 0.9766-0.9972 across grid sizes.


### Dense topology (40% obstacles)

| Algorithm            |   RDT (ms) |        RDM |  PL (hops) |         Ne | Measured (ms) |  Optimal |
|----------------------|------------|------------|------------|------------|---------------|----------|
| A*                   |     2.0646 |     2064.6 |     129.93 |     1003.9 |         1.897 | 100/100    |
| Dijkstra             |     2.5586 |     2558.6 |     129.93 |     1279.7 |         1.914 | 100/100    |
| QHR-V2X              |     2.0564 |     2056.4 |     129.93 |      992.1 |        48.353 | 100/100    |

Eq. 12 predicts N'e/Ne = 0.70; measured 0.9229-0.9914 across grid sizes.


## Figures

- `figures/Supp_solvability_vs_density.png`
- `figures/Fig6_sparse.png`
- `figures/Fig7_sparse.png`
- `figures/Fig8_sparse.png`
- `figures/Supp_measured_time_sparse.png`
- `figures/Supp_expansions_sparse.png`
- `figures/Supp_rdm_model_sparse.png`
- `figures/Supp_summary_sparse.png`
- `figures/Supp_Eq12_check_sparse.png`
- `figures/Fig3_dense.png`
- `figures/Fig4_dense.png`
- `figures/Fig5_dense.png`
- `figures/Supp_measured_time_dense.png`
- `figures/Supp_expansions_dense.png`
- `figures/Supp_rdm_model_dense.png`
- `figures/Supp_summary_dense.png`
- `figures/Supp_Eq12_check_dense.png`

## Reproduce

```bash
python experiments/scripts/generate_comparison_charts.py --seeds 20 --repeats 3 --eta 0.3 --temperature 1.0 --candidate-size 8
```
