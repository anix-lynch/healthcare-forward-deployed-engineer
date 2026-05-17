"""POST /v1/ask — the customer-facing triage endpoint.

Wraps workflows/triage_assistant.triage() with input guards + output guards
+ observability log.

case_id contract: callers MUST pass a pre-hashed, non-PHI identifier
(e.g. "DEMO-001", "encounter-3f4a2b", or the output of
identity_mapper.patient_id_from_mrn). This endpoint defensively hashes
ANY case_id that looks MRN-shaped (>=6 consecutive digits or starts with
"MRN") before storing it in audit logs. The contract is documented in
docs/solution-design.md.

TRUST BOUNDARY (phi_log payload):
    `triage()` may echo `chief_complaint` / `hpi` fragments into
    `similar_cases` snippets or `rationale`. Those strings live in
    `result` and are written verbatim to phi_archive.jsonl. Acceptable
    because phi_archive is the restricted sink BY DESIGN.
    The metadata sink (audit_log) is shielded by _METADATA_FIELDS
    in observability.logging — only whitelisted keys survive.

TODO(response_model): wire a Pydantic ResponseModel so FastAPI generates
    accurate OpenAPI docs + prevents accidentally returning PHI fields
    in the response body. Deferred — see api/app/schemas.py in the
    sibling healthcare-ai-data-engineer repo for the pattern (reference
    contracts kept; strict decorators dropped because nested aggregates
    don't fit flat schemas without losing fidelity).
"""
from __future__ import annotations
import logging
import re
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from workflows.triage_assistant import triage
from guardrails import validate_input, InputGuardError, mask_pii
from integrations.identity_mapper import patient_id_from_mrn
from observability.logging import audit_log, phi_log

_log = logging.getLogger(__name__)
router = APIRouter()

# MRN heuristic: starts with "MRN" OR is a pure ≥6-digit string.
# Tightened from "≥6 digits anywhere" so vendor case_ids like
# "DEMO-123456" or "encounter-3f4a2b-987654" don't false-positive into
# the hash path. The two alternations still catch the actual leak
# vectors: client-side mistake passes a bare MRN, or "MRN--12345678"
# (some Epic emitters use double-dash separators — `*` not `?`).
_MRN_SHAPE = re.compile(r"^MRN[#:\s-]*\d+$|^\d{6,}$", re.IGNORECASE)


def _sanitize_case_id(raw: str) -> tuple[str, bool]:
    """Return (safe_case_id, was_rewritten). Caller adds a warning if True."""
    if raw and _MRN_SHAPE.search(raw):
        return patient_id_from_mrn(raw), True
    return raw, False


class CaseRequest(BaseModel):
    case_id: str = "anon"
    chief_complaint: str = Field(..., min_length=1)
    hpi: str = ""
    age: int | None = None
    gender: str | None = None
    arrival_mode: str = "walk-in"
    vitals: dict | None = None


@router.post("/ask")
def ask(req: CaseRequest) -> dict:
    safe_case_id, rewritten = _sanitize_case_id(req.case_id)
    try:
        clean_cc = validate_input(req.chief_complaint)
    except InputGuardError as e:
        raise HTTPException(status_code=400, detail={"error": "input_guard", "message": str(e)})

    clean_cc, pii_counts = mask_pii(clean_cc)
    clean_hpi, _ = mask_pii(req.hpi or "")

    case = {
        "case_id": safe_case_id,
        "chief_complaint": clean_cc,
        "hpi": clean_hpi,
        "age": req.age,
        "gender": req.gender,
        "arrival_mode": req.arrival_mode,
        "vitals": req.vitals or {},
    }

    try:
        result = triage(case, case_id=safe_case_id)
    except Exception as exc:
        # Never let an internal exception bubble up with the case payload
        # in the FastAPI stack trace — that would leak through error
        # middleware to whatever sink catches 500s.
        _log.exception("triage() failed for case_id=%s", safe_case_id)
        raise HTTPException(status_code=502, detail="triage engine error") from exc

    if pii_counts:
        # `warnings` is whitelisted in observability._METADATA_FIELDS —
        # vendor-emitted operational signal, not patient content.
        result.setdefault("warnings", []).append(f"pii redacted: {dict(pii_counts)}")
    if rewritten:
        result.setdefault("warnings", []).append(
            "case_id appeared MRN-shaped; hashed at API boundary"
        )

    # Split-sink audit (sanitized case_id only — never the raw MRN):
    #   metadata sink (safe for cloud index + stdout)
    audit_log(safe_case_id, "triage_decision", result)
    #   PHI archive (full payload, restricted volume only).
    #   If phi_log raises (disk full / mount issue), bubble as 502 —
    #   unlogged triage = compliance event.
    try:
        phi_log(safe_case_id, "triage_payload", result)
    except OSError as exc:
        raise HTTPException(
            status_code=502,
            detail="audit archive unavailable — triage not recorded",
        ) from exc
    return result
