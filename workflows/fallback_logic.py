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
) -> dict:
    """Return a fallback-shaped response when escalation triggers fire."""
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
        "warnings": ["assistant in fallback mode — clinician must verify"],
    }
