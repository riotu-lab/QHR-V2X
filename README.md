# 🚀 Pathfinding Algorithm Comparison Project

**A comprehensive comparison of classical and quantum-enhanced pathfinding algorithms for grid-based navigation.**

> **📄 Paper Alignment**: This project implements and validates the algorithms described in **"QHR-V2X: A Quantum-Heuristic Routing Framework for Efficient V2X Path Discovery"** by Khan et al. (Prince Sultan University, 2024).

## 📖 What This Project Does

This project implements and compares **9 different pathfinding algorithms** on grid-based maps:

### 🔧 **Classical Algorithms** (Fast & Reliable)
- **Dijkstra's Algorithm** - Finds the shortest path between two points
- **A* Search** - Smart search that uses heuristics to find paths faster
- **Grover Classic** - Classical implementation of Grover's quantum algorithm

### 🔬 **Quantum-Enhanced Algorithms** (Research & Future)
- **QHR-V2X** - Quantum-Heuristic Routing for V2X (main paper contribution)
- **QHR-V2X Classical** - Classical baseline for QHR-V2X comparison
- **Quantum Dijkstra** - Quantum-enhanced version of Dijkstra
- **Quantum A*** - Quantum-enhanced A* search
- **Continuous Quantum Walk (CQW)** - Uses quantum mechanics for pathfinding
- **Vectorized CQW** - Optimized version of quantum walk
- **Quantum Grover BFS** - Quantum-enhanced breadth-first search

## 🎯 What Problem Does This Solve?

Imagine you have a **grid map** (like a video game world) with:
- 🟢 **Start point** (where you are)
- 🟡 **Goal point** (where you want to go)
- ⬛ **Obstacles** (walls, trees, enemies blocking the way)

**The algorithms find the best path from start to goal while avoiding obstacles.**

## 📄 **Research Paper Implementation**

This project implements the **QHR-V2X (Quantum-Heuristic Routing for V2X)** framework described in the research paper:

> **"QHR-V2X: A Quantum-Heuristic Routing Framework for Efficient V2X Path Discovery"**  
> *Zahid Khan, Sultan Almogbil, Muhammad Babar, Adel Ammar, and Wadii Boulila*  
> *Robotics and Internet-of-Things (RIOTU) Laboratory, Prince Sultan University*

### **Implemented**
- ✅ **Grid-based route discovery** in sparse and dense topologies
- ✅ **Grid sizes**: 10×10 to 100×100, as in the paper
- ✅ **Metrics**: Route Discovery Time (RDT), Route Discovery Messages (RDM), Path Length (PL)
- ✅ **Amplitude amplification** (Eqs. 9–11) biasing A* node selection, with an
  optional Grover circuit on the Qiskit AerSimulator
- ✅ **Classical baselines**: Dijkstra and A*
- ✅ **Python 3.11 + Qiskit**, as in the paper
- ✅ **Benchmark harness** with CSV export, 40 generated figures, seeded replay

### **Not yet implemented — see [VERIFICATION.md](VERIFICATION.md)**
- ⚠️ **Obstacle density**: the generators realise 1.6–12% obstacles, not the 20%
  and 40% stated in Table 1, and the density falls as the grid grows
- ⚠️ **Link-cost model** of Eq. 2 (`α·d + β·τ + γ·(1−R)`): every edge costs one
  hop; link reliability, SNR, transmission range and the mobility models of
  Eqs. 3–6 are absent
- ⚠️ **Repetitions**: one run per configuration, not Table 1's 20 independent
  seeds, so no variance is reported

## 🚀 Quick Start (5 minutes to running!)

### 1. **Install & Setup**
```bash
# Using Poetry (recommended)
poetry install

# Or using the setup script
./setup.sh
```

### 2. **Reproduce Paper Results**
```bash
# Paper Figures 3-8, from a clean checkout, in one command.
# Runs the algorithms, writes the CSVs, then draws the figures.
make figures

# Complete pipeline (install, tests, figures, statistical analysis)
make all

# Or step by step
make reproduce    # Run the algorithms and export benchmark CSVs
make figures      # Reproduce, then generate paper Figures 3-8
make analyze      # Run statistical analysis
```

**Where the figures land:** `experiments/results/paper_figures/Figure_{3..8}_*.png`

