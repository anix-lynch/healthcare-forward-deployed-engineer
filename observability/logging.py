"""Structured audit logging — TWO sinks, split by PHI sensitivity.

Sink 1: outputs/audit.jsonl (+ stdout mirror)
    Metadata-only. Safe for indexed cloud logging (Cloud Logging /
    App Insights / CloudWatch). NO rationale, NO similar_cases,
    NO snippets. Fields: ts, case_id, event, esi_tier, confidence,
    mode, latency_ms, red_flag_count, human_review_required.

Sink 2: outputs/phi_archive.jsonl (NO stdout mirror)
    Full payload including rationale + similar_cases snippets. These
    snippets ARE past-patient narrative text in real Epic-backed
    retrieval, so they are PHI-adjacent. This sink must be on a
    restricted-access volume with 7-year HIPAA Safe Harbor retention
    + access audit. NEVER mirrored to stdout (container logs would
    flow to Cloud Logging unfiltered).

Retention: customer is responsible for 7-year HIPAA Safe Harbor
on the PHI archive. Metadata sink can be 30-90 days for ops.
"""
from __future__ import annotations
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parents[1] / "outputs"
AUDIT_PATH = LOG_DIR / "audit.jsonl"        # metadata only — safe for cloud index
PHI_PATH = LOG_DIR / "phi_archive.jsonl"    # full payload — restricted volume

# Whitelist of payload fields that are safe for the metadata audit sink.
# Anything not in this list (rationale, similar_cases, snippet, etc.)
# is PHI-adjacent and goes to the PHI archive only.
_METADATA_FIELDS = {
    "esi_tier",
    "tier_bucket",
    "confidence",
    "mode",
    "latency_ms",
    "human_review_required",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _metadata_only(payload: dict) -> dict:
    """Strip PHI-adjacent fields. Keep counts; drop free text."""
    out = {k: payload.get(k) for k in _METADATA_FIELDS if k in payload}
    if "red_flags" in payload:
        out["red_flag_count"] = len(payload["red_flags"] or [])
    if "citations" in payload:
        out["citation_count"] = len(payload["citations"] or [])
    return out


def audit_log(case_id: str, event: str, payload: dict) -> None:
    """Metadata audit row — safe for stdout + indexed cloud logging.

    Caller passes the full payload; this fn whitelists safe fields.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    row = {
        "ts": _now_iso(),
        "case_id": case_id,
        "event": event,
        "payload": _metadata_only(payload) if isinstance(payload, dict) else payload,
    }
    line = json.dumps(row, default=str)
    with AUDIT_PATH.open("a") as f:
        f.write(line + "\n")
    # Mirror to stdout so docker-compose / kubectl logs picks it up.
    # Safe because payload is already metadata-only.
    print(line, file=sys.stdout, flush=True)


def phi_log(case_id: str, event: str, payload: dict) -> None:
    """PHI archive row — full payload, restricted sink, NO stdout mirror.

    Production must mount outputs/phi_archive.jsonl on a volume with
    access ACLs + 7-year retention + an access-audit trail.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    row = {
        "ts": _now_iso(),
        "case_id": case_id,
        "event": event,
        "payload": payload,
    }
    with PHI_PATH.open("a") as f:
        f.write(json.dumps(row, default=str) + "\n")
    # NOT mirrored to stdout — would leak PHI to container log sink.


def get_recent_logs(limit: int = 20) -> list[dict]:
    """Return the last N audit (metadata) rows. Used by /admin/recent."""
    if not AUDIT_PATH.exists():
        return []
    with AUDIT_PATH.open() as f:
        lines = f.readlines()
    return [json.loads(l) for l in lines[-limit:] if l.strip()]
