"""EHR adapter — Epic-like FHIR endpoint mock.

This is a STAND-IN. In a real engagement, this file talks to the customer's
Epic FHIR API via OAuth client credentials (see auth/oauth_client.py).
Here we read from a local JSON file so the rest of the stack can be
demoed end-to-end without Epic credentials.

Public contract:
    fetch_patient_intake(patient_mrn) -> dict | None
    fetch_recent_encounters(patient_mrn, limit=10) -> list[dict]
    list_active_intakes() -> list[dict]

In production, swap the JSON read for a `httpx.get` against the Epic FHIR
base URL + bearer token. Shape stays the same.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
MOCK_DATA = REPO_ROOT / "data" / "raw" / "healthcare_dataset.csv"


def _load_mock_rows() -> list[dict]:
    """Read the local synthetic CSV as a stand-in for Epic FHIR responses."""
    import csv
    if not MOCK_DATA.exists():
        return []
    with MOCK_DATA.open(newline="") as f:
        return list(csv.DictReader(f))


def fetch_patient_intake(patient_mrn: str) -> Optional[dict]:
    """Return the latest intake event for a patient, or None."""
    rows = _load_mock_rows()
    for r in rows:
        if (r.get("Name") or "").lower().replace(" ", "_") == patient_mrn.lower():
            return _to_intake(r)
    return None


def fetch_recent_encounters(patient_mrn: str, limit: int = 10) -> list[dict]:
    """Return the last N encounters for a patient (most recent first)."""
    rows = _load_mock_rows()
    hits = [r for r in rows if (r.get("Name") or "").lower().replace(" ", "_") == patient_mrn.lower()]
    hits.sort(key=lambda r: r.get("Date of Admission", ""), reverse=True)
    return [_to_encounter(r) for r in hits[:limit]]


def list_active_intakes(*, limit: int = 10) -> list[dict]:
    """Return currently-active intake events (most recent first).

    Production contract: hits Epic's `GET /Encounter?status=in-progress&_count=N`.
    Returns FHIR Encounter resources with `status=in-progress` ONLY.

    Mock proxy: the Kaggle synthetic dataset has no `encounter.status` column,
    so we approximate "active" with `Admission Type == Emergency`. This is an
    honest proxy, NOT a contract match — flagged here so a reviewer doesn't
    assume the mock filter and the production filter are equivalent.
    """
    rows = _load_mock_rows()
    # Sort most-recent-first to mirror Epic's default ordering.
    rows.sort(key=lambda r: r.get("Date of Admission", ""), reverse=True)
    active = [r for r in rows if r.get("Admission Type") == "Emergency"]
    return [_to_intake(r) for r in active[:limit]]


def _to_intake(row: dict) -> dict:
    return {
        "patient_mrn": (row.get("Name") or "").lower().replace(" ", "_"),
        "chief_complaint": row.get("chief_complaint") or row.get("Medical Condition", ""),
        "hpi": row.get("hpi", ""),
        "vitals": {
            "bp_sys": row.get("bp_systolic") or None,
            "hr":     row.get("heart_rate") or None,
            "rr":     row.get("respiratory_rate") or None,
            "spo2":   row.get("spo2_pct") or None,
            "temp_f": row.get("temperature_f") or None,
        },
        "arrival_mode": "ambulance" if row.get("Admission Type") == "Emergency" else "walk-in",
        "_source": "mock_csv",
    }


def _to_encounter(row: dict) -> dict:
    return {
        "encounter_id": f"L1-{hash(row.get('Name','')+row.get('Date of Admission','')) & 0xFFFFFF:06x}",
        "patient_mrn": (row.get("Name") or "").lower().replace(" ", "_"),
        "admission_date": row.get("Date of Admission"),
        "discharge_date": row.get("Discharge Date"),
        "condition":  row.get("Medical Condition"),
        "medication": row.get("Medication"),
        "_source": "mock_csv",
    }
