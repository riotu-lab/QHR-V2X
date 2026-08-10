# Reproducing the paper's results

Artifact for *QHR-V2X: A Quantum-Heuristic Routing Framework for Efficient V2X Path
Discovery*, IEEE Open J. Commun. Soc., vol. 7, 2026, pp. 211–220.

Everything below runs the routing algorithms and measures them. No figure in this
repository is drawn from stored numbers.

---

## 1. Install

```bash
poetry install          # Python 3.11, NumPy, Matplotlib, pandas, Qiskit, qiskit-aer
```

## 2. Reproduce the paper's figures

```bash
make figures SEED=paper
```

Runs the three algorithms across every grid size in both topologies, writes the
benchmark CSVs, then draws Figures 3–8 into
`experiments/results/paper_figures/`. Takes a few minutes. This is the exact
command behind the figures committed there.

`SEED=paper` selects the obstacle layout behind the published figures. Add
`STYLE=curved` for their smooth line style — see §5.

## 3. Every other view of the same data

```bash
make figures-all SEED=paper
```

Adds 34 more figures under `experiments/results/all_figures/` — log scales, bar
charts, per-mode overview panels, overhead relative to A*, and a
colour-vision-safe palette. Each is described in that directory's `MANIFEST.md`.

## 4. Check the numbers

`paper_figures.py` prints every value it plots, so each point on each figure can
be read off the terminal and compared against the image. The benchmark CSVs are in
`benchmarks/results/benchmark_output_{dense,sparse}/csv/`.

To confirm the algorithms really run rather than the plots being redrawn from a
cached CSV: run `make figures` twice. `msgs` and `path_len` come back identical
under a fixed seed, while measured `time_ms` shifts. Only live execution produces
that combination.

---

## 5. Options

| Variable | Values | Default |
| --- | --- | --- |
| `SEED` | `paper` (12345), any integer, or `random` | unset — a fresh seed is drawn, printed, and written to the CSV's `seed` column |
| `STYLE` | `curved`, `straight` | `straight` |

```bash
make figures                              # fresh layout, straight lines
make figures SEED=paper                   # published layout
make figures STYLE=curved                 # published line style
make figures SEED=paper STYLE=curved      # both — as committed
```

An unseeded run is still replayable: the seed it drew is printed and recorded, so
passing it back reproduces that run exactly.

`SEED` affects the dense topology only. Sparse obstacles are a deterministic
partial wall in column `size // 3`; the run banner says so.

`straight` joins measured points with segments and draws nothing that was not
measured. `curved` smooths with a monotone cubic (PCHIP), chosen over a natural
cubic spline because it cannot overshoot — with five grid sizes per curve, a
natural spline can bulge past the surrounding points and imply an extremum that
was never measured.

---

## 6. What reproduces, and what does not

Verified against the published figures with `SEED=paper`:

| Figure | A* | Dijkstra | QHR-V2X |
| --- | --- | --- | --- |
| 3, 4 (dense RDT, RDM) | exact | exact | lowest curve; values differ |
| 5 (dense PL) | exact | exact | exact |
| 6, 7 (sparse RDT, RDM) | exact | exact | lowest curve; values differ |
| 8 (sparse PL) | exact | exact | exact |

Dijkstra's RDM at 100×100 is 8919.27 against the published ≈8900; A*'s is 4771.27
against ≈4800; A*'s non-monotone sparse kink (1083.6 at 40×40 falling to 812.6 at
50×50) reproduces.

Path optimality is checked against breadth-first search: all three algorithms
return shortest paths on every query tested (346 queries across the benchmark
grids, random 25 %-density obstacle fields, and the Grover-simulated selection
path).

**Known divergences from Table 1**, documented with evidence in
[VERIFICATION.md](VERIFICATION.md):

- the link-cost model of Eq. 2 (`α·d + β·τ + γ·(1−R)`) is not implemented; every
  edge costs one hop, and link reliability, SNR, transmission range and the
  mobility models are absent (§2.4);
- realised obstacle density is 1.6–12 %, not the stated 20 % and 40 %, and it
  falls as the grid grows (§2.5);
- results come from a single run per configuration, not the 20 independent seeds
  of Table 1, so no variance is reported (§2.6);
- Eq. 12 (`N'_e ≈ (1−η)·N_e`) predicts a constant-factor reduction; the measured
  reduction is real but grows with grid size, from 64 % to 96 % (§2.3).

---

## 7. Layout

```
src/                     algorithm implementations; qhr_v2x.py is the contribution
tests/                   benchmark harness and grid construction
experiments/scripts/     reproduce_paper_results.py — runs the benchmark
experiments/analysis/    figure generation
experiments/results/     output (only paper_figures/ is tracked)
VERIFICATION.md          what reproduces, what does not, and the evidence
```
