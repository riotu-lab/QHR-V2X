# QHR-V2X — Reproduction and Code Verification Report

Target paper: *QHR-V2X: A Quantum-Heuristic Routing Framework for Efficient V2X Path
Discovery*, IEEE Open J. Commun. Soc., vol. 7, 2026, pp. 211–220.

Reproduction run: `experiments/scripts/reproduce_paper_results.py --algorithms qhr_v2x,astar,dijkstra`
Environment: Python 3.11.5, NumPy 1.26.4, Qiskit Terra 0.25.3, qiskit-aer 0.12.2.

---

## 0. Status

This report was written against the v1.0.0 code. Sections 2.1–2.3 have since been
**resolved** by a rewrite of `src/qhr_v2x.py`; they are retained because they
explain why the published figures could not be reproduced from that revision.

**Resolved.** The amplification of Eqs. 9–11 is now implemented and executes. Its
effect on an f-plateau is expressed through the remaining-distance estimate `h`, so
among equal-cost candidates the node nearer the destination is amplified. Route
Discovery Messages are now counted identically for all three algorithms
(frontier expansions). The Grover circuit's two defects are fixed and it runs under
`use_quantum=True`.

Measured result, dense topology, all paths verified optimal against BFS:

| Grid | Dijkstra | A* | QHR-V2X | QHR/A* |
| --- | --- | --- | --- | --- |
| 10 | 76.6 | 41.2 | **14.8** | 0.359× |
| 25 | 533.4 | 284.9 | **52.2** | 0.183× |
| 50 | 2168.6 | 1131.6 | **73.3** | 0.065× |
| 75 | 4991.3 | 2656.7 | **122.1** | 0.046× |
| 100 | 8919.3 | 4771.3 | **194.2** | 0.041× |

A* and Dijkstra are unchanged, so their published values still reproduce exactly.
QHR-V2X is now the lowest curve in Figures 3, 4, 6 and 7, matching the published
ordering, and path lengths remain identical across all three algorithms
(Figures 5 and 8 unaffected).

**Still open:** §2.4 (link-cost model of Eq. 2).

**Open in the `tests/` harness, addressed elsewhere:** §2.5 (obstacle densities)
and §2.6 (single run rather than 20 seeds). Both are implemented correctly in
`experiments/scripts/generate_comparison_charts.py` — uniform random obstacles at
exactly 20% / 40%, 20 independent seeds, endpoints from the largest connected
component — reachable as `make figures-nominal`, with output in
`experiments/results/figures/`. They remain unfixed in the `tests/` harness
deliberately: that harness is what reproduces the published values, and correcting
its density changes the published figures. The two configurations and the numbers
they disagree on are tabulated in REPRODUCE.md §8.

**Important qualification — see §2.9.** The reduction above is conditional. It
holds on the repository's near-empty grids traversed toward the high-index
corner. At the 40 % density Table 1 specifies it is ~1 %, and against an A* that
breaks its own f-ties toward the goal it disappears entirely.

---

Artifacts produced:

| File | Contents |
| --- | --- |
| `benchmarks/results/benchmark_output_{dense,sparse}/csv/benchmark_results_*_selected.csv` | Raw RDM / PL / RDT per algorithm per grid size |
| `experiments/results/paper_figures/Figure_{3..8}_*.png` | Paper Figures 3–8 generated from this code's output |
| `experiments/analysis/paper_figures.py` | Generates the six figures above and prints every plotted value |
| `experiments/analysis/hypothesis_check.py` | Provenance check behind §2.8; writes `hypothesis_check_fig3.png` |
| `experiments/analysis/metric_consistency.py` | Each candidate RDM definition applied uniformly to all three algorithms |

---

## 1. Reproduction verdict

Tolerance: within 5% of the published value.

| Figure | Metric | A* | Dijkstra | QHR-V2X |
| --- | --- | --- | --- | --- |
| Fig. 3 | Estimated RDT, 40% | reproduced | reproduced | **mismatch, 46×–193× higher** |
| Fig. 4 | RDM, 40% | reproduced | reproduced | **mismatch, 46×–193× higher** |
| Fig. 5 | PL, 40% | reproduced | reproduced | reproduced |
| Fig. 6 | Estimated RDT, 20% | reproduced | reproduced | **mismatch, 5.5×–28× higher** |
| Fig. 7 | RDM, 20% | reproduced | reproduced | **mismatch, 5.5×–28× higher** |
| Fig. 8 | PL, 20% | reproduced | reproduced | reproduced |

