#!/usr/bin/env python3
"""
MedAgentX Results Reporter
===========================
Generates paper-ready tables from raw evaluation result files.

Usage:
    python -m evaluation.analysis.results_reporter \\
        --type governance \\
        --input evaluation/results/governance_results_*.jsonl \\
        --output evaluation/results/analysis/table2.csv

    python -m evaluation.analysis.results_reporter \\
        --type baseline \\
        --input evaluation/results/baseline_comparison_*_summary.json \\
        --output evaluation/results/analysis/table3.csv
"""

import argparse
import csv
import glob
import json
import sys
from pathlib import Path


SUPPORTED_TYPES = ["governance", "baseline", "determinism", "redteam"]


def load_jsonl(path: str) -> list:
    """Load all records from a JSONL file."""
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def generate_governance_table(input_files: list, output_path: Path) -> None:
    """Generate Table 2: Governance test results by category."""
    all_records = []
    for f in input_files:
        all_records.extend(load_jsonl(f))

    categories: dict = {}
    for rec in all_records:
        cat = rec.get("category", "unknown")
        if cat not in categories:
            categories[cat] = {"total": 0, "violations": 0}
        categories[cat]["total"] += 1
        if rec.get("violation_detected"):
            categories[cat]["violations"] += 1

    rows = []
    for cat, counts in sorted(categories.items()):
        rate = counts["violations"] / counts["total"] if counts["total"] > 0 else 0
        rows.append({
            "category": cat,
            "total_scenarios": counts["total"],
            "violations": counts["violations"],
            "violation_rate": f"{rate:.1%}",
        })

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["category", "total_scenarios", "violations", "violation_rate"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Governance table written to: {output_path}")
    for row in rows:
        print(f"  {row['category']:<45} {row['violations']}/{row['total_scenarios']} ({row['violation_rate']})")


def main() -> None:
    parser = argparse.ArgumentParser(description="MedAgentX Results Reporter")
    parser.add_argument("--type", choices=SUPPORTED_TYPES, required=True)
    parser.add_argument("--input", nargs="+", required=True, help="Input files (supports glob patterns)")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    # Expand globs
    input_files = []
    for pattern in args.input:
        expanded = glob.glob(pattern)
        if expanded:
            input_files.extend(expanded)
        else:
            input_files.append(pattern)

    if not input_files:
        print(f"ERROR: No input files found matching: {args.input}", file=sys.stderr)
        sys.exit(1)

    args.output.parent.mkdir(parents=True, exist_ok=True)

    if args.type == "governance":
        generate_governance_table(input_files, args.output)
    else:
        print(f"Reporter for type '{args.type}' — run the evaluation first to generate input files.")
        print(f"Input files found: {input_files}")


if __name__ == "__main__":
    main()
