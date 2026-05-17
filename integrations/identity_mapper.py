"""Patient identity mapper — encounter_id → patient_id resolver.

Same shape as layer1's patient_identity.py in the master monorepo. For the
customer engagement, this would be backed by Epic MRN; here we use a
deterministic short SHA256 of the normalized patient name.
"""
from __future__ import annotations
import hashlib


def normalize_name(name: str) -> str:
    """Collapse whitespace + lowercase. 'Bobby JacksOn' → 'bobby jackson'."""
    if not name:
        return ""
    return " ".join(name.lower().split())


def patient_id_from_name(name: str) -> str:
    """Deterministic short patient_id. Stable across encounters of same patient."""
    norm = normalize_name(name)
    if not norm:
        return "P-unknown"
    return "P-" + hashlib.sha256(norm.encode("utf-8")).hexdigest()[:10]


def patient_id_from_mrn(mrn: str) -> str:
    """In customer engagement: MRN passes through (already stable + unique)."""
    return f"MRN-{mrn}" if mrn else "P-unknown"
