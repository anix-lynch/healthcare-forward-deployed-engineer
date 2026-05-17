"""FHIR → canonical schema transform.

In production, Epic FHIR returns nested resources (Patient, Encounter,
Observation, Condition, Medication, etc.). We normalize to the canonical
shape that workflows/triage_assistant consumes.

This is the contract boundary between "customer's EHR shape" and
"our workflow's expected shape." Keeping it thin + explicit means swapping
Epic for Cerner or athenahealth is a same-file change, not a stack-wide
refactor.
"""
from __future__ import annotations


def fhir_patient_to_canonical(patient_resource: dict) -> dict:
    """FHIR Patient resource → canonical patient context (subset)."""
    return {
        "patient_mrn": _find_identifier(patient_resource, "MR"),
        "age": _calc_age(patient_resource.get("birthDate")),
        "gender": patient_resource.get("gender", "unknown"),
        "name": _flatten_name(patient_resource.get("name")),
    }


def fhir_encounter_to_canonical(encounter_resource: dict) -> dict:
    """FHIR Encounter resource → canonical encounter."""
    return {
        "encounter_id": encounter_resource.get("id"),
        "patient_mrn": _ref_to_mrn(encounter_resource.get("subject", {}).get("reference")),
        "admission_date": encounter_resource.get("period", {}).get("start"),
        "discharge_date": encounter_resource.get("period", {}).get("end"),
        "class": (encounter_resource.get("class") or {}).get("code", "AMB"),
    }


def fhir_observation_to_vitals(observations: list[dict]) -> dict:
    """FHIR Observation list → vitals dict."""
    vitals: dict = {}
    loinc_map = {
        "8480-6": "bp_sys",     # systolic BP
        "8462-4": "bp_dia",     # diastolic BP
        "8867-4": "hr",         # heart rate
        "9279-1": "rr",         # respiratory rate
        "59408-5": "spo2",      # pulse oximetry
        "8310-5": "temp_f",     # body temp
    }
    for obs in observations:
        for coding in obs.get("code", {}).get("coding", []):
            code = coding.get("code")
            if code in loinc_map:
                val = obs.get("valueQuantity", {}).get("value")
                if val is not None:
                    vitals[loinc_map[code]] = val
                break
    return vitals


# ── helpers ────────────────────────────────────────────────────────────────
def _find_identifier(resource: dict, type_code: str) -> str:
    for ident in resource.get("identifier", []):
        for coding in (ident.get("type") or {}).get("coding", []):
            if coding.get("code") == type_code:
                return ident.get("value", "")
    return ""


def _flatten_name(name_list: list[dict] | None) -> str:
    if not name_list:
        return ""
    n = name_list[0]
    given = " ".join(n.get("given") or [])
    family = n.get("family", "")
    return f"{given} {family}".strip()


def _calc_age(birth_date: str | None) -> int:
    if not birth_date:
        return 0
    try:
        from datetime import date
        yyyy = int(birth_date[:4])
        return date.today().year - yyyy
    except (ValueError, TypeError):
        return 0


def _ref_to_mrn(ref: str | None) -> str:
    """'Patient/abc123' → 'abc123' (would actually need a lookup in prod)."""
    if not ref:
        return ""
    return ref.split("/")[-1] if "/" in ref else ref
