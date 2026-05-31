"""Dataset replay pipeline — offline regression suite.

Titan JD signal: "dataset replay pipeline, offline regression suites"

Loads eval_dataset.json and replays each case through the live triage
pipeline. Compares output against expected labels. Acts as a regression
gate in CI: exit code 1 if pass-rate drops below threshold.

Usage:
    python -m evaluation.replay_pipeline              # full suite
    python -m evaluation.replay_pipeline --fast       # ESI accuracy only
    python -m evaluation.replay_pipeline --threshold 0.9
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

from workflows.triage_assistant import triage

EVAL_DATASET = Path(__file__).parent / "eval_dataset.json"
DEFAULT_PASS_THRESHOLD = 0.85


def load_dataset() -> list[dict]:
    with EVAL_DATASET.open() as f:
        return json.load(f)


def run_case(case: dict) -> dict:
    """Replay one eval case and return result + match verdict."""
    t0 = time.time()
    result = triage(case, case_id=case.get("case_id", "eval-anon"))
    latency = int((time.time() - t0) * 1000)

    expected_tier = case.get("expected_esi_tier")
    expected_review = case.get("expected_human_review")

    tier_match = (expected_tier is None) or (result["esi_tier"] == expected_tier)
    review_match = (expected_review is None) or (result["human_review_required"] == expected_review)

    return {
        "case_id": case.get("case_id", "?"),
        "expected_tier": expected_tier,
        "got_tier": result["esi_tier"],
        "tier_match": tier_match,
        "expected_review": expected_review,
        "got_review": result["human_review_required"],
        "review_match": review_match,
        "passed": tier_match and review_match,
        "confidence": result["confidence"],
        "mode": result["mode"],
        "latency_ms": latency,
    }


def run_replay(threshold: float = DEFAULT_PASS_THRESHOLD, fast: bool = False) -> int:
    """Run full replay suite. Returns exit code (0=pass, 1=fail)."""
    cases = load_dataset()
    if fast:
        cases = [c for c in cases if c.get("expected_esi_tier") is not None]

    results = []
    for case in cases:
        r = run_case(case)
        results.append(r)
        status = "✅" if r["passed"] else "❌"
        print(
            f"  {status} {r['case_id']:20s} "
            f"tier={r['got_tier']} (expected={r['expected_tier']}) "
            f"conf={r['confidence']:.2f} latency={r['latency_ms']}ms"
        )

    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    pass_rate = passed / total if total else 0.0
    avg_latency = sum(r["latency_ms"] for r in results) / total if total else 0

    print(f"\n{'='*60}")
    print(f"Pass rate: {passed}/{total} = {pass_rate:.0%}  (threshold: {threshold:.0%})")
    print(f"Avg latency: {avg_latency:.0f}ms")

    if pass_rate < threshold:
        print(f"❌ REGRESSION: pass rate {pass_rate:.0%} < threshold {threshold:.0%}")
        return 1

    print(f"✅ PASSED: {pass_rate:.0%} >= {threshold:.0%}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--threshold", type=float, default=DEFAULT_PASS_THRESHOLD)
    parser.add_argument("--fast", action="store_true")
    args = parser.parse_args()
    sys.exit(run_replay(threshold=args.threshold, fast=args.fast))
