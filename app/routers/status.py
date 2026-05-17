"""GET /health, GET /status — liveness and deployment-state probes."""
from __future__ import annotations
from datetime import datetime
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "healthcare-triage-assistant",
        "version": "0.1.0",
        "ts": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }


@router.get("/status")
def status() -> dict:
    """Returns deployment + integration status for the ops dashboard."""
    from app.routers.admin import _mode_state
    return {
        "mode": _mode_state["mode"],
        "ehr_connector": "mock (synthetic CSV)",
        "identity_map_age_minutes": 0,
        "ts": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }
