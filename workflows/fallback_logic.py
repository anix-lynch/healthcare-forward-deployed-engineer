"""Human handoff + degraded-mode logic.

When the AI says "I'm not confident" or upstream is degraded, the workflow
SHOULD NOT push a suggestion. It should hand off cleanly.

Rules:
    - confidence < 0.5    → human review required, no AI suggestion shown
    - upstream degraded   → rules_fallback mode (deterministic ESI scoring only)
    - safety triggers     → escalate immediately (page attending)
"""
from __future__ import annotations


def should_escalate(esi: int, confidence: float, red_flags: list[str]) -> bool:
    """Return True iff the AI assistant should refuse to suggest + escalate."""
    # ESI 1 always escalates regardless of confidence
    if esi == 1:
        return True
    # Pediatric safety: under-1y always escalates
    if any("pediatric_under_1y" in f for f in red_flags):
        return True
    # Low confidence → don't show AI suggestion, route to human
    if confidence < 0.5:
        return True
    return False


def to_rules_fallback(
    case_id: str,
    case: dict,
    esi: int,
    red_flags: list[str],
    rationale: str,
    *,
    latency_ms: int = 0,
) -> dict:
    """Return a fallback-shaped response when escalation triggers fire.

    Shape parity with workflows.triage_assistant.triage() — same key set,
    so downstream consumers don't have to branch on `mode` to read fields.
    `latency_ms` defaults to 0 if caller doesn't measure, but should be
    threaded through from the calling workflow for honest p95 reporting.
    """
    return {
        "case_id": case_id,
        "esi_tier": esi,
        "tier_bucket": "NOW" if esi <= 2 else "SOON" if esi == 3 else "WAIT",
        "confidence": 1.0,  # rules-based = deterministic
        "red_flags": red_flags,
        "rationale": (
            f"AI assistant unavailable or low-confidence — falling back to rules-based "
            f"ESI scoring. Final tier suggestion: ESI {esi}. {rationale}"
        ),
        "citations": [],
        "similar_cases": [],
        "human_review_required": True,
        "mode": "rules_fallback",
        "latency_ms": latency_ms,
        "warnings": ["assistant in fallback mode — clinician must verify"],
    }
