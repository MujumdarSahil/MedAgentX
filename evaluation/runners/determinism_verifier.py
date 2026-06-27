#!/usr/bin/env python3
"""
MedAgentX Determinism Verifier
================================
Verifies that MedAgentX agents produce deterministic (or highly consistent)
outputs for identical inputs across repeated executions.

Two verification modes:
  - Non-LLM agents: SHA-256 hash comparison — 100% match = DETERMINISTIC
  - LLM agents: cosine similarity of sentence embeddings — ≥85% = HIGH_CONSISTENCY

Usage:
    python -m evaluation.runners.determinism_verifier \\
        --workflow crf_transition \\
        --input '{"current_state": "AI_SUGGESTED", "event": "DOCTOR_REVIEW_COMPLETE"}' \\
        --runs 20 \\
        --agent-type non-llm

    python -m evaluation.runners.determinism_verifier \\
        --workflow symptom_analysis \\
        --input '{"symptoms": ["fever", "cough"], "patient_age": 45, "sex": "M"}' \\
        --runs 20 \\
        --agent-type llm

Exit codes:
    0  — DETERMINISTIC or HIGH_CONSISTENCY
    1  — LOW_CONSISTENCY (may indicate governance-relevant variance)
    2  — Execution error
"""

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False


# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

HASH_MATCH_THRESHOLD = 0.99   # ≥99% hash match → DETERMINISTIC
COSINE_HIGH_THRESHOLD = 0.85  # ≥85% mean cosine → HIGH_CONSISTENCY
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


# ──────────────────────────────────────────────────────────────────────────────
# API call
# ──────────────────────────────────────────────────────────────────────────────

