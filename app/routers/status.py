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


def _active_ehr_connector_name() -> str:
    """Resolve which EHR connector is wired today.

    Today: the import-resolved ehr_adapter module name + mode tag.
    Production: read from an env var (e.g. EHR_CONNECTOR=epic_prod_us_east)
    that the deploy pipeline sets per customer / per environment, so /status
    shows "epic_prod_us_east" or "cerner_dev_eu_central" without code change.
    """
    import os
    from integrations import ehr_adapter
    return os.environ.get("EHR_CONNECTOR", f"{ehr_adapter.__name__} (mock: synthetic CSV)")


@router.get("/status")
def status() -> dict:
    """Returns deployment + integration status for the ops dashboard."""
    from app.routers.admin import _mode_state
    return {
        "mode": _mode_state["mode"],
        "ehr_connector": _active_ehr_connector_name(),
        "identity_map_age_minutes": 0,
        "ts": _now_iso(),
    }
