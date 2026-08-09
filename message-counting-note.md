# Note on message counting in the QHR-V2X comparison

**Prepared while getting the repository ready for public use.**

While setting up the reproduction scripts I found that the three algorithms measure their
message counts in different ways. This note records what the difference is, what effect it has on
the charts, and a few options for how we might want to handle it.

---

## 1. Summary

The three implementations each return a number they call messages, but they count different
events. Because of that, the three series in the RDT and RDM charts are not measuring the same
quantity, and the gap between them partly reflects the counting rule rather than the algorithms.

When all three are counted the same way, QHR-V2X and A\* come out equal.

---

## 2. What the three counters currently do

| Implementation | What it counts |
| --- | --- |
| `src/astar_u.py` | nodes taken off the queue |
| `src/dijkstra_grid_u.py` | nodes taken off the queue, skipping stale entries |
| `src/qhr_v2x.py` | nodes taken off the queue **and** nodes put on it |

On a single 15×15 grid, running searches that behave identically, these return **174**, **174** and
**347**.

A second convention also appears to be in play. Reading the QHR-V2X points off Figure 3 and
dividing by the `time_complexity_factor` of 0.001 gives roughly 20, 50, 90, 140 and 180 messages at
the five grid sizes. Those values are close to the *path lengths* at those sizes (13.5, 36, 71.8,
109.6, 146.9), which suggests QHR-V2X may be counted along its discovered route while A\* and
Dijkstra are counted by nodes examined during the search.

That is worth confirming, because it is the largest single factor in the shape of the chart.

---

## 3. What difference it makes

At a 100×100 grid with dense obstacles:

- A\* examines about 5,800 nodes and returns a route of about 280 hops.
- QHR-V2X examines about 5,800 nodes and returns a route of about 280 hops.

Both do the same work and return the same route. If one is plotted using 5,800 and the other using
280, the chart shows a 20× gap. That gap is the difference between a search and a route, and it
would appear for any algorithm measured that way — including A\*.

`experiments/results/figures/Supp_rdm_model_dense.png` shows this directly. The left panel counts
all three the same way; the right panel counts QHR-V2X along its route and the other two by nodes
examined. The right panel reproduces the shape of Figure 3.

---

## 4. Why QHR-V2X and A\* come out equal when counted the same way

This part is independent of the counting question, so it is worth separating out.

Algorithm 1 step 4 selects the candidate with the highest amplified probability. Working through
Eqs. (9)–(11):

1. Eq. 9 gives `P_i ∝ exp(−f_i / T)`, so the lowest-cost candidate starts with the highest
   probability.
2. Eq. 10 multiplies below-average candidates by `(1 + η)` and the rest by `(1 − η)`. The lowest
   cost is always below average, so it receives the larger factor.
3. Eq. 11 rescales everything by a positive constant, which preserves the ordering.

So the highest amplified probability always belongs to the lowest-`f` candidate — which is what A\*
selects. This holds for any `T`, any `η`, and any number of amplification rounds.

The measurements agree: identical message counts and identical node expansions at every grid size
in both densities, and an expansion ratio of 1.0000 where Eq. 12 anticipates `1 − η` = 0.70.

**A small related point.** The Qiskit block in `src/qhr_v2x.py` currently returns the classical
choice rather than the circuit result. The circuit is created with `QuantumCircuit(n, n)` and
measured with `measure_all()`, which adds a second register, so the result comes back as
`'0010 0000'` and `int(key, 2)` raises a `ValueError` that the surrounding `except` absorbs. This
happens on every call, on both the pinned Qiskit version and the current one. It does not change any
result — the fallback is the same node the selection rule would pick — but it does account for the
runtime, which is roughly a thousand times A\*'s for the same route.

---

## 5. Charts

Regenerated from 20 seeds per grid size, with all three algorithms counted identically:

| File | Shows |
| --- | --- |
| `Fig3_dense.png` … `Fig8_sparse.png` | The Section IV figures, same titles and axes |
| `Supp_rdm_model_dense.png` | Side-by-side of the two counting conventions |
| `Supp_Eq12_check_dense.png` | Measured expansion ratio against Eq. 12 |
| `Supp_measured_time_dense.png` | Measured wall-clock time, separate from estimated RDT |
| `Supp_solvability_vs_density.png` | How often a random grid at a given density has a route |

All under `experiments/results/figures/`. Numbers are in `experiments/results/comparison_summary.md`.

---

## 6. Two smaller things found along the way

**Obstacle density.** `tests/test_pathfinding_all.py` places `int(size * density)` obstacles. Since
the cell count grows quadratically and the obstacle count linearly, the realised density falls with
grid size — about 12% at 10×10 and 1.6% at 100×100, against a nominal 40%. Changing it to
`int(size * size * density)` gives the intended density.

**Endpoint selection.** At a true 40% density, opposite corners of a large grid are usually not
connected, because the free-cell fraction of 0.60 sits close to the percolation threshold for a
square lattice (about 0.593). At 75×75 I found no connected corner pair in 200 draws. The
regenerated charts draw start and goal from the largest connected region instead, which keeps every
instance solvable. Clustered rather than uniform obstacles would be another reasonable option and
may be closer to an urban layout.

---

## 7. Suggested next steps

Roughly in order of how much they need deciding:

1. **Confirm the counting convention.** Was QHR-V2X counted along its route while the baselines were
   counted by nodes examined? This one question determines most of what follows.
2. **Settle on one convention and apply it to all three.** Either works — nodes examined suits a
   protocol that floods, route hops suit one that forwards only along its answer. It just needs to be
   the same for every algorithm.
3. **Separate estimated RDT from measured time.** At the moment `estimated_ms = avg_msgs × 0.001`,
   so the RDT and RDM charts are the same curve at different scales. Reporting measured time
   alongside would give two independent readings.
4. **Decide the direction for the selection rule.** Given that argmax over Eqs. (9)–(11) matches A\*,
   the options are roughly: treat `η` as an explicit quality-versus-effort trade-off, in the manner
   of Weighted A\*; restrict the mechanism to breaking ties between equal-cost candidates; or apply
   it in the dynamic setting of Section II-C, where keeping several candidate routes has clear value
   because links change. The third looks the most promising and is closest to the V2X motivation.
5. **Add a few correctness checks.** The current tests verify the shape of the results dictionary.
   Checking that returned paths are valid, avoid obstacles, and match Dijkstra's length would catch
   this class of thing early.

---

## 8. Reproducing the charts

```bash
pip install numpy matplotlib
python experiments/scripts/generate_comparison_charts.py --seeds 20 --repeats 3
```

Add `--include-repo-impl` to include the current `src/qhr_v2x.py` in the timing chart (needs Qiskit,
and takes a few minutes), or `--include-stochastic` to also measure sampling from the amplified
distribution rather than taking its maximum.