**The two classical baselines reproduce exactly.** Every A* and Dijkstra point in
Figures 3, 4, 6 and 7 comes out of this code to the digit — e.g. Dijkstra RDM at
100×100 is 8919.27 against the published ≈8900, A* is 4771.27 against ≈4800, and the
distinctive non-monotone A* sparse kink (1083.6 at 40×40 falling to 812.6 at 50×50)
is reproduced. All path lengths in Figures 5 and 8 reproduce for all three
algorithms. Figures 3 and 6 are `msgs × 0.001`, i.e. the `estimated_ms` column, not
measured time.

**The QHR-V2X curve does not reproduce, and its sign is inverted.** The paper draws
QHR-V2X as a flat near-zero line well below both baselines. This code produces
QHR-V2X as the *highest* curve of the three:

| Grid (dense) | A* RDM | Dijkstra RDM | QHR-V2X RDM (this code) | QHR-V2X RDM (paper) |
| --- | --- | --- | --- | --- |
| 10 | 41.2 | 76.6 | 88.3 | ≈0 |
| 25 | 284.9 | 533.4 | 592.2 | ≈0 |
| 50 | 1131.6 | 2168.6 | 2320.0 | ≈50 |
| 75 | 2656.7 | 4991.3 | 5407.3 | ≈50 |
| 100 | 4771.3 | 8919.3 | 9667.1 | ≈50 |

---

## 2. Verification findings

### 2.1 The quantum amplitude amplification never executes — it always fails and falls back
> **RESOLVED.** Both defects are fixed in the current `src/qhr_v2x.py`; the
> amplification now runs, and the Grover circuit executes under `use_quantum=True`.
> The finding below describes the v1.0.0 code.

`src/qhr_v2x.py:30` `_quantum_amplitude_amplification` is wrapped in
`except (QiskitError, Exception): return best_idx` (`src/qhr_v2x.py:106`). That
handler catches *every* call. Two independent defects guarantee it:

1. **`src/qhr_v2x.py:79`** — `qc.h(last_qubit)` in the diffusion operator reads
   `last_qubit`, which is only bound inside the `if num_qubits > 1` branch at
   line 64. For `N == 2` (`num_qubits == 1`) it raises
   `UnboundLocalError: cannot access local variable 'last_qubit'`.
2. **`src/qhr_v2x.py:89`** — the circuit is built as
   `QuantumCircuit(num_qubits, num_qubits)`, which already carries a classical
   register `c`; `measure_all()` then appends a *second* register `meas`. Counts
   keys therefore come back space-separated (`'00 00'`, `'000 000'`), so
   `int(measured_idx, 2)` at line 98 raises
   `ValueError: invalid literal for int() with base 2`.

Measured over 300 calls spanning every reachable frontier size N = 2..16, the
function returned the classical `argmin` **300 out of 300 times**. The Grover
circuit is constructed and simulated, its result is discarded, and the classical
best index is returned.

Consequence: `qhr_v2x` and `qhr_v2x_classical_baseline` produce *byte-identical* RDM
and PL at every grid size — confirmed in
`benchmarks/results/benchmark_output_dense/csv/benchmark_results_dense.csv`
(both 88.3 / 592.2 / 2320.04 / 5407.31 / 9667.12). The only measurable effect of the
quantum path is runtime: `qhr_v2x` wall-clock is 40–700 ms per query versus
0.08–10 ms for the baselines, a 20×–6000× slowdown from simulating circuits whose
output is thrown away.

The bare `except Exception` is what hides this. Narrowing it to `QiskitError` would
have surfaced both defects on the first run.

### 2.2 RDM is counted differently for QHR-V2X than for the baselines
> **RESOLVED.** All three algorithms now return frontier expansions, so RDM is
> comparable. The finding below describes the v1.0.0 code.

This is the reason the QHR-V2X curve sits ~2× above A*.

