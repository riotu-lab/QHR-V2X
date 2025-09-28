#!/usr/bin/env python3
"""
Statistical Analysis and Visualization Script
=============================================

This script performs statistical analysis and generates visualizations
for the QHR-V2X experimental results, suitable for research papers.

Usage:
    python experiments/analysis/analyze_results.py [--input-dir DIR] [--output-dir DIR]

Features:
    - Statistical significance testing (t-tests, ANOVA)
    - Performance comparison plots
    - Scalability analysis
    - Export publication-ready figures
"""

import os
import sys
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from scipy import stats
import warnings

# Set style for publication-ready plots
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def load_results(input_dir):
    """Load experimental results from CSV files."""
    input_path = Path(input_dir)
    
    results = {}
    
    # Load dense results
    dense_file = input_path / "dense_results.csv"
    if dense_file.exists():
        results['dense'] = pd.read_csv(dense_file)
        print(f"✅ Loaded dense results: {len(results['dense'])} records")
    
    # Load sparse results
    sparse_file = input_path / "sparse_results.csv"
    if sparse_file.exists():
        results['sparse'] = pd.read_csv(sparse_file)
        print(f"✅ Loaded sparse results: {len(results['sparse'])} records")
    
    return results

def statistical_analysis(df, metric='msgs'):
    """Perform statistical analysis on the results."""
    algorithms = df['algorithm'].unique()
    
    print(f"\n📊 Statistical Analysis - {metric.upper()}")
    print("-" * 40)
    
    # Descriptive statistics
    print("Descriptive Statistics:")
    stats_summary = df.groupby('algorithm')[metric].agg(['mean', 'std', 'min', 'max'])
    print(stats_summary.round(3))
    
    # ANOVA test
    groups = [df[df['algorithm'] == algo][metric].values for algo in algorithms]
    f_stat, p_value = stats.f_oneway(*groups)
    
    print(f"\nANOVA Test:")
    print(f"F-statistic: {f_stat:.4f}")
    print(f"P-value: {p_value:.4f}")
    print(f"Significant: {'Yes' if p_value < 0.05 else 'No'} (α = 0.05)")
    
    # Pairwise t-tests
    print(f"\nPairwise T-tests (Bonferroni corrected):")
    from itertools import combinations
    
    n_comparisons = len(list(combinations(algorithms, 2)))
    alpha_corrected = 0.05 / n_comparisons
    
    for algo1, algo2 in combinations(algorithms, 2):
        group1 = df[df['algorithm'] == algo1][metric].values
        group2 = df[df['algorithm'] == algo2][metric].values
        
        t_stat, p_val = stats.ttest_ind(group1, group2)
        significant = p_val < alpha_corrected
        
        print(f"{algo1} vs {algo2}: t={t_stat:.4f}, p={p_val:.4f}, "
              f"significant={'Yes' if significant else 'No'}")
    
    return stats_summary

