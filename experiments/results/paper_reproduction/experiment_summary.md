# QHR-V2X Paper Reproduction Results

**Generated on**: 2025-09-28 13:42:41

**Algorithms tested**: qhr_v2x, dijkstra

## Experimental Setup

- **Grid sizes**: 10×10, 20×20, 30×30, 40×40, 50×50 (sparse) / 10×10, 25×25, 50×50, 75×75, 100×100 (dense)
- **Obstacle densities**: 20% (sparse), 40% (dense)
- **Performance metrics**: Route Discovery Time (RDT), Route Discovery Messages (RDM), Path Length (PL)
- **Simulation environment**: Python 3.11 + Qiskit

## Results Summary

### Dense Environment Results

**qhr_v2x**:
- Average RDM: 3614.99
- Average PL: 75.55
- Average RDT: 71.555 ms

**dijkstra**:
- Average RDM: 3337.82
- Average PL: 75.55
- Average RDT: 5.120 ms


### Sparse Environment Results

**qhr_v2x**:
- Average RDM: 914.90
- Average PL: 47.13
- Average RDT: 273.835 ms

**dijkstra**:
- Average RDM: 901.11
- Average PL: 47.13
- Average RDT: 1.356 ms


## Files Generated

- `dense_results.csv`: Dense environment results
- `sparse_results.csv`: Sparse environment results
- `experiment_summary.md`: This summary report
- `figures/`: Generated visualization plots

## Reproducibility

To reproduce these results:

```bash
python experiments/scripts/reproduce_paper_results.py
```

For detailed analysis and visualization:

```bash
python experiments/analysis/analyze_results.py
```