For every other view of the same data — log scales, bar charts, per-mode overview
panels, overhead relative to A*, and a colour-vision-safe palette — run:

```bash
make figures-all   # 40 figures total: the 6 above + 34 more
```

These land in `experiments/results/all_figures/`, alongside a generated
`MANIFEST.md` describing every file. That directory is not tracked — it is rebuilt
from the algorithms on each run.

`make figures` depends on `make reproduce`, so the figures are always drawn from a
fresh benchmark run rather than a stale CSV. `make clean` removes every generated
artifact, including `benchmarks/results/`. Nothing in the figure pipeline is
hard-coded: every plotted point comes from a live call to the algorithm under test,
and `paper_figures.py` prints all plotted values so each point can be checked
against the figure.

### Seeds

By default each run draws a **fresh** obstacle layout, so repeated runs explore
different grids. The seed used is printed and written to the `seed` column of the
results CSV, so any run can be replayed exactly:

```bash
make figures                    # fresh layout each time (default)
make figures SEED=paper         # the grids behind the published figures
make figures SEED=4102968646    # replay a specific earlier run
```

Sparse mode is deterministic by construction — its obstacles are a partial wall in
column `size // 3` — so the seed only affects dense mode. With a fixed seed,
`msgs` and `path_len` are identical across runs; measured `time_ms` still varies
with machine load, as expected.

### Line style

```bash
make figures                    # straight (default)
make figures STYLE=curved       # smooth, matching the published figures
```

`SEED` and `STYLE` combine freely:

```bash
make figures SEED=paper STYLE=curved   # closest to the published figures
make figures-all SEED=paper            # all 40, published layout, straight
```

`straight` joins the measured points with segments, so nothing is drawn that was
not measured. `curved` smooths with a monotone cubic (PCHIP) for the look of the
published figures; PCHIP is used instead of a natural cubic spline because it
cannot overshoot — with only five grid sizes per curve, a natural spline can bulge
past the surrounding points and imply a peak that was never measured. Markers sit
on the measured values under either style. Curved output gets a `_curved` suffix,
so both can coexist.

> **Reproduction status.** With `SEED=paper`, the A* and Dijkstra series reproduce
> the published values exactly, and all three series in Figures 5 and 8 do too.
> QHR-V2X is the lowest curve in Figures 3, 4, 6 and 7, matching the published
> ordering. Its absolute values differ from the published ones — see
> [VERIFICATION.md](VERIFICATION.md) §0 for what was fixed to get there, and
> §2.4–2.6 for the Table 1 parameters still not implemented.

### 3. **Quick Testing**
```bash
poetry run python main.py help      # See all available commands
poetry run python main.py demo      # Try a simple example
poetry run python main.py test      # Test basic algorithms
poetry run python main.py quantum   # Test quantum algorithms
poetry run python main.py benchmark # Run full performance tests
```

## 📁 Project Structure Explained

```
QHR-V2X/
├── 📁 src/                           # 🧠 Algorithm implementations (9 files)
│   ├── dijkstra_grid_u.py           # Classic shortest path
│   ├── astar_u.py                   # Smart A* search
│   ├── grover_classic.py            # Classical Grover
│   ├── qhr_v2x.py                   # QHR-V2X (main paper contribution)
│   ├── dijkstra_quantum_enhanced.py # Quantum Dijkstra
│   ├── astar_u_quantum.py          # Quantum A*
│   ├── cqw_quantum.py              # Quantum walk
│   ├── cqw_vectorized.py           # Fast quantum walk
│   └── grover_quantum_bfs.py       # Quantum BFS
├── 📁 tests/                         # 🧪 Testing and benchmarking (2 files)
│   ├── test_pathfinding_all.py     # Full benchmark suite
│   └── test_pathfinding_modes.py   # Different test modes
├── 📁 experiments/                   # 🔬 Research pipeline
│   ├── 📁 analysis/                 # Statistical analysis
│   │   ├── analyze_results.py      # Analysis script
│   │   └── results/                # Generated figures & analysis
│   ├── 📁 results/                  # Experimental data
│   │   └── paper_reproduction/     # Paper reproduction results
│   └── 📁 scripts/                  # Reproduction scripts
│       └── reproduce_paper_results.py # Main reproduction script
├── 📄 main.py                        # 🚀 Main project entry point
├── 📄 Makefile                       # 🛠️ Automation commands
├── 📄 setup.sh                       # 🔧 Installation script
├── 📄 CITATION.cff                   # 📖 Citation metadata
├── 📄 LICENSE                        # ⚖️ MIT License
├── 📄 REPRODUCE.md                   # 🔬 How to reproduce the figures
├── 📄 VERIFICATION.md                # 🔍 What reproduces, and what does not
├── 📄 pyproject.toml                 # 📦 Poetry dependencies
├── 📄 poetry.lock                    # 🔒 Locked dependency versions
└── 📄 README.md                      # 📚 This file
```

