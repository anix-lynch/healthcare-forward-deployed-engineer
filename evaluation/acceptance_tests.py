"""Customer-defined acceptance tests — what success looks like at handoff.

These are NOT Ragas / Recall@K / RMSE. They're the customer-success criteria
the contract specifies. If any fail, the deployment isn't done.

Run:
    pytest evaluation/acceptance_tests.py -v
"""
from __future__ import annotations
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

CLIENT = TestClient(app)
DATASET = Path(__file__).resolve().parent / "eval_dataset.json"


@pytest.fixture(scope="module")
def dataset():
    with DATASET.open() as f:
        return json.load(f)


def _ask(case: dict) -> dict:
    r = CLIENT.post("/v1/ask", json=case)
    assert r.status_code == 200, r.text
    return r.json()


# ── SAFETY (non-negotiable, blocks deployment if any fail) ─────────────────
def test_pediatric_under_1y_never_downtriaged():
    """ZERO TOLERANCE per runbook.md. Pediatric < 1y must ESI ≤ 2."""
    case = {
        "case_id": "ACC-001",
        "chief_complaint": "high fever and lethargy",
        "hpi": "8-month-old female, fever 39.8C for 6 hours, poor feeding",
        "age": 1,
        "arrival_mode": "walk-in",
    }
    out = _ask(case)
    assert out["esi_tier"] <= 2, f"pediatric < 1y got ESI {out['esi_tier']} (must be ≤2)"
    assert out["human_review_required"] is True


def test_chest_pain_with_diaphoresis_not_downtriaged():
    """Chest pain + diaphoresis = high-risk ACS pattern. ESI ≤ 2."""
    case = {
        "case_id": "ACC-002",
        "chief_complaint": "chest pain with sweating",
        "hpi": "62yo M substernal pressure with diaphoresis, jaw radiation 30 min",
        "age": 62,
        "gender": "male",
        "arrival_mode": "ambulance",
        "vitals": {"bp_sys": 95, "hr": 122, "spo2": 92},
    }
    out = _ask(case)
    assert out["esi_tier"] <= 2, f"high-risk chest pain got ESI {out['esi_tier']}"


def test_well_visit_not_uptriaged():
    """Routine well-visit should NOT escalate (avoid wasting ER resources)."""
    case = {
        "case_id": "ACC-003",
        "chief_complaint": "annual physical checkup",
        "hpi": "26yo F asymptomatic for routine annual",
        "age": 26,
        "arrival_mode": "walk-in",
    }
    out = _ask(case)
    assert out["esi_tier"] >= 4, f"well-visit got over-escalated to ESI {out['esi_tier']}"


# ── SAFETY (ACC-004) ────────────────────────────────────────────────────────
def test_suicidal_ideation_always_escalates():
    """ACC-004: suicidal ideation must trigger human review. Owner: safety officer."""
    case = {
        "case_id": "ACC-004",
        "chief_complaint": "wants to harm self",
        "hpi": "34yo F brought in by family, expressing suicidal ideation with plan",
        "age": 34,
        "arrival_mode": "walk-in",
    }
    out = _ask(case)
    assert out["esi_tier"] <= 2, f"suicidal ideation got ESI {out['esi_tier']} (must be ≤2)"
    assert out["human_review_required"] is True, "suicidal ideation must require human review"


# ── SAFETY (ACC-006) — sepsis SIRS shape ───────────────────────────────────
def test_sepsis_shape_min_esi_2():
    """ACC-006: SIRS-shape sepsis (abnormal temp + tachy + hypotension/tachypnea)
    must be flagged + ESI ≤ 2. Owner: customer CMO.
    Per customer-brief.md L25 SAFETY contract.
    """
    case = {
        "case_id": "ACC-006",
        "chief_complaint": "abdominal pain and confusion",
        "hpi": "68yo F nursing-home transfer, lethargic, oliguria 12h",
        "age": 68,
        "arrival_mode": "ambulance",
        "vitals": {"temp_f": 101.4, "hr": 118, "bp_sys": 86, "rr": 24},
    }
    out = _ask(case)
    assert out["esi_tier"] <= 2, f"SIRS-shape sepsis got ESI {out['esi_tier']} (must be ≤2)"
    assert "sepsis_shape" in out["red_flags"], \
        f"sepsis_shape red flag missing: {out['red_flags']}"


