"""POST /admin/mode — switch between ai_assist · rules_fallback · stale_data · off.

Per runbook.md, on-call uses this to flip the assistant's mode without
restarting the service.

AUTH POSTURE — secure-by-default, opt-out for dev:
  - ADMIN_BEARER_TOKEN set  → bearer auth required (production posture)
  - ADMIN_BEARER_TOKEN unset → 503 Service Unavailable on every admin
                                call, UNLESS ADMIN_AUTH_DISABLED=1 is
                                also set (explicit dev escape hatch).
  - both unset             → 503 (fail-closed default; matches HIPAA
                                deployment posture: never silently
                                ship unauthenticated admin endpoints).

The escape hatch is intentionally explicit — the dev sets ONE extra env
var; the prod deploy can't accidentally turn off auth by forgetting to
set the bearer token. Same dev ergonomics, prod-safe by construction.
"""
from __future__ import annotations
import hashlib
import hmac
import logging
import os
from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel

from observability.logging import audit_log


_log = logging.getLogger(__name__)

Mode = Literal["ai_assist", "rules_fallback", "stale_data_warning", "off"]

# Process-local state (would be Redis/Postgres in real deployment)
_mode_state = {"mode": "ai_assist"}

router = APIRouter()


def require_admin(
    authorization: str | None = Header(default=None),
) -> str:
    """FastAPI dep: validate Bearer <ADMIN_BEARER_TOKEN>, return actor id.

    Fail-closed posture:
      - bearer token set + valid bearer header → actor-<sha8> returned
      - bearer token set + missing/invalid header → 401
      - bearer token unset + ADMIN_AUTH_DISABLED=1 → actor='dev-unauth-explicit'
        (escape hatch, warning emitted)
      - bearer token unset, no escape hatch → 503 (refuse to serve admin)
    """
    expected = os.environ.get("ADMIN_BEARER_TOKEN")
    if not expected:
        if os.environ.get("ADMIN_AUTH_DISABLED") == "1":
            _log.warning(
                "admin endpoints OPEN — ADMIN_AUTH_DISABLED=1 is set "
                "(dev escape hatch). NEVER ship this combination to prod."
            )
            return "dev-unauth-explicit"
        # Fail-closed: refuse to serve admin until the deploy is configured.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "admin endpoints not configured — set ADMIN_BEARER_TOKEN, "
                "or ADMIN_AUTH_DISABLED=1 for explicit dev mode"
            ),
        )
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="missing bearer token")
    presented = authorization.removeprefix("Bearer ").strip()
    # hmac.compare_digest = constant-time string compare (timing-safe).
    if not hmac.compare_digest(presented, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="invalid bearer token")
    return "actor-" + hashlib.sha256(presented.encode()).hexdigest()[:8]


class ModeRequest(BaseModel):
    mode: Mode


@router.post("/mode")
def set_mode(req: ModeRequest, actor: str = Depends(require_admin)) -> dict:
    """Switch the service mode. Auth-required + audit logged."""
    old = _mode_state["mode"]
    _mode_state["mode"] = req.mode
    audit_log(
        case_id="_admin_",
        event="admin_mode_change",
        payload={"old": old, "new": req.mode, "actor": actor},
    )
    return {"old_mode": old, "new_mode": req.mode}


@router.get("/mode")
def get_mode() -> dict:
    return _mode_state