## 🎮 How to Use (Step by Step)

### **Option 1: Simple Demo (Recommended for first time)**
```bash
poetry run python main.py demo
```
**What happens:** Creates a small 8x8 grid, shows you the map, and runs 3 algorithms to find a path.

### **Option 2: Test Basic Algorithms**
```bash
poetry run python main.py test
```
**What happens:** Tests Dijkstra and A* on a 5x5 grid, shows you the path found and how many "messages" were sent.

### **Option 3: Test Quantum Algorithms**
```bash
poetry run python main.py quantum
```
**What happens:** Tests quantum algorithms on a 4x4 grid. Note: These may be slower on regular computers.

### **Option 4: Full Benchmarking**
```bash
poetry run python main.py benchmark
```
**What happens:** Runs all algorithms on grids from 10x10 to 100x100, generates performance reports, CSV files, and charts.

### **Option 5: Selective Benchmarking (Recommended)**
```bash
poetry run python main.py selective dijkstra astar astar_quantum
```
Or shortcut via Poetry:
```bash
poetry run bench-select dijkstra astar astar_quantum
```

### **Option 6: One-shot Pipeline (Clean → Run → PDF)**
```bash
# Run paper reproduction pipeline
poetry run python experiments/scripts/reproduce_paper_results.py
```
This reproduces all experimental results and generates comprehensive analysis under `experiments/analysis/results/`.

## 🔍 Understanding the Output

### **Grid Visualization**
```
S . . . . . . . G    S = Start point
. . █ . . . . . .    G = Goal point  
. . . . █ . . . .    █ = Obstacle
. . . . . . . . .    . = Free space
. . █ . . . . . .    * = Path found
. . . . . . . . .
. . . . . . . . .
. . . . . . . . .
```

### **Algorithm Results**
```
✅ Dijkstra: Path found! Length: 12, Messages: 45
   Path: [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (6, 0), (7, 0), (7, 1), (7, 2), (7, 3), (7, 4), (7, 5), (7, 6), (7, 7)]
```

**What this means:**
- **Length: 12** = Path has 12 steps (excluding start)
- **Messages: 45** = Algorithm sent 45 internal messages
- **Path** = List of coordinates from start to goal

## 📊 Benchmarking Explained

### **What Gets Tested**
- **Grid Sizes**: 10x10, 20x20, 30x30, 40x40, 50x50, 60x60, 70x70, 80x80, 90x90, 100x100
- **Density Modes**:
  - **Dense**: 40% obstacles (harder to find paths)
  - **Sparse**: 20% obstacles (easier to find paths)

### **What Gets Measured**
- **Messages**: How many internal communications
- **Path Length**: How long the found path is
- **Execution Time**: How long the algorithm takes
- **Complexity Estimate**: Theoretical performance

### **Output Files**
- **CSV files**: Raw data for analysis (organized in `experiments/results/`)
- **PNG charts**: Visual comparisons (organized in `experiments/analysis/results/`)
- **Markdown reports**: Summary of results (organized in `experiments/analysis/results/`)
- **Statistical analysis**: Complete analysis reports (generated in `experiments/analysis/results/`)

**All results are automatically organized in the proper directories - no more messy root folder!**

## 🔬 Quantum Computing Notes

### **What You Need to Know**
- **Qiskit**: IBM's quantum computing framework
- **Qiskit-Aer**: Quantum circuit simulator (runs on your computer)
- **Simulation**: We're running quantum algorithms on regular computers (simulating quantum behavior)
- **Performance**: Quantum algorithms may be slower on classical hardware due to simulation overhead
- **Research**: These demonstrate theoretical advantages for future quantum computers

