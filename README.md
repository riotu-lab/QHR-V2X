# QHR-V2X

Reference implementation and reproduction artifact for:

> **QHR-V2X: A Quantum-Heuristic Routing Framework for Efficient V2X Path Discovery**
> Zahid Khan, Sultan Almogbil, Muhammad Babar, Adel Ammar, and Wadii Boulila
> Robotics and Internet-of-Things (RIOTU) Laboratory, Prince Sultan University
> *IEEE Open Journal of the Communications Society*, vol. 7, 2026, pp. 211–220.
> [doi:10.1109/OJCOMS.2025.3644144](https://doi.org/10.1109/OJCOMS.2025.3644144)

QHR-V2X biases A* node selection with quantum amplitude amplification (Eqs. 9–11),
optionally routing the selection through a Grover circuit on the Qiskit
AerSimulator. This repository contains that algorithm, the classical baselines it
is measured against, the benchmark harness, the figure pipeline behind Figures
3–8, and a verification report on what does and does not reproduce.

Everything here runs the routing algorithms and measures them. No figure in this
repository is drawn from stored numbers.

## Install

```bash
poetry install      # Python 3.11, NumPy, Matplotlib, pandas, Qiskit, qiskit-aer
```

Poetry is not required. Every `make` target invokes Python through `$(PY)`, which
resolves to Poetry if installed, otherwise a project-local `.venv`, otherwise
`python3` — so a plain virtual environment works:

```bash
uv venv --python 3.11 .venv        # or: python3.11 -m venv .venv
uv pip install -r <(poetry export -f requirements.txt --without-hashes)
make figures SEED=paper             # picks up .venv automatically
```

`./setup.sh` bootstraps the whole toolchain instead — it installs pyenv and
Poetry from their upstream install scripts, pins Python 3.11.5 with `pyenv local`,
then runs `poetry install`. Use it only if you want that.

Qiskit is a hard requirement: `src/qhr_v2x.py` imports `qiskit` and `qiskit_aer`
at module level. Only the `use_quantum=True` selection path actually executes a
circuit, and a `QiskitError` there falls back to classical selection — but the
import must succeed either way.

## Reproduce the paper's figures

```bash
make figures SEED=paper
```

Runs the three algorithms across every grid size in both topologies, writes the
benchmark CSVs, then draws Figures 3–8 into `experiments/results/paper_figures/`.
Takes a few minutes. `SEED=paper` selects the obstacle layout behind the published
figures; add `STYLE=curved` for their smooth line style.

```bash
make figures-nominal          # the same six figures at Table 1's stated parameters
make figures-all SEED=paper   # the 6 above plus 34 further views of the same data
make analyze                  # statistical summary
make all                      # install, test, figures, analyze
```

`make figures-nominal` is the counterpart to `make figures`: uniform random
obstacles at exactly 20 % / 40 %, 20 independent seeds, one shared message counter.
**It does not match the published figures** — that is the finding rather than a
bug, and REPRODUCE.md §8 tabulates where the two disagree.

`make figures` depends on `make reproduce`, so figures are never drawn from a
stale CSV, and `paper_figures.py` prints every value it plots so each point can be
checked against the image.

**[REPRODUCE.md](REPRODUCE.md)** covers the seed and line-style options, how to
confirm the algorithms really run, and what is committed versus generated.

## What reproduces, and what does not

With `SEED=paper`, A* and Dijkstra reproduce the published values exactly, all
three algorithms match in Figures 5 and 8, and QHR-V2X is the lowest curve in
Figures 3, 4, 6 and 7 as published — though its absolute values differ. Path
optimality is verified against breadth-first search across 346 queries.

Divergences from the paper's Table 1 are documented with evidence in
**[VERIFICATION.md](VERIFICATION.md)**.

Unimplemented anywhere:

- the link-cost model of Eq. 2 (`α·d + β·τ + γ·(1−R)`) — every edge costs one hop,
  and link reliability, SNR, transmission range and the mobility models of
  Eqs. 3–6 are absent (§2.4).

Open in the `tests/` harness, corrected in `make figures-nominal`:

- realised obstacle density is 1.6–12 %, not the stated 20 % and 40 %, and falls
  as the grid grows (§2.5);
- the sparse generator is not random at all — it writes a partial wall into the
  single column `size // 3`, where Section IV-A specifies "20 % randomly
  distributed obstacles" and "a unique realization... rather than a static
  layout". Different seeds produce identical grids (§2.5);
- results come from a single run per configuration, not 20 independent seeds, so
  no variance is reported — and for sparse mode, seed variation would change
  nothing (§2.6).

The `tests/` harness is left uncorrected deliberately: it is what reproduces the
published values, and fixing its density changes the published figures.

Holds as measured:

- Eq. 12 predicts a constant-factor reduction in expansions; the measured
  reduction is real but grows with grid size, from 64 % to 96 % (§2.3).

## Layout

```
src/                        algorithm implementations; qhr_v2x.py is the contribution
tests/                      benchmark harness and grid construction
main.py                     optional CLI for exploring the algorithms by hand
examples/                   standalone qiskit-aer smoke test
experiments/scripts/        reproduce_paper_results.py  — runs the benchmark
                            generate_comparison_charts.py — the 20-seed run
experiments/analysis/       figure generation and statistical analysis
experiments/results/        measured CSVs, and generated figures (see REPRODUCE.md §7)
scripts/audit.sh            checks the docs still match the code (`make audit`)
REPRODUCE.md                how to reproduce the figures, and the two figure sets
VERIFICATION.md             what reproduces, what does not, and the evidence
```

The docs here make checkable claims — code line numbers, make targets, which
files ship — and those drift as the code changes. `make audit` verifies them and
exits non-zero on a stale one; run it before committing documentation changes.

**No figure is committed** — every chart is drawn from a live run, so `make
figures SEED=paper` and `make figures-nominal` produce them on demand. What *is*
committed is the measured CSVs under `experiments/results/`, which carry the
numbers behind every claim in VERIFICATION.md. REPRODUCE.md §7 lists the policy
per directory.

## The algorithms

| Module | Algorithm |
| --- | --- |
| `src/qhr_v2x.py` | QHR-V2X — the paper's contribution, plus its classical baseline |
| `src/dijkstra_grid_u.py` | Dijkstra |
| `src/astar_u.py` | A* |
| `src/astar_u_quantum.py` | A*, quantum-enhanced selection |
| `src/dijkstra_quantum_enhanced.py` | Dijkstra, quantum-enhanced selection |
| `src/grover_classic.py` | Classical simulation of Grover selection |
| `src/grover_quantum_bfs.py` | Grover-assisted BFS on the AerSimulator |
| `src/cqw_quantum.py` | Continuous quantum walk |
| `src/cqw_vectorized.py` | Vectorized continuous quantum walk |

Figures 3–8 compare the first three; the rest are additional implementations
carried by the harness.

Grids are NumPy boolean arrays (`True` = obstacle) with 4-connectivity and
`(row, col)` coordinates from `(0, 0)`. Every algorithm returns
`(path, messages)`, where `path` is a list of coordinates and `messages` is the
route-discovery message count — one per frontier expansion, counted identically
for all three algorithms; see [VERIFICATION.md](VERIFICATION.md) §2.2.

## Exploring by hand

```bash
python main.py help       # commands and the algorithm registry
python main.py demo       # 5x5 grid, Dijkstra and A*, printed maps
python main.py quantum    # smaller grid, the quantum-enhanced variants
python main.py compare qhr_v2x qhr_v2x_classical
python main.py selective dijkstra astar astar_quantum
```

Prefix with `poetry run` or use `.venv/bin/python`, depending on how you
installed.

This CLI is for inspection, not for the paper's numbers — those come from
`make figures`. Benchmark output lands in `benchmarks/results/`.

Three environment variables tune the quantum-walk simulator:

```bash
export CQW_MAX_QPOS=20        # maximum position qubits
export CQW_SHOT_CAP=256       # maximum simulator shots
export CQW_LOG_LEVEL=WARNING  # logging level
```

## Benchmark configuration

Dense mode runs 10×10, 25×25, 50×50, 75×75 and 100×100; sparse mode runs 10×10
through 50×50 in steps of 10. Dense obstacles are randomly seeded; sparse
obstacles are a deterministic partial wall in column `size // 3`, so `SEED`
affects dense mode only. The nominal densities are 40 % and 20 % — see
VERIFICATION.md §2.5 for what is actually realised.

Measured per run: route discovery time (RDT), route discovery messages (RDM),
path length (PL), node expansions, and wall-clock time.

## Requirements

Python 3.11 (the published results were produced on 3.11.5) and 8 GB RAM for the
100×100 grids. If `poetry install` leaves something missing, `poetry install --sync`
reinstalls from the lockfile. The Qiskit versions are pinned to those the published
figures were generated with; see REPRODUCE.md §7.

## License

MIT — see [LICENSE](LICENSE).

## Citation

```bibtex
@article{khan2026qhrv2x,
  title   = {{QHR-V2X}: A Quantum-Heuristic Routing Framework for Efficient {V2X} Path Discovery},
  author  = {Khan, Zahid and Almogbil, Sultan Hamad and Babar, Muhammad and Ammar, Adel and Boulila, Wadii},
  journal = {IEEE Open Journal of the Communications Society},
  volume  = {7},
  pages   = {211--220},
  year    = {2026},
  doi     = {10.1109/OJCOMS.2025.3644144},
  issn    = {2644-125X}
}
```

Machine-readable metadata is in [CITATION.cff](CITATION.cff).
