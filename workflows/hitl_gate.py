"""Human-in-the-loop (HITL) approval gate.

Titan JD signal: "HITL controls — pause execution, require human approval
before high-risk tool calls proceed"

Pattern:
    1. Agent reaches a decision that requires human sign-off
    2. Execution PAUSES — state persisted to SQLite
    3. Human reviews via /admin/review endpoint or CLI
    4. On approval → resume; on rejection → escalate

States:
    PENDING   → awaiting human decision
    APPROVED  → human approved, execution resumes
    REJECTED  → human rejected, escalate to attending
    EXPIRED   → TTL exceeded, auto-escalate
"""
from __future__ import annotations

import json
import logging
import sqlite3
import time
import uuid
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any

_log = logging.getLogger(__name__)

HITL_DB_PATH = Path("outputs/hitl_pending.db")
HITL_TTL_SECONDS = 300  # 5 min — after this, auto-escalate


class HITLDecision(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


@dataclass
class HITLRequest:
    request_id: str
    case_id: str
    trigger_reason: str       # why HITL fired (e.g. "esi_1", "low_confidence")
    ai_suggestion: dict       # what the AI proposed
    created_at: float
    decided_at: float | None
    decision: HITLDecision
    reviewer_note: str


def _get_db() -> sqlite3.Connection:
    HITL_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(HITL_DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS hitl_requests (
            request_id TEXT PRIMARY KEY,
            case_id TEXT,
            trigger_reason TEXT,
            ai_suggestion TEXT,
            created_at REAL,
            decided_at REAL,
            decision TEXT,
            reviewer_note TEXT
        )
    """)
    conn.commit()
    return conn


def create_hitl_request(
    case_id: str,
    trigger_reason: str,
    ai_suggestion: dict,
) -> HITLRequest:
    """Pause execution and create a pending HITL request.

    Returns the HITLRequest — caller should stop processing and
    return a 'pending_human_review' response to the API consumer.
    """
    req = HITLRequest(
        request_id=str(uuid.uuid4())[:8],
        case_id=case_id,
        trigger_reason=trigger_reason,
        ai_suggestion=ai_suggestion,
        created_at=time.time(),
        decided_at=None,
        decision=HITLDecision.PENDING,
        reviewer_note="",
    )
    with _get_db() as conn:
        conn.execute(
            """INSERT INTO hitl_requests VALUES (?,?,?,?,?,?,?,?)""",
            (
                req.request_id, req.case_id, req.trigger_reason,
                json.dumps(req.ai_suggestion), req.created_at,
                req.decided_at, req.decision.value, req.reviewer_note,
            ),
        )
    _log.warning(
        "hitl_pause case_id=%s request_id=%s reason=%s",
        case_id, req.request_id, trigger_reason,
    )
    return req


def resolve_hitl_request(
    request_id: str,
    decision: HITLDecision,
    reviewer_note: str = "",
) -> HITLRequest | None:
    """Human resolves a pending HITL request (approve or reject)."""
    now = time.time()
    with _get_db() as conn:
        conn.execute(
            """UPDATE hitl_requests
               SET decision=?, decided_at=?, reviewer_note=?
               WHERE request_id=? AND decision='PENDING'""",
            (decision.value, now, reviewer_note, request_id),
        )
        row = conn.execute(
            "SELECT * FROM hitl_requests WHERE request_id=?", (request_id,)
        ).fetchone()
    if not row:
        return None
    return _row_to_request(row)


def get_pending_requests(case_id: str | None = None) -> list[HITLRequest]:
    """Return all PENDING requests, optionally filtered by case_id."""
    with _get_db() as conn:
        if case_id:
            rows = conn.execute(
                "SELECT * FROM hitl_requests WHERE decision='PENDING' AND case_id=?",
                (case_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM hitl_requests WHERE decision='PENDING'"
            ).fetchall()

    # Expire stale requests
    expired = []
    live = []
    for row in rows:
        req = _row_to_request(row)
        if (time.time() - req.created_at) > HITL_TTL_SECONDS:
            expired.append(req)
        else:
            live.append(req)

    if expired:
        _expire_requests([r.request_id for r in expired])

    return live


def check_hitl_required(triage_result: dict) -> tuple[bool, str]:
    """Decide if triage result should be gated by HITL before returning to client.

    Returns (requires_hitl, reason).
    Gate on ESI 1 or explicit human_review_required=True with safety flags.
    """
    if triage_result.get("esi_tier") == 1:
        return True, "esi_1_resuscitation"
    if triage_result.get("mode") == "rules_fallback":
        return True, "rules_fallback_mode"
    red_flags = triage_result.get("red_flags", [])
    if any(f.startswith("safety_floor:") for f in red_flags):
        return True, f"safety_floor:{red_flags[0]}"
    return False, ""


def _expire_requests(request_ids: list[str]) -> None:
    with _get_db() as conn:
        conn.executemany(
            "UPDATE hitl_requests SET decision='EXPIRED', decided_at=? WHERE request_id=?",
            [(time.time(), rid) for rid in request_ids],
        )


def _row_to_request(row: tuple) -> HITLRequest:
    return HITLRequest(
        request_id=row[0],
        case_id=row[1],
        trigger_reason=row[2],
        ai_suggestion=json.loads(row[3]),
        created_at=row[4],
        decided_at=row[5],
        decision=HITLDecision(row[6]),
        reviewer_note=row[7] or "",
    )
