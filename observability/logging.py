"""Structured audit logging — every triage decision gets one row.

Today: writes to outputs/audit.jsonl + stdout JSON line.
Production swap path: ship to Cloud Logging / Application Insights / CloudWatch
via shared infra. Same shape, different sink.

Retention: customer is responsible for 7-year HIPAA Safe Harbor retention.
"""
from __future__ import annotations
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parents[1] / "outputs"
LOG_PATH = LOG_DIR / "audit.jsonl"


def audit_log(case_id: str, event: str, payload: dict) -> None:
    """Write one structured audit record + emit to stdout."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    row = {
        # tz-aware now() — datetime.utcnow() is deprecated in 3.12+
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "case_id": case_id,
        "event": event,
        "payload": payload,
    }
    line = json.dumps(row, default=str)
    with LOG_PATH.open("a") as f:
        f.write(line + "\n")
    # Mirror to stdout so docker-compose / kubectl logs picks it up
    print(line, file=sys.stdout, flush=True)


def get_recent_logs(limit: int = 20) -> list[dict]:
    """Return the last N audit rows. Used by /admin/recent."""
    if not LOG_PATH.exists():
        return []
    with LOG_PATH.open() as f:
        lines = f.readlines()
    return [json.loads(l) for l in lines[-limit:] if l.strip()]
