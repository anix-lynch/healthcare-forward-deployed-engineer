"""POST /v1/ask — the customer-facing triage endpoint.

Wraps workflows/triage_assistant.triage() with input guards + output guards
+ observability log.
"""
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from workflows.triage_assistant import triage
from guardrails import validate_input, InputGuardError, mask_pii
from observability.logging import audit_log

router = APIRouter()


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
    try:
        clean_cc = validate_input(req.chief_complaint)
    except InputGuardError as e:
        raise HTTPException(status_code=400, detail={"error": "input_guard", "message": str(e)})

    clean_cc, pii_counts = mask_pii(clean_cc)
    clean_hpi, _ = mask_pii(req.hpi or "")

    case = {
        "case_id": req.case_id,
        "chief_complaint": clean_cc,
        "hpi": clean_hpi,
        "age": req.age,
        "gender": req.gender,
        "arrival_mode": req.arrival_mode,
        "vitals": req.vitals or {},
    }

    result = triage(case, case_id=req.case_id)
    if pii_counts:
        result.setdefault("warnings", []).append(f"pii redacted: {dict(pii_counts)}")

    audit_log(req.case_id, "triage", result)
    return result
