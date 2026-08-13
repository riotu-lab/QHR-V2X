# QHR-V2X Research Repository Makefile
# =====================================
# 
# This Makefile provides convenient commands for reproducing
# research results and managing the academic codebase.

.PHONY: help install test clean reproduce analyze figures figures-all all \
        figures-nominal lint format dev-setup validate docs status

# How every target below invokes Python.
#
# Resolved in order: Poetry if it is actually installed (the documented setup),
# then a project-local .venv, then plain python3. Previously this was hard-coded
# to `poetry run python`, which meant a machine without Poetry failed with a bare
# `poetry: Permission denied` and no hint about what to do.
#
# Override explicitly whenever you want a specific interpreter:
#
#   make figures SEED=paper PY=.venv/bin/python
#   make figures SEED=paper PY=/usr/bin/python3.11
#
# Dev tools run as `$(PY) -m <tool>`, so they follow the same choice.
PY ?= $(shell \
	if command -v poetry >/dev/null 2>&1; then echo 'poetry run python'; \
	elif [ -x .venv/bin/python ]; then echo '.venv/bin/python'; \
	else echo 'python3'; fi)

# Default target
help:
	@echo "QHR-V2X Research Repository Commands"
	@echo "===================================="
	@echo ""
	@echo "Setup Commands:"
	@echo "  make install     - Install all dependencies"
	@echo "  make test        - Run basic algorithm tests"
	@echo ""
	@echo "Research Commands:"
	@echo "  make reproduce   - Reproduce all paper results"
	@echo "  make analyze     - Run statistical analysis"
	@echo "  make figures     - Reproduce results, then generate paper Figures 3-8"
	@echo "  make figures-all - Generate all 40 figures (6 paper + 34 others)"
	@echo "                     SEED=paper|<int>   published or specific layout"
	@echo "                     STYLE=curved       smooth lines (default straight)"
	@echo "  make figures-nominal"
	@echo "                   - The same six figures at Table 1's stated 20%/40%"
	@echo "                     density over 20 seeds. Does NOT match the"
	@echo "                     published figures -- see VERIFICATION.md 2.5"
	@echo "  make all         - Run complete research pipeline"
	@echo ""
	@echo "Utility Commands:"
	@echo "  make clean       - Clean generated files"
	@echo "  make lint        - Run code linting"
	@echo "  make format      - Format code"
	@echo ""

# Installation
install:
	@echo "📦 Installing dependencies..."
	poetry install
	@echo "✅ Installation complete!"

# Basic testing
test:
	@echo "🧪 Running basic algorithm tests..."
	$(PY) main.py test
	$(PY) main.py compare qhr_v2x qhr_v2x_classical
	@echo "✅ Tests completed!"

# Reproduce paper results
# Restricted to the three algorithms the paper compares, so the CSV that feeds
# the figures contains exactly the published series.
#
# SEED is unset by default, so each run draws a fresh obstacle layout and the
# seed it used is printed and written to the CSV. Override to replay a run:
#   make reproduce SEED=paper     # the grids behind the published figures
#   make reproduce SEED=12345     # any specific seed
SEED ?=
SEED_ARG = $(if $(SEED),--seed $(SEED),)

# STYLE selects how the figure points are joined: straight (default) or curved.
#   make figures STYLE=curved
STYLE ?=
STYLE_ARG = $(if $(STYLE),--line-style $(STYLE),)

reproduce:
	@echo "🔬 Reproducing paper results..."
	$(PY) experiments/scripts/reproduce_paper_results.py --algorithms qhr_v2x,astar,dijkstra $(SEED_ARG)
	@echo "✅ Paper results reproduced!"

# Statistical analysis
analyze:
	@echo "📊 Running statistical analysis..."
	$(PY) experiments/analysis/analyze_results.py
	@echo "✅ Analysis completed!"

# Generate the paper's Figures 3-8 from the benchmark output.
# Depends on `reproduce` so the figures can never be drawn from stale CSVs.
figures: reproduce
	@echo "📈 Generating paper Figures 3-8..."
	$(PY) experiments/analysis/paper_figures.py $(STYLE_ARG)
	@echo "✅ Figures generated in experiments/results/paper_figures/"

