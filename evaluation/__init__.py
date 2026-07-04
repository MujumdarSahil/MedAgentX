"""
MedAgentX Evaluation Framework

This package contains all evaluation tooling for Phase 2:
- governance_test_runner: Tests CRF governance enforcement against adversarial scenarios
- determinism_verifier: Verifies SHA-256 hash consistency for non-LLM agents
- baseline_comparison: Compares MedAgentX vs GPT-4 baseline on governance metrics
- red_team_runner: Executes adversarial attack scenarios and classifies results
- statistical_analysis: Chi-square tests, confidence intervals, summary tables
- results_reporter: Generates paper-ready tables from raw evaluation results
"""

__version__ = "2.0.0"
__author__ = "Sahil Mujumdar"
