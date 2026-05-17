"""Triage assistant — the one workflow this deployment runs.

Flow:
    case_in  → retrieve similar past cases
             → classify ESI tier (rule-based for now)
             → generate grounded answer with citations
             → apply fallback_logic if confidence low
             → return customer-shaped response

This file is the "what the AI does for the charge nurse" surface. Everything
else in the repo is integration + observability + ops around this.
"""
from __future__ import annotations
import time
from typing import Any

from generation.generate import generate_answer
from retrieval.query_pipeline import QueryPipeline
from .fallback_logic import should_escalate, to_rules_fallback


def _esi_from_case(case: dict) -> tuple[int, float, list[str]]:
    """Rule-based ESI scoring — deliberately simple + auditable.

    Returns (esi_tier, confidence, red_flags).
    In real customer engagement, swap with the customer-validated ESI rules
    or a small LLM classifier behind a fallback flag.
    """
    cc = (case.get("chief_complaint", "") or case.get("cc", "")).lower()
    hpi = (case.get("hpi", "") or "").lower()
    text = f"{cc} {hpi}"
    vitals = case.get("vitals") or {}

    red_flags: list[str] = []
    tier = 4  # default less-urgent

    # ESI 1: resuscitation triggers
    for kw in ("cardiac arrest", "stroke", "stemi", "anaphylax", "respiratory failure"):
        if kw in text:
            red_flags.append(f"resuscitation_keyword:{kw}")
            tier = 1
            break

    # ESI 2: high-risk triggers
    if tier > 2:
        for kw in ("chest pain", "sepsis", "diaphoresis", "altered mental"):
            if kw in text:
                red_flags.append(f"high_risk_keyword:{kw}")
                tier = min(tier, 2)

    # Vital instability bumps tier toward 2
    if vitals:
        try:
            if int(vitals.get("bp_sys", 120)) < 90:
                red_flags.append("hypotension")
                tier = min(tier, 2)
            if int(vitals.get("spo2", 100)) < 92:
                red_flags.append("hypoxia")
                tier = min(tier, 2)
            if int(vitals.get("hr", 70)) > 120:
                red_flags.append("tachycardia")
                tier = min(tier, 3)
        except (ValueError, TypeError):
            pass

    # Pediatric safety floor
    try:
        age = int(case.get("Age", case.get("age", 100)))
        if age <= 1:
            red_flags.append("pediatric_under_1y")
            tier = min(tier, 2)
    except (ValueError, TypeError):
        pass

    confidence = 0.85 if red_flags else 0.65
    return tier, confidence, red_flags


def triage(case: dict, *, case_id: str = "anon") -> dict:
    """Run the full triage assistant flow on one case.

    Returns customer-shaped dict (NOT a Pydantic model — the FDE app
    serializes this directly).
    """
    t0 = time.time()

    pipeline = QueryPipeline()
    query = f"{case.get('chief_complaint', '')} {case.get('hpi', '')[:200]}".strip()
    hits = pipeline.retrieve(query, k=5, method="bm25")

    esi, confidence, red_flags = _esi_from_case(case)
    gen = generate_answer(query, hits)

    fallback = should_escalate(esi, confidence, red_flags)
    if fallback:
        return to_rules_fallback(case_id, case, esi, red_flags, gen["answer"])

    return {
        "case_id": case_id,
        "esi_tier": esi,
        "tier_bucket": "NOW" if esi <= 2 else "SOON" if esi == 3 else "WAIT",
        "confidence": confidence,
        "red_flags": red_flags,
        "rationale": gen["answer"],
        "citations": gen["citations"],
        "similar_cases": [
            {"source_id": h["case_id"], "snippet": (h.get("snippet") or "")[:200]}
            for h in hits[:3]
        ],
        "human_review_required": esi == 1 or confidence < 0.7,
        "mode": "ai_assist",
        "latency_ms": int((time.time() - t0) * 1000),
        "warnings": gen.get("warnings", []),
    }
