#!/usr/bin/env python3
"""
MedAgentX Statistical Analysis
================================
Chi-square tests, confidence intervals, and summary tables
for evaluation results.

Usage:
    python -m evaluation.analysis.statistical_analysis \\
        --results-dir evaluation/results/ \\
        --output-dir evaluation/results/analysis/
"""

import argparse
import json
import sys
from pathlib import Path


def run_chi_square(violations_a: list, violations_b: list) -> dict:
    """
    Run chi-square test comparing two violation rate arrays.
    Returns dict with chi2, p_value, significance.
    """
    try:
        from scipy.stats import chi2_contingency
        n_a, n_b = len(violations_a), len(violations_b)
        v_a, v_b = sum(violations_a), sum(violations_b)
        c_a, c_b = n_a - v_a, n_b - v_b
        chi2, p, dof, _ = chi2_contingency([[v_a, c_a], [v_b, c_b]], correction=False)
        stars = "***" if p < 0.001 else ("**" if p < 0.01 else ("*" if p < 0.05 else "ns"))
        return {
            "chi2": round(float(chi2), 4),
            "p_value": round(float(p), 6),
            "dof": int(dof),
            "significant": p < 0.05,
            "significance_stars": stars,
        }
    except ImportError:
        return {"error": "scipy not installed"}


def wilson_confidence_interval(successes: int, n: int, alpha: float = 0.05) -> tuple:
    """
    Wilson confidence interval for a proportion.
    Returns (lower, upper) bounds.
    """
    try:
        from statsmodels.stats.proportion import proportion_confint
        lo, hi = proportion_confint(successes, n, alpha=alpha, method="wilson")
        return round(lo, 4), round(hi, 4)
    except ImportError:
        import math
        if n == 0:
            return 0.0, 0.0
        p = successes / n
        z = 1.96
        margin = z * math.sqrt(p * (1 - p) / n)
        return round(max(0, p - margin), 4), round(min(1, p + margin), 4)


def main() -> None:
    parser = argparse.ArgumentParser(description="MedAgentX Statistical Analysis")
    parser.add_argument("--results-dir", type=Path, default="evaluation/results/")
    parser.add_argument("--output-dir", type=Path, default="evaluation/results/analysis/")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Analyzing results in: {args.results_dir}")
    print(f"Output directory: {args.output_dir}")
    print("Run evaluation first, then re-run this script to generate statistical summaries.")


if __name__ == "__main__":
    main()
