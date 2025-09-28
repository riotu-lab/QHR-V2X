# Experimental Setup and Reproduction Guide

This document provides detailed instructions for reproducing the experimental results from the QHR-V2X paper.

## 📋 Table of Contents

- [Overview](#overview)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Running Experiments](#running-experiments)
- [Understanding Results](#understanding-results)
- [Statistical Analysis](#statistical-analysis)
- [Troubleshooting](#troubleshooting)

## 🎯 Overview

This repository implements the **QHR-V2X (Quantum-Heuristic Routing for V2X)** framework and provides tools to reproduce all experimental results from the research paper:

> **"QHR-V2X: A Quantum-Heuristic Routing Framework for Efficient V2X Path Discovery"**  
> *Khan, Z., Almogbil, S., Babar, M., Ammar, A., & Boulila, W.*  
> *Prince Sultan University, RIOTU Laboratory*

### Key Features

- ✅ **Complete algorithm implementations** (QHR-V2X, Dijkstra, A*, quantum variants)
- ✅ **Reproducible experiments** with fixed random seeds
- ✅ **Statistical analysis tools** for research validation
- ✅ **Publication-ready visualizations**
- ✅ **Performance benchmarking** across multiple grid sizes and obstacle densities

## 💻 System Requirements

### Hardware Requirements
- **CPU**: Multi-core processor (recommended: 4+ cores)
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 2GB free space for results and figures

### Software Requirements
- **Python**: 3.11.5 (required for optimal performance)
- **Operating System**: Linux, macOS, or Windows
- **Git**: For cloning the repository

### Python Dependencies
- `numpy` >= 1.24.0
- `matplotlib` >= 3.7.0
- `pandas` >= 2.0.0
- `qiskit` >= 0.44.0
- `qiskit-aer` >= 0.12.0
- `scipy` >= 1.10.0
- `seaborn` >= 0.12.0

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/[your-username]/QHR-V2X.git
cd QHR-V2X
```

### 2. Install Dependencies

We use Poetry for dependency management:

```bash
# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install

# Verify installation
poetry run python --version  # Should show Python 3.11.5
```

### 3. Verify Quantum Backend

```bash
# Test quantum backend availability
poetry run python -c "from qiskit_aer import AerSimulator; print('Quantum backend ready')"
```

## 🧪 Running Experiments

### Quick Start: Reproduce Paper Results

```bash
# Run all experiments from the paper
poetry run python experiments/scripts/reproduce_paper_results.py
```

This will:
- ✅ Run experiments on both dense (40%) and sparse (20%) obstacle environments
- ✅ Test all algorithms: QHR-V2X, Dijkstra, A*, and quantum variants
- ✅ Generate CSV files with raw results
- ✅ Create summary reports
- ✅ Save results to `experiments/results/paper_reproduction/`

### Custom Experiments

```bash
# Test specific algorithms only
poetry run python experiments/scripts/reproduce_paper_results.py --algorithms qhr_v2x,dijkstra,astar

# Custom output directory
poetry run python experiments/scripts/reproduce_paper_results.py --output-dir my_results

# Enable verbose output
poetry run python experiments/scripts/reproduce_paper_results.py --verbose
```

### Individual Algorithm Testing

```bash
# Quick algorithm comparison
poetry run python main.py compare qhr_v2x qhr_v2x_classical

# Test specific algorithms
poetry run python main.py selective qhr_v2x dijkstra astar

# Run full benchmark suite
poetry run python main.py benchmark
```

## 📊 Understanding Results

### Experimental Design

The experiments follow the paper's methodology:

| Parameter | Value |
|-----------|-------|
| **Grid Sizes** | 10×10, 20×20, 30×30, 40×40, 50×50 (sparse)<br/>10×10, 25×25, 50×50, 75×75, 100×100 (dense) |
| **Obstacle Density** | 20% (sparse), 40% (dense) |
| **Start Position** | (0, 0) |
| **Goal Position** | Bottom-right corner |
| **Random Seed** | Fixed (12345) for reproducibility |

### Performance Metrics

| Metric | Description | Unit |
|--------|-------------|------|
| **RDM** | Route Discovery Messages | Count |
| **PL** | Path Length | Steps |
| **RDT** | Route Discovery Time | Milliseconds |
| **Estimated Time** | Theoretical complexity estimate | Milliseconds |

### Output Files

After running experiments, you'll find:

```
experiments/results/paper_reproduction/
├── dense_results.csv              # Dense environment results
├── sparse_results.csv             # Sparse environment results
├── experiment_summary.md          # Summary report
└── figures/                       # Generated plots
    ├── performance_comparison_dense.png
    ├── performance_comparison_sparse.png
    ├── scalability_analysis_dense.png
    └── scalability_analysis_sparse.png
```

## 📈 Statistical Analysis

### Automated Analysis

```bash
# Run comprehensive statistical analysis
poetry run python experiments/analysis/analyze_results.py
```

This generates:
- ✅ **Statistical tests** (ANOVA, t-tests)
- ✅ **Performance comparison plots**
- ✅ **Scalability analysis**
- ✅ **Publication-ready figures**

### Analysis Output

```
experiments/analysis/results/
├── performance_comparison_dense.png
├── performance_comparison_sparse.png
├── scalability_analysis_dense.png
├── scalability_analysis_sparse.png
└── statistical_analysis.md
```

### Key Statistical Tests

1. **ANOVA**: Tests for significant differences between algorithms
2. **Pairwise t-tests**: Compares specific algorithm pairs
3. **Bonferroni correction**: Controls for multiple comparisons
4. **Effect size analysis**: Quantifies practical significance

## 🔬 Research Validation

### Reproducibility Checklist

- ✅ **Fixed random seeds** ensure identical results across runs
- ✅ **Version-controlled dependencies** via Poetry lock file
- ✅ **Documented system requirements** and installation steps
- ✅ **Automated experiment scripts** reduce manual errors
- ✅ **Statistical validation** confirms significance of results

### Expected Results

Based on the paper, you should observe:

1. **QHR-V2X outperforms classical algorithms** in RDM (Route Discovery Messages)
2. **Similar path lengths** across all algorithms (optimality maintained)
3. **Improved scalability** for QHR-V2X in larger grids
4. **Statistical significance** in performance differences

### Validation Commands

```bash
# Verify QHR-V2X implementation
poetry run python main.py compare qhr_v2x qhr_v2x_classical

# Check quantum backend functionality
poetry run python -c "from src.qhr_v2x import qhr_v2x; print('QHR-V2X ready')"

# Validate experimental setup
poetry run python experiments/scripts/reproduce_paper_results.py --algorithms qhr_v2x --verbose
```

## 🐛 Troubleshooting

### Common Issues

#### 1. **Quantum Backend Errors**
```bash
# Error: Qiskit backend not available
# Solution: Install Qiskit Aer
poetry add qiskit-aer
```

#### 2. **Memory Issues with Large Grids**
```bash
# Error: Out of memory on 100×100 grids
# Solution: Reduce grid size or increase system memory
poetry run python experiments/scripts/reproduce_paper_results.py --algorithms qhr_v2x,dijkstra
```

#### 3. **Slow Quantum Simulation**
```bash
# Quantum algorithms are slower on classical hardware
# This is expected - quantum simulation has overhead
# For faster testing, use classical algorithms only
poetry run python main.py selective dijkstra astar
```

#### 4. **Missing Dependencies**
```bash
# Error: ModuleNotFoundError
# Solution: Reinstall dependencies
poetry install --sync
```

### Performance Tips

1. **For quick testing**: Use smaller grid sizes (10×10, 20×20)
2. **For full reproduction**: Allow 30-60 minutes for complete experiments
3. **For quantum algorithms**: Expect 2-3x slower execution due to simulation overhead
4. **For large-scale testing**: Use classical algorithms for baseline comparisons

### Getting Help

If you encounter issues:

1. **Check the logs**: Run with `--verbose` flag
2. **Verify installation**: `poetry run python --version`
3. **Test individual components**: Use `main.py` commands first
4. **Report issues**: Create an issue on GitHub with:
   - System information
   - Error messages
   - Steps to reproduce

## 📚 Additional Resources

- **Paper**: [QHR-V2X: A Quantum-Heuristic Routing Framework for Efficient V2X Path Discovery]
- **Citation**: See [CITATION.md](CITATION.md) for proper citation format
- **Algorithm Details**: See [src/qhr_v2x.py](src/qhr_v2x.py) for implementation
- **Benchmarking**: See [tests/test_pathfinding_all.py](tests/test_pathfinding_all.py) for test framework

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines for:
- Code style and standards
- Testing requirements
- Documentation updates
- Bug reports and feature requests

---

**For questions about this experimental setup, please contact the authors or open an issue on GitHub.**