def create_performance_plots(results, output_dir):
    """Create publication-ready performance comparison plots."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Set up the plotting style
    plt.rcParams.update({
        'font.size': 12,
        'axes.titlesize': 14,
        'axes.labelsize': 12,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'legend.fontsize': 10,
        'figure.titlesize': 16
    })
    
    for mode, df in results.items():
        # Create subplots for different metrics
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle(f'QHR-V2X Performance Analysis - {mode.title()} Environment', 
                     fontsize=16, fontweight='bold')
        
        metrics = ['msgs', 'path_len', 'time_ms', 'estimated_ms']
        titles = ['Route Discovery Messages (RDM)', 'Path Length (PL)', 
                 'Route Discovery Time (RDT)', 'Estimated Time']
        
        for idx, (metric, title) in enumerate(zip(metrics, titles)):
            ax = axes[idx // 2, idx % 2]
            
            # Create box plot
            sns.boxplot(data=df, x='algorithm', y=metric, ax=ax)
            ax.set_title(title)
            ax.set_xlabel('Algorithm')
            ax.set_ylabel(metric.replace('_', ' ').title())
            
            # Rotate x-axis labels for better readability
            ax.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plot_path = output_path / f"performance_comparison_{mode}.png"
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"📊 Created performance plot: {plot_path}")
        
        # Create scalability plot
        create_scalability_plot(df, output_path, mode)

def create_scalability_plot(df, output_dir, mode):
    """Create scalability analysis plot."""
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle(f'Scalability Analysis - {mode.title()} Environment', 
                 fontsize=16, fontweight='bold')
    
    metrics = ['msgs', 'path_len', 'time_ms']
    titles = ['Route Discovery Messages vs Grid Size', 
             'Path Length vs Grid Size', 
             'Route Discovery Time vs Grid Size']
    
    for idx, (metric, title) in enumerate(zip(metrics, titles)):
        ax = axes[idx]
        
        for algorithm in df['algorithm'].unique():
            algo_data = df[df['algorithm'] == algorithm]
            ax.plot(algo_data['grid_size'], algo_data[metric], 
                   marker='o', linewidth=2, markersize=6, label=algorithm)
        
        ax.set_title(title)
        ax.set_xlabel('Grid Size')
        ax.set_ylabel(metric.replace('_', ' ').title())
        ax.grid(True, alpha=0.3)
        ax.legend()
    
    plt.tight_layout()
    plot_path = output_dir / f"scalability_analysis_{mode}.png"
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"📈 Created scalability plot: {plot_path}")

def create_statistical_summary(results, output_dir):
    """Create statistical summary report."""
    output_path = Path(output_dir)
    
    summary_path = output_path / "statistical_analysis.md"
    
    with open(summary_path, 'w') as f:
        f.write("# Statistical Analysis Report\n\n")
        f.write("## QHR-V2X Algorithm Performance Analysis\n\n")
        
        for mode, df in results.items():
            f.write(f"### {mode.title()} Environment\n\n")
            
            for metric in ['msgs', 'path_len', 'time_ms']:
                f.write(f"#### {metric.upper()} Analysis\n\n")
                
                # Descriptive statistics
                stats_summary = df.groupby('algorithm')[metric].agg(['mean', 'std', 'min', 'max'])
                f.write("**Descriptive Statistics:**\n\n")
                f.write(stats_summary.round(3).to_markdown())
                f.write("\n\n")
                
                # ANOVA
                algorithms = df['algorithm'].unique()
                groups = [df[df['algorithm'] == algo][metric].values for algo in algorithms]
                f_stat, p_value = stats.f_oneway(*groups)
                
                f.write(f"**ANOVA Test:**\n")
                f.write(f"- F-statistic: {f_stat:.4f}\n")
                f.write(f"- P-value: {p_value:.4f}\n")
                f.write(f"- Significant difference: {'Yes' if p_value < 0.05 else 'No'}\n\n")
            
            f.write("\n")
        
        f.write("## Interpretation\n\n")
        f.write("### Key Findings:\n\n")
        f.write("1. **QHR-V2X Performance**: [Analysis of quantum enhancement effects]\n")
        f.write("2. **Scalability**: [Analysis of performance across grid sizes]\n")
        f.write("3. **Statistical Significance**: [Summary of significant differences]\n\n")
        
        f.write("### Research Implications:\n\n")
        f.write("- [Discussion of results in context of V2X routing]\n")
        f.write("- [Implications for quantum-enhanced algorithms]\n")
        f.write("- [Future research directions]\n")
    
    print(f"📋 Created statistical summary: {summary_path}")

def main():
    parser = argparse.ArgumentParser(
        description="Analyze QHR-V2X experimental results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "--input-dir",
        type=str,
        default="experiments/results/paper_reproduction",
        help="Input directory containing CSV results (default: experiments/results/paper_reproduction)"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="experiments/analysis/results",
        help="Output directory for analysis results (default: experiments/analysis/results)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Suppress warnings for cleaner output
    if not args.verbose:
        warnings.filterwarnings('ignore')
    
    print("🔬 QHR-V2X Results Analysis")
    print("=" * 40)
    print(f"📁 Input directory: {args.input_dir}")
    print(f"📁 Output directory: {args.output_dir}")
    print()
    
    # Load results
    results = load_results(args.input_dir)
    
    if not results:
        print("❌ No results found. Please run experiments first:")
        print("   python experiments/scripts/reproduce_paper_results.py")
        return
    
    # Create output directory
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Perform analysis
    print("📊 Performing Statistical Analysis")
    print("-" * 40)
    
    for mode, df in results.items():
        print(f"\n{mode.title()} Environment:")
        for metric in ['msgs', 'path_len', 'time_ms']:
            statistical_analysis(df, metric)
    
    # Create visualizations
    print("\n📊 Creating Visualizations")
    print("-" * 40)
    create_performance_plots(results, output_path)
    
    # Generate statistical summary
    print("\n📋 Generating Statistical Summary")
    print("-" * 40)
    create_statistical_summary(results, output_path)
    
    print("\n🎉 Analysis completed!")
    print(f"📁 Results saved to: {output_path}")
    print("\nGenerated files:")
    print("- Performance comparison plots")
    print("- Scalability analysis plots")
    print("- Statistical analysis report")

if __name__ == "__main__":
    main()