# The same six Section IV figures, but at the parameters Table 1 states rather
# than the ones the tests/ harness builds: obstacle placement uniformly random at
# exactly 20% / 40% at every grid size, 20 independent seeds, three timing
# repeats, and one shared message counter across all three algorithms.
#
# These do NOT match the published figures, and that is the finding, not a bug --
# the published shape depends on the realised density being 1.6-12% rather than
# the stated 20%/40%. See REPRODUCE.md section 8 and VERIFICATION.md section 2.5.
#
# Endpoints come from the largest connected free component rather than corner to
# corner, because at 40% density opposite corners are almost never connected.
figures-nominal:
	@echo "📈 Generating figures at the Table 1 parameters (20 seeds)..."
	$(PY) experiments/scripts/generate_comparison_charts.py --seeds $(SEEDS) --repeats $(REPEATS)
	@echo "✅ Written to experiments/results/figures/"

# Seeds and timing repeats for figures-nominal.
SEEDS   ?= 20
REPEATS ?= 3

# Full catalogue: the six paper figures plus every other view of the same CSVs
# (log scales, bar charts, overview panels, relative overhead, CVD-safe palette).
figures-all: figures
	@echo "📈 Generating the full figure catalogue..."
	$(PY) experiments/analysis/all_figures.py $(STYLE_ARG)
	@echo "✅ Catalogue generated in experiments/results/all_figures/ (see MANIFEST.md)"

# Complete research pipeline
all: install test figures analyze
	@echo "🎉 Complete research pipeline finished!"
	@echo "📁 Results available in experiments/results/"
	@echo "📊 Paper figures in experiments/results/paper_figures/"
	@echo "📊 Analysis available in experiments/analysis/results/"

# Code quality
lint:
	@echo "🔍 Running code linting..."
	$(PY) -m flake8 src/ tests/ experiments/
	@echo "✅ Linting completed!"

format:
	@echo "🎨 Formatting code..."
	$(PY) -m black src/ tests/ experiments/
	@echo "✅ Code formatted!"

# Cleanup
# Remove generated output only.
#
# Deliberately does NOT `rm -rf experiments/results/`: several files in there are
# tracked (the paper figures, the comparison charts and CSVs), and a blanket
# delete removes them from the working tree, leaving a clone looking broken until
# someone runs `git checkout`. `git clean -Xdf` removes exactly the ignored
# files -- which is precisely the generated set, since .gitignore already lists
# benchmarks/results/, all_figures/, diagnostics/, paper_reproduction/ and
# analysis/results/. REPRODUCE.md section 7 tabulates what is tracked and why.
# Outside a git checkout it falls back to removing those paths directly.
clean:
	@echo "🧹 Cleaning generated files..."
	@if git rev-parse --git-dir >/dev/null 2>&1; then \
		git clean -Xdf -- benchmarks experiments | sed 's/^/  /'; \
	else \
		rm -rf benchmarks/results/ experiments/results/all_figures/ \
		       experiments/results/diagnostics/ experiments/results/paper_reproduction/ \
		       experiments/analysis/results/; \
	fi
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleanup completed (tracked files untouched)"

# Development commands
dev-setup: install
	@echo "🔧 Setting up development environment..."
	$(PY) -m pre_commit install || echo "pre-commit not available"
	@echo "✅ Development setup complete!"

# Quick validation for reviewers
validate:
	@echo "✅ Quick validation for reviewers..."
	@echo "1. Testing QHR-V2X implementation..."
	$(PY) main.py compare qhr_v2x qhr_v2x_classical
	@echo "2. Running small experiment..."
	$(PY) experiments/scripts/reproduce_paper_results.py --algorithms qhr_v2x,dijkstra
	@echo "3. Generating analysis..."
	$(PY) experiments/analysis/analyze_results.py --input-dir experiments/results/paper_reproduction
	@echo "✅ Validation completed!"

# Documentation
docs:
	@echo "📚 Documentation available:"
	@echo "- README.md: Project overview and quick start"
	@echo "- REPRODUCE.md: How to reproduce the paper's figures"
	@echo "- VERIFICATION.md: What reproduces, what does not, and why"
	@echo "- CITATION.cff: Citation metadata"

# Show repository status
status:
	@echo "📊 Repository Status"
	@echo "==================="
	@echo "Python version: $$($(PY) --version)"
	@echo "Dependencies: $$(poetry show --tree 2>/dev/null | wc -l) packages (requires poetry)"
	@echo "Algorithms: $$(ls src/*.py | wc -l) implementations"
	@echo "Experiments: $$(ls experiments/scripts/*.py 2>/dev/null | wc -l) scripts"
	@echo "Results: $$(find experiments/results/ -name "*.csv" 2>/dev/null | wc -l) CSV files"
	@echo "Figures: $$(find experiments/results/ -name "*.png" 2>/dev/null | wc -l) plots"