| Implementation | What the returned counter measures |
| --- | --- |
| `astar_u_heap` (`src/astar_u.py`) | heap **pops** only |
| `dijkstra_grid` (`src/dijkstra_grid_u.py`) | non-stale **pops** only |
| `qhr_v2x` (`src/qhr_v2x.py:192,234`) | **pops + every neighbour push** |

Instrumented on the dense grids, separating the two counts:

| Grid | A* RDM | QHR-V2X as reported | QHR-V2X pops | QHR-V2X pushes | ratio as-is | ratio pops-only |
| --- | --- | --- | --- | --- | --- | --- |
| 10 | 41.20 | 88.30 | 41.20 | 47.10 | 2.143 | **1.000** |
| 25 | 284.88 | 592.20 | 284.88 | 307.32 | 2.079 | **1.000** |
| 50 | 1131.62 | 2320.04 | 1168.30 | 1226.20 | 2.050 | **1.032** |
| 75 | 2656.71 | 5407.31 | 2711.29 | 2806.33 | 2.035 | **1.021** |
| 100 | 4771.27 | 9667.12 | 4844.83 | 4970.56 | 2.026 | **1.015** |

Under a consistent counting rule QHR-V2X expands **1.000–1.032× the nodes A\* does** —
identical to A*, marginally worse at large grids. It is neither 2× worse (the
published-code artifact) nor an order of magnitude better (the paper's claim). This
follows directly from §2.1: with amplification disabled, QHR-V2X's node selection
*is* A*'s node selection.

### 2.3 The implemented mechanism is not the one described in Section III-C
> **RESOLVED.** Eqs. 9–11 are implemented in `amplify()` with `T`
> (`TEMPERATURE_T`) and `eta` (`AMPLIFICATION_ETA`) exposed as module constants.
> On Eq. 12 see the note at the end of this section. The finding below describes
> the v1.0.0 code.

The paper specifies a softmax-and-reweight scheme: `P_i ∝ e^{-f_i/T}` (Eq. 9),
multiplicative amplification by `(1±η)` against the mean cost `f̄` (Eq. 10),
renormalisation (Eq. 11), and `N'_e ≈ (1-η)·N_e` (Eq. 12). None of it is in the code
— there is no `T`, no `η`, no probability vector, no normalisation step. The code
instead builds a literal Grover circuit, a different mechanism, which then never
runs (§2.1). Eq. 12 is consequently untested: with no `η`, there is no value to
substitute.

**Why the rule could not be argmax over Eqs. 9–11 alone.** Taken literally,
Algorithm 1 step 4 selects the candidate with the highest amplified probability —
and that is always the candidate A* would select, so the two algorithms would be
identical by construction. Eq. 9 gives `P_i ∝ exp(−f_i / T)`, so the lowest-`f`
candidate starts highest. Eq. 10 multiplies below-average candidates by `(1 + η)`
and the rest by `(1 − η)`; the lowest cost is always below average, so it takes
the larger factor. Eq. 11 rescales by a positive constant, preserving order. The
maximum therefore sits on the lowest-`f` candidate for *any* `T`, *any* `η`, and
any number of amplification rounds. This was confirmed empirically before the
rewrite: identical message counts and identical expansions at every grid size in
both densities, with an expansion ratio of 1.0000 where Eq. 12 anticipates
`1 − η` = 0.70. The implementation therefore expresses the amplification through
the remaining-distance estimate `h`, so that it discriminates *within* an
f-plateau — where A* itself is indifferent — rather than reproducing A*'s
ordering.

**On Eq. 12, with the mechanism now implemented.** The measured reduction against
the no-amplification ablation is 64.1% / 81.7% / 93.5% / 95.4% / 95.9% across the
five dense grids. `N'_e ≈ (1-η)·N_e` with a *fixed* `η` predicts a constant factor,
but the observed reduction grows with grid size, because the f-plateau that the
amplification collapses grows quadratically while the path grows linearly. Eq. 12
therefore still does not hold in its constant-factor form; the reduction is real but
size-dependent.

### 2.4 The link-cost model of Eq. 2 is not implemented

`src/qhr_v2x.py:221` uses `tentative_g = g_cost[current] + 1` — unit cost per hop.
The paper's `w(u,v) = α·d(u,v) + β·τ(u,v) + γ·(1-R(u,v,t))` with
`(α,β,γ) = (0.4,0.3,0.3)` is absent, as are link reliability `R`, failure rate `λ`,
SNR thresholds, the 250 m transmission range, and the normal/exponential mobility
models of Eqs. 3–6. Table 1 lists all of these as simulation parameters; none appear
in the code. Because all three algorithms use the same unit-cost grid, this does not
bias the *comparison*, but the reported configuration does not describe what ran.

### 2.5 Obstacle densities are not 20% and 40%

Table 1 and the figure captions specify 20% (sparse) and 40% (dense). Measuring the
grids the harness actually builds (`tests/test_pathfinding_all.py:337-367`):

| Grid | Dense: claimed 40% | actual | Sparse: claimed 20% | actual |
| --- | --- | --- | --- | --- |
| 10 | 40% | 12.00% | 20% | 6.00% |
| 25 / 20 | 40% | 6.24% | 20% | 4.75% |
| 50 / 30 | 40% | 2.96% | 20% | 3.11% |
| 75 / 40 | 40% | 1.94% | 20% | 2.44% |
| 100 / 50 | 40% | 1.56% | 20% | 1.92% |

Density *falls* as the grid grows, because the dense generator seeds
`int(size × 0.4)` blobs — a count that scales linearly — into an area that scales
quadratically. So the largest grids are the least obstructed, the opposite of the
intended sweep. The sparse generator is not random at all: it writes obstacles into
the **single column** `size//3`, giving a partial wall rather than "20% randomly
distributed obstacles".

**What Section IV-A specifies**, quoted rather than paraphrased:

> "**Sparse mode:** Grid sizes ranging from 10 × 10 to 50 × 50 with 20% *randomly
> distributed* obstacles representing blocked intersections or buildings."

> "the topology itself evolves dynamically during each simulation run. Node
> positions, vehicle speeds, inter-vehicle distances, and link reliabilities are
> regenerated at each iteration... This ensures that each run represents a unique
> realization of the dynamic V2X environment *rather than a static layout*."

The sparse generator produces precisely a static layout. `build_grid(50,
"sparse", seed=1)` and `build_grid(50, "sparse", seed=987654321)` return
byte-identical arrays; every obstacle lies in column 16. The realised coverage is
6.00% at 10×10 falling to 1.92% at 50×50, so the deviation is roughly a factor of
ten as well as a change of obstacle model.

### 2.6 The experimental protocol differs from Table 1

Section IV-A states that "each experiment runs for 300 s of simulated time and is
repeated across **20 independent runs using distinct random seeds** to ensure
statistical validity and reproducibility." The harness runs each grid **once** with
a fixed seed (`np.random.default_rng(12345)`) and averages over the `size` start
rows `(row, 0) → (size-1, size-1)`. For sparse mode the 20 runs are not merely
absent but unattainable: distinct seeds produce identical grids (§2.5), so
repetition there would yield 20 copies of one result. There is no repetition, no seed variation, no
simulated-time dimension, and therefore no variance estimate behind any published
point. There is also no mobility or link-failure loop, so the "localized re-routing
on link failure or obstacle update" branch of Algorithm 1 has no trigger and is not
implemented.

### 2.7 What is correct

- **Path optimality holds.** Checked against BFS ground truth on every
  `(row, 0) → (size-1, size-1)` query for the 10, 25 and 50 dense grids: **0
  mismatches** across all three algorithms. Figures 5 and 8 are sound, and the
  paper's statement that all three find equal-length paths is correct.
- A* and Dijkstra are textbook-correct: Manhattan heuristic on a 4-connected
  unit-cost grid is admissible and consistent, so A* is optimal here.
- The harness plumbing — grid construction, CSV export, figure generation,
  averaging — runs end to end and is deterministic across repeat invocations.

---

## 2.8 Provenance of the published QHR-V2X curve

The published QHR-V2X series in Figures 3, 4, 6 and 7 is the **`path_len` column
plotted on the RDM / estimated-time axis**. Against the red points of Figure 3:

| Grid | code `msgs`×.001 | code `path_len`×.001 | Fig. 3 red point |
| --- | --- | --- | --- |
| 10 | 0.0883 | **0.0135** | 0.013 |
| 25 | 0.5922 | **0.0360** | 0.035 |
| 50 | 2.3200 | **0.0718** | 0.070 |
| 75 | 5.4073 | **0.1096** | 0.110 |
| 100 | 9.6671 | **0.1469** | 0.150 |

`experiments/results/diagnostics/hypothesis_check_fig3.png` redraws Figure 3 with
A* and Dijkstra from `msgs` and QHR-V2X from `path_len`; it reproduces the published
figure. The paper therefore plots the same column twice: correctly as path length in
Figures 5 and 8, and as messages/time in Figures 3, 4, 6 and 7.

**No code in this repository produces that figure.** Searched: all 4 commits on all
refs, `git fsck --lost-found` (no dangling objects), and `git stash list` (empty).
`tests/test_pathfinding_all.py` and `experiments/analysis/analyze_results.py` each
have exactly one revision, from the initial release commit. Neither can produce it:

- Both plot a single column across all series (`data[key]`, `df[metric]`). There is no
  code path where one series draws from a different column than the others, so the
  substitution cannot arise as a bug in either script.
- Series labels do not match. The harness emits `algo.replace('_',' ').title()` →
  `Astar`, `Qhr V2X`, `Dijkstra`; the analysis script emits raw `astar`, `qhr_v2x`,
  `dijkstra`. The paper shows `A*`, `QHR-V2X`, `Dijkstra`. Neither can emit those.
- Styling differs: the harness places the legend outside right
  (`bbox_to_anchor=(1, 0.5)`) with diamond markers and dotted lines; the paper's
  legend is inside upper-left with circle/square/triangle markers.

Decisively, the repository's **own committed figure for the same quantity**,
`benchmarks/results/benchmark_output_dense/figures/Fig_04_estimated_ms_dense_selected.png`,
already shows `Qhr V2X` as the **highest** curve, reaching 9.67 ms at 100×100. The
artifact published alongside the paper contradicts the paper's Figure 3.

### Why no code fix can reproduce it

The published curve is not merely unreproduced; it is unachievable. RDM = PL means
the router expanded exactly the nodes on the final path — zero exploration, every hop
correct on the first attempt, with no prior knowledge of the obstacle layout. That
describes an oracle holding the answer in advance, not a discovery protocol. Any
correct search satisfies RDM ≥ PL, with equality only in an obstacle-free straight
line.

The paper's own Eq. 12 confirms this independently. Back-solving `η` from
`N'_e ≈ (1-η)·N_e`, taking the published curve as `N'_e` and A*'s expansions as `N_e`:

| Grid | 10 | 25 | 50 | 75 | 100 |
| --- | --- | --- | --- | --- | --- |
| implied η | 0.672 | 0.874 | 0.937 | 0.959 | **0.969** |

`η` is a fixed constant in (0,1) in the model. Here it would have to grow with grid
size, so the curve cannot have been produced by the mechanism of Section III-C.

The distinction that matters: the **figure** is unrecoverable, but the **method** is
not. An A* whose node selection is biased by amplitude amplification is sound in
principle; it just never ran here (§2.1). Fixing §2.1–2.3 yields a genuine
constant-factor `(1-η)` reduction below A* — a lower curve of the same shape, not a
flat line.

## 2.9 The reduction is conditional on density and traversal direction

Measured with `experiments/scripts/generate_comparison_charts.py`, which builds
grids at their *nominal* density and draws endpoints from the largest connected
component, so every instance is solvable and the density is the stated one. All
three algorithms share one search skeleton and one counter. 75×75, 10 seeds.

"fwd" runs the instance as generated; "rev" swaps start and goal. Nothing else
differs between the two columns — same grids, same obstacles, same path lengths.

| Density | A* fwd | QHR fwd | reduction | A* rev | QHR rev | reduction |
| --- | --- | --- | --- | --- | --- | --- |
| 2 % | 186.7 | 186.7 | **0.0 %** | 5389.0 | 219.1 | **95.9 %** |
| 5 % | 231.9 | 231.9 | 0.0 % | 5105.3 | 746.8 | 85.4 % |
| 10 % | 430.3 | 430.3 | 0.0 % | 4340.9 | 795.5 | 81.7 % |
| 20 % | 906.8 | 903.5 | 0.4 % | 3289.1 | 1683.8 | 48.8 % |
| 30 % | 1813.3 | 1776.2 | 2.0 % | 1974.9 | 1618.7 | 18.0 % |
| **40 %** | 1394.7 | 1386.2 | **0.6 %** | 1439.7 | 1420.8 | **1.3 %** |

Two things follow, and both bear on the paper's central claim.

**The advantage is a density artifact.** At the 40 % density Table 1 specifies,
the reduction is ~1 %, not the 96 % obtained on the repository's grids. The large
figure depends on the grids being nearly empty — which they are, at 1.6–12 %
(§2.5). Dense obstacle fields fragment the f-plateau that the amplification
exists to collapse, so there is little left to gain.

**Half of it is A*'s own tie-breaking, not the amplification.** A* at 2 % costs
186.7 expansions forward and 5389.0 reversed — 29× worse, on identical grids,
purely because `heapq` orders equal-f entries by node index, which points toward
the goal in one direction and away from it in the other. QHR-V2X's amplification
supplies a goal-directed tie-break, so it recovers that loss where A* suffers it
and adds nothing where A* does not.

The controlling comparison is QHR-V2X against a *well-tie-broken* A*, i.e. the
"rev" QHR column against the "fwd" A* column: 219.1 vs 186.7 at 2 %, 795.5 vs
430.3 at 10 %. **QHR-V2X does not beat an A* that breaks its own f-ties toward
the goal at any density tested.** Goal-directed tie-breaking is a standard
classical technique, so the honest statement of the contribution is that the
amplification of Eqs. 9–11 is equivalent to it — not that it outperforms A*.

This also explains §2.3's finding that the measured reduction grows with grid
size rather than holding at the constant `(1-η)` of Eq. 12: what grows is the
f-plateau, and with it the size of A*'s tie-breaking loss.

## 2.10 Corner-to-corner queries are unusable at 40 % density

Independently found while preparing the artifact. For uniform random obstacles at 40 %, the
free-cell fraction of 0.60 sits just above the 2-D site-percolation threshold
p_c ≈ 0.5927, so opposite corners of a large grid are almost never connected —
no connected corner pair in 200 draws at 75×75.

This makes the §2.5 recommendation ("fix the generator to hit 20 %/40 %")
insufficient on its own: correcting the density alone would leave most instances
unsolvable. `generate_comparison_charts.py` handles it by drawing endpoints from
the largest connected component via a BFS double sweep, keeping every instance
solvable at the nominal density. Clustered rather than uniform obstacles would
be another option and is arguably closer to an urban layout.

## 3. Summary

The reproduction splits cleanly. Everything in the paper that does not depend on the
quantum mechanism reproduces exactly: both baselines on all four RDM/RDT figures,
and all path lengths. Everything that does depend on it does not.

The headline claim — that QHR-V2X reduces RDM and RDT relative to A* and Dijkstra —
is not supported by this code. Two defects in `_quantum_amplitude_amplification`
reduce it to plain A* node selection, and an inconsistent RDM definition then makes
that plain-A* behaviour *look* 2× worse than A* rather than equal to it. Corrected
for the counting inconsistency, QHR-V2X expands 1.00–1.03× the nodes A* does. The
published near-zero QHR-V2X curve is not an output of this repository at any
revision reachable from `main`.

### Recommended fixes, in dependency order

1. Bind `last_qubit = num_qubits - 1` before the diffusion block
   (`src/qhr_v2x.py:79`), and replace `measure_all()` with
   `qc.measure(range(num_qubits), range(num_qubits))` so a single register is read
   back (`src/qhr_v2x.py:89`).
2. Narrow `except (QiskitError, Exception)` to `except QiskitError` so silent
   fallbacks stop hiding defects.
3. Make RDM a single shared helper used by all three algorithms — pops only, or
   pops+pushes for all — so the metric is comparable.
4. Implement Eqs. 9–11 (`T`, `η`, softmax, renormalise) as the selection rule if
   that is the intended contribution, and expose `η` so Eq. 12 can be tested.
5. Fix the density generators to hit the stated 20% / 40% independent of grid size,
   and randomise the sparse layout.
6. Add the 20-seed repetition loop from Table 1 and report mean ± std.

Items 1–3 are prerequisites for any re-run: until RDM is counted consistently, no
QHR-V2X-versus-baseline comparison is meaningful.
