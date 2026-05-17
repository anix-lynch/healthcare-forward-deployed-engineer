"""POST /admin/mode — switch between ai_assist · rules_fallback · stale_data · off.

Per runbook.md, on-call uses this to flip the assistant's mode without
restarting the service.

AUTH: bearer token from ADMIN_BEARER_TOKEN env var. If unset, endpoints
are open (dev-mode warning logged at startup). In production this MUST
be set — flipping the assistant off is a P0-blast-radius operation.
"""
from __future__ import annotations
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


def _admin_token_or_warn() -> str | None:
    """Read ADMIN_BEARER_TOKEN. Emit one-time startup warning if unset."""
    tok = os.environ.get("ADMIN_BEARER_TOKEN")
    if not tok:
        _log.warning(
            "admin endpoints unprotected — ADMIN_BEARER_TOKEN unset "
            "(acceptable in dev; in prod set via secret manager)."
        )
    return tok


def require_admin(
    authorization: str | None = Header(default=None),
) -> str:
    """FastAPI dep: validate Bearer <ADMIN_BEARER_TOKEN>, return actor id.

    Actor id = sha256 prefix of the presented token (never echoed in full).
    If ADMIN_BEARER_TOKEN env var is unset (dev only), all calls pass with
    actor='dev-unauth'.
    """
    expected = _admin_token_or_warn()
    if expected is None:
        return "dev-unauth"
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="missing bearer token")
    presented = authorization.removeprefix("Bearer ").strip()
    # hmac.compare_digest = constant-time string compare (timing-safe).
    if not hmac.compare_digest(presented, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="invalid bearer token")
    import hashlib
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