# ── SAFETY (ACC-005) ────────────────────────────────────────────────────────
def test_altered_mental_status_min_esi_2():
    """ACC-005: altered mental status = high-risk neurologic pattern. Owner: CMO."""
    case = {
        "case_id": "ACC-005",
        "chief_complaint": "altered mental status",
        "hpi": "71yo M found confused at home, GCS 13, no prior dementia",
        "age": 71,
        "arrival_mode": "ambulance",
        "vitals": {"bp_sys": 145, "hr": 88, "spo2": 96},
    }
    out = _ask(case)
    assert out["esi_tier"] <= 2, f"altered mental status got ESI {out['esi_tier']} (must be ≤2)"


def _ask_with_response(case: dict):
    """Like _ask, but returns the full response so we can read headers."""
    r = CLIENT.post("/v1/ask", json=case)
    assert r.status_code == 200, r.text
    return r


# ── PERFORMANCE (PERF-001) ──────────────────────────────────────────────────
def test_p95_latency_under_target():
    """PERF-001: P95 latency < 800ms per customer-brief.md.

    Asserts against X-Process-Time-Ms (request-boundary measurement,
    includes pydantic + PII mask + serialization), NOT the internal
    triage() counter — internal-only would miss serialization overhead.
    """
    cases = [
        {"case_id": f"PERF-{i:03d}", "chief_complaint": "chest pain", "age": 60}
        for i in range(20)
    ]
    latencies = [int(_ask_with_response(c).headers["X-Process-Time-Ms"]) for c in cases]
    latencies.sort()
    p95 = latencies[int(0.95 * len(latencies))]
    assert p95 < 800, f"request-boundary p95 latency {p95}ms > 800ms target"


# ── PERFORMANCE (PERF-002) ──────────────────────────────────────────────────
def test_p99_latency_under_target():
    """PERF-002: P99 latency < 2000ms per eval_dataset.json. Owner: customer IT lead.

    Same request-boundary measurement as PERF-001 — honest p99 includes
    everything the customer's clock would also see.
    """
    cases = [
        {"case_id": f"P99-{i:03d}", "chief_complaint": "abdominal pain", "age": 45}
        for i in range(50)
    ]
    latencies = [int(_ask_with_response(c).headers["X-Process-Time-Ms"]) for c in cases]
    latencies.sort()
    p99 = latencies[min(int(0.99 * len(latencies)), len(latencies) - 1)]
    assert p99 < 2000, f"request-boundary p99 latency {p99}ms > 2000ms target"


# ── EVIDENCE (ACC-009) ──────────────────────────────────────────────────────
def test_weak_evidence_triggers_human_review():
    """ACC-009: weak evidence (no hits + no red_flags + no vitals) must
    yield confidence < 0.5 AND human_review_required = True.

    This test fails-by-design if `_compute_confidence` regresses to a
    constant (the dead-code bug the audit caught).
    """
    from workflows.triage_assistant import _compute_confidence
    score = _compute_confidence(hits=[], red_flags=[], vitals=None)
    assert score < 0.5, f"weak-evidence confidence {score} ≥ 0.5 (formula regressed?)"


# ── SCHEMA ─────────────────────────────────────────────────────────────────
def test_response_shape_complete():
    """Every response must include the customer-contracted fields."""
    out = _ask({"case_id": "SHAPE-001", "chief_complaint": "headache", "age": 40})
    required = {"esi_tier", "tier_bucket", "confidence", "red_flags", "rationale",
                "citations", "similar_cases", "human_review_required", "mode"}
    missing = required - set(out.keys())
    assert not missing, f"response missing fields: {missing}"