### **📚 Learning Qiskit-Aer**

**New to quantum computing or qiskit-aer?** We've created comprehensive guides:

- **[examples/qiskit_aer_example.py](examples/qiskit_aer_example.py)** - Runnable example demonstrating quantum pathfinding

**Quick Installation:**
```bash
pip install qiskit-aer
# or
poetry add qiskit-aer
```

**Test your installation:**
```bash
poetry run python examples/qiskit_aer_example.py
```

### **Environment Variables**
```bash
export CQW_MAX_QPOS=20      # Maximum position qubits
export CQW_SHOT_CAP=256     # Maximum simulator shots
export CQW_LOG_LEVEL=WARNING # Logging level
```

## 🐛 Troubleshooting

### **Common Issues & Solutions**

#### 1. **"No module named 'numpy'"**
```bash
poetry install
```

#### 2. **"Import error"**
Make sure you're running from the project directory:
```bash
cd pathfinding-algorithms
poetry run python main.py help
```

#### 3. **"Qiskit not found"**
```bash
poetry install
```

#### 4. **"Start or goal on obstacle"**
This means the random obstacle generation blocked the start/goal. The algorithms handle this automatically.

### **Performance Tips**
- **Small grids** (< 20x20): All algorithms work well
- **Medium grids** (20x20 - 50x50): Classical algorithms are fastest
- **Large grids** (> 50x50): Consider using classical algorithms for practical use
- **Quantum algorithms**: Best for research and understanding quantum concepts

## 🏗️ **Project Organization (NEW!)**

### **Professional Structure**
This project now follows **industry-standard organization**:
- **Clean root directory** - No more scattered files
- **Logical grouping** - Related files are together
- **Easy navigation** - Know exactly where to find anything
- **Scalable design** - Easy to add new features

### **Directory Purposes**
- **`src/`** - All algorithm implementations
- **`tests/`** - Testing and validation framework
- **`experiments/`** - Complete research pipeline with analysis

## 🎓 Learning Path

### **Beginner (Start Here)**
1. `python main.py demo` - See how it works
2. `python main.py test` - Understand basic algorithms
3. Read the grid visualization output

### **Intermediate**
1. `python main.py quantum` - Explore quantum algorithms
2. Look at the source code in `src/` folder
3. Understand how different algorithms work

### **Advanced**
1. `python main.py benchmark` - Run full performance tests
2. Analyze the CSV results and charts
3. Modify algorithms in `src/` folder
4. Create your own test scenarios

## 🔧 Technical Details

### **Grid Representation**
- **NumPy arrays**: `True` = obstacle, `False` = free space
- **4-connectivity**: Only move up, down, left, right (no diagonals)
- **Coordinates**: (row, column) starting from (0, 0)

### **Algorithm Complexity**
- **Dijkstra**: O(V²) where V = number of vertices
- **A***: O(V log V) with admissible heuristic
- **Quantum**: Theoretical O(√N) for certain problem classes

### **File Formats**
- **Input**: NumPy boolean arrays
- **Output**: Tuple of (path, messages)
- **Path**: List of (row, col) coordinates
- **Messages**: Integer count of internal communications

## 🤝 Contributing

This is a research project demonstrating various pathfinding approaches. Feel free to:
- Experiment with different grid sizes
- Modify algorithm parameters
- Add new test scenarios
- Improve the visualization

## 📄 License

This appears to be academic/research work. Please check with the original authors for licensing information.

## 🆘 Getting Help

### **If Something Goes Wrong**
1. Check the troubleshooting section above
2. Make sure all dependencies are installed
3. Verify you're in the correct directory
4. Look at the error messages for clues

### **For More Information**
- Read the source code in the `src/` folder
- Check the experimental results in the `experiments/` folder
- Look at the test outputs for debugging information

---

## 🎉 **You're Ready to Go!**

**Start with:** `poetry run python main.py demo`

**This will show you exactly how the pathfinding algorithms work on a real example!**

**The project is now clean, organized, and follows modern Python conventions with Poetry dependency management!** 🚀

## 🐍 **Python Version Requirement**
**This project requires Python 3.11.5** for optimal performance and modern features.

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

Machine-readable metadata is in [`CITATION.cff`](CITATION.cff); GitHub renders it
as "Cite this repository".
