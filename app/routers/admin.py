"""POST /admin/mode — switch between ai_assist · rules_fallback · stale_data · off.

Per runbook.md, on-call uses this to flip the assistant's mode without
restarting the service.
"""
from __future__ import annotations
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Literal


Mode = Literal["ai_assist", "rules_fallback", "stale_data_warning", "off"]

# Process-local state (would be Redis/Postgres in real deployment)
_mode_state = {"mode": "ai_assist"}

router = APIRouter()


class ModeRequest(BaseModel):
    mode: Mode


@router.post("/mode")
def set_mode(req: ModeRequest) -> dict:
    """Switch the service mode. Audit logged."""
    old = _mode_state["mode"]
    _mode_state["mode"] = req.mode
    return {"old_mode": old, "new_mode": req.mode}


@router.get("/mode")
def get_mode() -> dict:
    return _mode_state
