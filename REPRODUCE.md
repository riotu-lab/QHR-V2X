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

**Without Poetry.** Every `make` target invokes Python through `$(PY)`, which
resolves to Poetry if installed, otherwise a project-local `.venv`, otherwise
`python3`. So a plain virtual environment is enough:

```bash
uv venv --python 3.11 .venv          # or: python3.11 -m venv .venv
uv pip install -r <(poetry export -f requirements.txt --without-hashes)
make figures SEED=paper               # picks up .venv automatically
```

Pass `PY=` explicitly to force a particular interpreter — `make figures
PY=/usr/bin/python3.11`. `make lint` and `make format` run their tools as
`$(PY) -m flake8` / `-m black`, so they follow the same choice.

The published results were produced on Python 3.11.5; the requirement is
`>=3.11,<3.12`, so any 3.11 patch release will do. 8 GB RAM is comfortable for the
100×100 grids. A full run of both topologies takes a few minutes; `make figures-all`
a little longer.

If `poetry install` leaves something missing, `poetry install --sync` reinstalls
from the lockfile. Qiskit is not optional: `src/qhr_v2x.py` imports `qiskit` and
`qiskit_aer` at module level, so both must be installed for the algorithm to
import at all. What *is* optional is executing a circuit —
`qhr_v2x(..., use_quantum=True)` is the only path that runs one, it is off by
default, and a `QiskitError` raised there falls back to classical selection.

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
main.py                  optional CLI for exploring the algorithms by hand
examples/                a standalone qiskit-aer smoke test
experiments/scripts/     reproduce_paper_results.py — runs the benchmark
                         generate_comparison_charts.py — the 20-seed run
experiments/analysis/    figure generation
experiments/results/     output; see below for what is committed
VERIFICATION.md          what reproduces, what does not, and the evidence
```

### What is committed, and what you generate

**No figure is committed.** Every chart here is drawn from a live run of the
algorithms, so a checked-in image could only ever duplicate what `make` rebuilds.
Generate them:

```bash
make figures SEED=paper   # Figures 3-8 as published  -> results/paper_figures/
make figures-nominal      # Table 1 parameters, 20 seeds -> results/figures/
```

| Path | Tracked | Why |
| --- | --- | --- |
| `results/comparison_*.csv`, `comparison_summary.md` | **yes** | The measured numbers behind every figure and every claim in VERIFICATION.md. Small, text, diffable. |
| `results/paper_figures/` | no | `make figures SEED=paper`, a few minutes. |
| `results/figures/` | no | `make figures-nominal`. The slowest to rebuild — 20 seeds × 3 repeats. |
| `results/all_figures/` | no | 34 further views, `make figures-all`. |
| `results/diagnostics/` | no | `hypothesis_check.py` and `metric_consistency.py` output, cited in VERIFICATION.md. |
| `results/paper_reproduction/` | no | `make validate` scratch output. |
| `analysis/results/` | no | `make analyze`, seconds. |
| `benchmarks/results/` | no | Raw per-run CSVs from the harness. |

Because the figures are generated rather than stored, the CSVs are what carries
the evidence between runs — the numbers quoted throughout VERIFICATION.md can be
checked against them without regenerating anything.

`make clean` removes the generated set and leaves the committed CSVs alone.

### On the pinned versions

`pyproject.toml` pins `qiskit ^0.44` and `qiskit-aer ^0.12` — the versions the
published figures were generated with. That pin is part of the reproduction
contract and is deliberate, not neglect. The Python requirement is `>=3.11,<3.12`:
3.11.5 is what the paper used, the range is open across 3.11 patch releases so a
reproducer is not blocked by a patch-level mismatch, and 3.12 is excluded because
the pinned qiskit predates it.

---

## 8. The two figure sets

`experiments/results/` holds the Section IV figures twice, under two different
configurations. They disagree, and the disagreement is the point.

| Dense RDM @ 100×100 | `paper_figures/` | `figures/` |
| --- | --- | --- |
| Dijkstra | 8919.3 | 7081.9 |
| A* | 4771.3 | 5831.9 |
| QHR-V2X | 194.2 | 5826.4 |

**`paper_figures/` matches the published numbers.** Produced by `make figures
SEED=paper` from the `tests/` harness — one obstacle layout per grid size,
endpoints running each row of the left column to the bottom-right corner. That
harness places `int(size × density)` obstacles rather than `int(size² × density)`,
so realised density falls as the grid grows: 1.56 % at 100×100 against a nominal
40 %, 12 % at 10×10. These are the conditions under which the published A* and
Dijkstra values reproduce exactly, which is why they are kept.

**`figures/` matches the published parameters.** Produced by:

```bash
python experiments/scripts/generate_comparison_charts.py --seeds 20 --repeats 3
```

Exactly 40 % / 20 % obstacles at every grid size, 20 independent seeds averaged,
three timing repeats, and one shared message counter across all three algorithms
so RDM, RDT, PL and Ne each have a single definition.

Endpoints there are not corner-to-corner, because at 40 % density they cannot be:
a free-cell fraction of 0.60 sits just above the 2-D site-percolation threshold
p_c ≈ 0.5927, so opposite corners of a large grid are almost never connected — a
75×75 draw failed 200 consecutive solvability checks. Endpoints are instead an
approximate-diameter pair inside the largest free component, which keeps every
instance solvable without quietly lowering the density.
`Supp_solvability_vs_density.png` documents this.

Beyond the six Section IV figures, `figures/` carries supplementary charts:
`Supp_expansions_*` (node expansions Ne, the quantity Eq. 12 constrains),
`Supp_Eq12_check_*` (measured ratio against Eq. 12's prediction),
`Supp_rdm_model_*` (the two message-counting conventions side by side),
`Supp_measured_time_*` (measured wall-clock, separate from estimated RDT) and
`Supp_summary_*` (all metrics for one density in one panel).

### Regenerating `figures/`

Re-running the command reproduces 15 of the 17 charts byte-identically, and every
deterministic column of the CSVs. Three outputs legitimately differ:
`Supp_measured_time_{dense,sparse}.png`, the `wall_ms` column of
`comparison_*.csv`, and `comparison_summary.md` where it quotes those timings —
all measured wall-clock, hence machine-dependent. Message counts, expansions and
path lengths are seeded and identical everywhere; if *those* move, something is
genuinely wrong.

Add `--include-stochastic` to also measure sampling from the amplified
distribution rather than taking its maximum.

See [VERIFICATION.md](VERIFICATION.md) §2.5, §2.9 and §2.10 for what follows from
the density difference.