def call_workflow_api(
    api_url: str,
    workflow: str,
    payload: dict[str, Any],
    timeout: int = 60,
) -> dict[str, Any]:
    """Call the MedAgentX workflow API and return the response."""
    endpoint = f"{api_url.rstrip('/')}/api/v1/workflows/{workflow}/run"
    start = time.monotonic()

    try:
        if HAS_HTTPX:
            with httpx.Client(timeout=timeout) as client:
                resp = client.post(endpoint, json=payload)
                resp.raise_for_status()
                data = resp.json()
        else:
            import urllib.request as req
            body = json.dumps(payload).encode()
            request = req.Request(
                endpoint,
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with req.urlopen(request, timeout=timeout) as r:
                data = json.loads(r.read())

        latency_ms = int((time.monotonic() - start) * 1000)
        return {"success": True, "data": data, "latency_ms": latency_ms}

    except Exception as exc:
        latency_ms = int((time.monotonic() - start) * 1000)
        return {"success": False, "error": str(exc), "latency_ms": latency_ms}


# ──────────────────────────────────────────────────────────────────────────────
# Non-LLM verification: SHA-256 hash comparison
# ──────────────────────────────────────────────────────────────────────────────

def compute_sha256(data: Any) -> str:
    """Compute SHA-256 hash of JSON-serialized data (sorted keys for determinism)."""
    serialized = json.dumps(data, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(serialized.encode()).hexdigest()


def verify_non_llm(
    api_url: str,
    workflow: str,
    payload: dict[str, Any],
    runs: int,
    verbose: bool = False,
) -> dict[str, Any]:
    """
    Run workflow N times and check SHA-256 hash consistency.

    Returns a result dict with hash_match_rate and classification.
    """
    print(f"\nRunning {runs} executions of workflow '{workflow}' (non-LLM mode)...")
    hashes: list[str] = []
    latencies: list[int] = []

    for i in range(1, runs + 1):
        result = call_workflow_api(api_url, workflow, payload)
        if not result["success"]:
            print(f"  Run {i:>3}/{runs}: ERROR — {result['error']}", file=sys.stderr)
            continue

        h = compute_sha256(result["data"])
        hashes.append(h)
        latencies.append(result["latency_ms"])

        if verbose:
            print(f"  Run {i:>3}/{runs}: hash={h[:16]}... ({result['latency_ms']}ms)")
        else:
            print(f"  Run {i:>3}/{runs}: ✓ ({result['latency_ms']}ms)", end="\r")

    print()  # newline after \r progress

    if not hashes:
        return {
            "classification": "ERROR",
            "hash_match_rate": 0.0,
            "error": "All runs failed",
        }

    # Count how many hashes match the most common hash
    unique_hashes = set(hashes)
    most_common = max(unique_hashes, key=lambda h: hashes.count(h))
    match_count = hashes.count(most_common)
    hash_match_rate = match_count / len(hashes)

    classification = "DETERMINISTIC" if hash_match_rate >= HASH_MATCH_THRESHOLD else "NON_DETERMINISTIC"
    mean_latency = sum(latencies) / len(latencies) if latencies else 0

    return {
        "workflow": workflow,
        "agent_type": "non-llm",
        "runs_attempted": runs,
        "runs_successful": len(hashes),
        "unique_hashes": len(unique_hashes),
        "most_common_hash": most_common,
        "hash_match_rate": hash_match_rate,
        "hash_match_pct": f"{hash_match_rate * 100:.1f}%",
        "classification": classification,
        "mean_latency_ms": round(mean_latency, 1),
        "all_hashes": hashes if verbose else None,
    }


# ──────────────────────────────────────────────────────────────────────────────
# LLM verification: cosine similarity of sentence embeddings
# ──────────────────────────────────────────────────────────────────────────────

def extract_text_from_response(response_data: Any) -> str:
    """Extract text content from a workflow API response."""
    if isinstance(response_data, str):
        return response_data
    if isinstance(response_data, dict):
        for field in ("response", "output", "content", "message", "result", "text"):
            if field in response_data and isinstance(response_data[field], str):
                return response_data[field]
    return json.dumps(response_data)


def compute_pairwise_cosine(embeddings: "np.ndarray") -> float:
    """
    Compute mean pairwise cosine similarity across all pairs of embeddings.

    Returns a float in [0, 1] representing mean similarity.
    """
    n = len(embeddings)
    if n < 2:
        return 1.0

    # Normalize embeddings
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    normalized = embeddings / (norms + 1e-8)

    # Compute all pairwise dot products
    dot_products = normalized @ normalized.T

    # Extract upper triangle (excluding diagonal)
    indices = np.triu_indices(n, k=1)
    pairwise = dot_products[indices]

    return float(np.mean(pairwise))


def verify_llm(
    api_url: str,
    workflow: str,
    payload: dict[str, Any],
    runs: int,
    verbose: bool = False,
) -> dict[str, Any]:
    """
    Run workflow N times and measure cosine similarity of sentence embeddings.

    Returns a result dict with mean_similarity, std_similarity, and classification.
    """
    if not HAS_SENTENCE_TRANSFORMERS:
        print("WARNING: sentence-transformers not installed. Run: pip install sentence-transformers")
        print("Falling back to hash comparison...")
        return verify_non_llm(api_url, workflow, payload, runs, verbose)

    print(f"\nLoading embedding model: {EMBEDDING_MODEL}...")
    model = SentenceTransformer(EMBEDDING_MODEL)

    print(f"Running {runs} executions of workflow '{workflow}' (LLM mode)...")
    texts: list[str] = []
    latencies: list[int] = []

    for i in range(1, runs + 1):
        result = call_workflow_api(api_url, workflow, payload)
        if not result["success"]:
            print(f"  Run {i:>3}/{runs}: ERROR — {result['error']}", file=sys.stderr)
            continue

        text = extract_text_from_response(result["data"])
        texts.append(text)
        latencies.append(result["latency_ms"])

        if verbose:
            print(f"  Run {i:>3}/{runs}: '{text[:60]}...' ({result['latency_ms']}ms)")
        else:
            print(f"  Run {i:>3}/{runs}: ✓ ({result['latency_ms']}ms)", end="\r")

    print()

    if len(texts) < 2:
        return {
            "classification": "ERROR",
            "mean_similarity": 0.0,
            "error": "Fewer than 2 successful runs",
        }

    # Compute embeddings and pairwise cosine similarity
    print("Computing embeddings and cosine similarities...")
    embeddings = model.encode(texts, show_progress_bar=False)
    mean_similarity = compute_pairwise_cosine(embeddings)
    std_similarity = float(np.std([
        float(np.dot(embeddings[i], embeddings[j]) / (
            np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[j]) + 1e-8
        ))
        for i in range(len(embeddings))
        for j in range(i + 1, len(embeddings))
    ]))

    if mean_similarity >= COSINE_HIGH_THRESHOLD:
        classification = "HIGH_CONSISTENCY"
    else:
        classification = "LOW_CONSISTENCY"

    mean_latency = sum(latencies) / len(latencies) if latencies else 0

    return {
        "workflow": workflow,
        "agent_type": "llm",
        "embedding_model": EMBEDDING_MODEL,
        "runs_attempted": runs,
        "runs_successful": len(texts),
        "mean_similarity": round(mean_similarity, 4),
        "std_similarity": round(std_similarity, 4),
        "mean_similarity_display": f"{mean_similarity:.4f} ± {std_similarity:.4f}",
        "classification": classification,
        "mean_latency_ms": round(mean_latency, 1),
    }


# ──────────────────────────────────────────────────────────────────────────────
# Output formatting
# ──────────────────────────────────────────────────────────────────────────────

def print_verification_report(result: dict[str, Any]) -> None:
    """Print a human-readable verification report."""
    sep = "═" * 60
    print(f"\n{sep}")
    print("DETERMINISM VERIFICATION REPORT")
    print(sep)
    print(f"Workflow:       {result.get('workflow', 'N/A')}")
    print(f"Agent Type:     {result.get('agent_type', 'N/A')}")
    print(f"Runs Attempted: {result.get('runs_attempted', 'N/A')}")
    print(f"Runs Succeeded: {result.get('runs_successful', 'N/A')}")

    if result.get("agent_type") == "non-llm":
        print(f"Unique Hashes:  {result.get('unique_hashes', 'N/A')}")
        print(f"Hash Match:     {result.get('hash_match_pct', 'N/A')}")
    else:
        print(f"Mean Similarity:{result.get('mean_similarity_display', 'N/A')}")
        print(f"Embedding Model:{result.get('embedding_model', 'N/A')}")

    print(f"Mean Latency:   {result.get('mean_latency_ms', 'N/A')} ms")
    print()

    classification = result.get("classification", "UNKNOWN")
    icons = {
        "DETERMINISTIC": "✅ DETERMINISTIC",
        "HIGH_CONSISTENCY": "✅ HIGH_CONSISTENCY",
        "LOW_CONSISTENCY": "⚠️  LOW_CONSISTENCY — Review required",
        "NON_DETERMINISTIC": "❌ NON_DETERMINISTIC — Governance risk",
        "ERROR": "❌ ERROR",
    }
    print(f"Classification: {icons.get(classification, classification)}")
    print(sep)


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="MedAgentX Determinism Verifier",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="Base URL of the MedAgentX API",
    )
    parser.add_argument(
        "--workflow",
        required=True,
        help="Workflow name to verify (e.g., crf_transition, symptom_analysis)",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="JSON-encoded input payload for the workflow",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=20,
        help="Number of repetitions (default: 20)",
    )
    parser.add_argument(
        "--agent-type",
        choices=["non-llm", "llm", "auto"],
        default="auto",
        help="Agent type: non-llm (hash), llm (cosine), auto (default: auto)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default="evaluation/results/",
        help="Directory to save results JSON",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print individual run details",
    )
    args = parser.parse_args()

    # Parse input payload
    try:
        payload = json.loads(args.input)
    except json.JSONDecodeError as exc:
        print(f"ERROR: Invalid JSON input: {exc}", file=sys.stderr)
        sys.exit(2)

    # Auto-detect agent type: assume non-llm unless workflow contains known LLM indicators
    agent_type = args.agent_type
    if agent_type == "auto":
        llm_workflows = {"symptom_analysis", "guideline_summary", "clinical_context", "recommendation"}
        agent_type = "llm" if args.workflow in llm_workflows else "non-llm"
        print(f"Auto-detected agent type: {agent_type}")

    # Run verification
    if agent_type == "non-llm":
        result = verify_non_llm(args.api_url, args.workflow, payload, args.runs, args.verbose)
    else:
        result = verify_llm(args.api_url, args.workflow, payload, args.runs, args.verbose)

    # Add metadata
    result["timestamp"] = datetime.now(timezone.utc).isoformat()
    result["input_payload"] = payload

    # Save results
    args.output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_file = args.output_dir / f"determinism_{args.workflow}_{ts}.json"
    with output_file.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"\nResults saved to: {output_file}")

    # Print report
    print_verification_report(result)

    # Exit code based on classification
    classification = result.get("classification", "ERROR")
    if classification in ("DETERMINISTIC", "HIGH_CONSISTENCY"):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
