# QHR-V2X Research Repository Makefile
# =====================================
# 
# This Makefile provides convenient commands for reproducing
# research results and managing the academic codebase.

.PHONY: help install test clean reproduce analyze figures all

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
	@echo "  make figures     - Generate publication figures"
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
	poetry run python main.py test
	poetry run python main.py compare qhr_v2x qhr_v2x_classical
	@echo "✅ Tests completed!"

# Reproduce paper results
reproduce:
	@echo "🔬 Reproducing paper results..."
	poetry run python experiments/scripts/reproduce_paper_results.py
	@echo "✅ Paper results reproduced!"

# Statistical analysis
analyze:
	@echo "📊 Running statistical analysis..."
	poetry run python experiments/analysis/analyze_results.py
	@echo "✅ Analysis completed!"

# Generate figures
figures: analyze
	@echo "📈 Figures generated in experiments/analysis/results/"
	@ls -la experiments/analysis/results/*.png 2>/dev/null || echo "No figures found. Run 'make analyze' first."

# Complete research pipeline
all: install test reproduce analyze
	@echo "🎉 Complete research pipeline finished!"
	@echo "📁 Results available in experiments/results/"
	@echo "📊 Analysis available in experiments/analysis/results/"

# Code quality
lint:
	@echo "🔍 Running code linting..."
	poetry run flake8 src/ tests/ experiments/
	@echo "✅ Linting completed!"

format:
	@echo "🎨 Formatting code..."
	poetry run black src/ tests/ experiments/
	@echo "✅ Code formatted!"

# Cleanup
clean:
	@echo "🧹 Cleaning generated files..."
	rm -rf experiments/results/
	rm -rf experiments/analysis/results/
	rm -rf __pycache__/
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleanup completed!"

# Development commands
dev-setup: install
	@echo "🔧 Setting up development environment..."
	poetry run pre-commit install || echo "pre-commit not available"
	@echo "✅ Development setup complete!"

# Quick validation for reviewers
validate:
	@echo "✅ Quick validation for reviewers..."
	@echo "1. Testing QHR-V2X implementation..."
	poetry run python main.py compare qhr_v2x qhr_v2x_classical
	@echo "2. Running small experiment..."
	poetry run python experiments/scripts/reproduce_paper_results.py --algorithms qhr_v2x,dijkstra
	@echo "3. Generating analysis..."
	poetry run python experiments/analysis/analyze_results.py --input-dir experiments/results/paper_reproduction
	@echo "✅ Validation completed!"

# Documentation
docs:
	@echo "📚 Documentation available:"
	@echo "- README.md: Project overview and quick start"
	@echo "- EXPERIMENTS.md: Detailed experimental guide"
	@echo "- PAPER_INTEGRATION.md: Paper integration guide"
	@echo "- CITATION.md: Citation information"

# Show repository status
status:
	@echo "📊 Repository Status"
	@echo "==================="
	@echo "Python version: $$(poetry run python --version)"
	@echo "Dependencies: $$(poetry show --tree | wc -l) packages"
	@echo "Algorithms: $$(ls src/*.py | wc -l) implementations"
	@echo "Experiments: $$(ls experiments/scripts/*.py 2>/dev/null | wc -l) scripts"
	@echo "Results: $$(find experiments/results/ -name "*.csv" 2>/dev/null | wc -l) CSV files"
	@echo "Figures: $$(find experiments/analysis/results/ -name "*.png" 2>/dev/null | wc -l) plots"
