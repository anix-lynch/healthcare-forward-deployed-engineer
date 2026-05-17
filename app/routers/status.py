"""GET /health, GET /status — liveness and deployment-state probes."""
from __future__ import annotations
from datetime import datetime, timezone
from fastapi import APIRouter

router = APIRouter()


def _now_iso() -> str:
    """tz-aware UTC now() — datetime.utcnow() is deprecated in 3.12+."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


@router.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "healthcare-triage-assistant",
        "version": "0.1.0",
        "ts": _now_iso(),
    }


@router.get("/status")
def status() -> dict:
    """Returns deployment + integration status for the ops dashboard."""
    from app.routers.admin import _mode_state
    return {
        "mode": _mode_state["mode"],
        "ehr_connector": "mock (synthetic CSV)",
        "identity_map_age_minutes": 0,
        "ts": _now_iso(),
    }
