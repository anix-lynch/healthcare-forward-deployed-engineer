"""LangGraph stateful triage agent with checkpointing.

Titan JD signal: "stateful agent — tool calling, planning loops, state/memory
across sessions, checkpointed so failures resume mid-flow"

Graph:
    intake → retrieve → generate → validate → hitl_gate → respond
                                       ↓ (low confidence)
                                    escalate

State persists across requests via thread_id — same case_id resumes
from last checkpoint rather than restarting from scratch.

Checkpointing: MemorySaver (in-process, dev-friendly).
Production upgrade path: swap for SqliteSaver or RedisSaver for
multi-instance / cross-restart durability.
"""
from __future__ import annotations

import logging
import time
from typing import Annotated, Any, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

from generation.generate import generate_answer
from retrieval.query_pipeline import QueryPipeline
from workflows.fallback_logic import should_escalate, to_rules_fallback
from workflows.hitl_gate import check_hitl_required, create_hitl_request
from workflows.reliability import idempotent, retry
from workflows.triage_assistant import _compute_confidence, _esi_from_case

_log = logging.getLogger(__name__)

# ── State schema ────────────────────────────────────────────────────────────

class TriageState(TypedDict):
    # Input
    case: dict
    case_id: str
    # Retrieved context
    hits: list[dict]
    query: str
    # Classification
    esi_tier: int
    confidence: float
    red_flags: list[str]
    # Generation
    gen_answer: str
    gen_citations: list[dict]
    gen_warnings: list[str]
    # Control
    requires_hitl: bool
    hitl_reason: str
    escalate: bool
    # Output
    result: dict | None
    # Timing
    t0: float


# ── Node implementations ─────────────────────────────────────────────────────

def node_intake(state: TriageState) -> dict:
    case = state["case"]
    query = f"{case.get('chief_complaint', '')} {case.get('hpi', '')[:200]}".strip()
    return {"query": query, "t0": time.time()}


@retry(max_attempts=3, backoff="exponential", exceptions=(Exception,))
@idempotent(key_fn=lambda *a, **kw: a[0]["case_id"])
def _retrieve(state: TriageState) -> dict:
    pipeline = QueryPipeline()
    hits = pipeline.retrieve(state["query"], k=5, method="bm25")
    return {"hits": hits}


def node_retrieve(state: TriageState) -> dict:
    return _retrieve(state)


def node_generate(state: TriageState) -> dict:
    esi, _, red_flags = _esi_from_case(state["case"])
    confidence = _compute_confidence(
        hits=state["hits"],
        red_flags=red_flags,
        vitals=state["case"].get("vitals"),
    )
    gen = generate_answer(state["query"], state["hits"])
    return {
        "esi_tier": esi,
        "confidence": confidence,
        "red_flags": red_flags,
        "gen_answer": gen["answer"],
        "gen_citations": gen["citations"],
        "gen_warnings": gen.get("warnings", []),
    }


def node_validate(state: TriageState) -> dict:
    escalate = should_escalate(state["esi_tier"], state["confidence"], state["red_flags"])
    requires_hitl, hitl_reason = check_hitl_required({
        "esi_tier": state["esi_tier"],
        "confidence": state["confidence"],
        "red_flags": state["red_flags"],
        "human_review_required": escalate,
        "mode": "ai_assist",
    })
    return {
        "escalate": escalate,
        "requires_hitl": requires_hitl,
        "hitl_reason": hitl_reason,
    }


def node_hitl(state: TriageState) -> dict:
    pending = create_hitl_request(
        case_id=state["case_id"],
        trigger_reason=state["hitl_reason"],
        ai_suggestion={
            "esi_tier": state["esi_tier"],
            "confidence": state["confidence"],
            "red_flags": state["red_flags"],
        },
    )
    result = {
        "case_id": state["case_id"],
        "status": "pending_human_review",
        "hitl_request_id": pending.request_id,
        "hitl_reason": state["hitl_reason"],
        "esi_tier": state["esi_tier"],
        "mode": "hitl_pending",
        "latency_ms": int((time.time() - state["t0"]) * 1000),
    }
    return {"result": result}


def node_escalate(state: TriageState) -> dict:
    result = to_rules_fallback(
        state["case_id"],
        state["case"],
        state["esi_tier"],
        state["red_flags"],
        state["gen_answer"],
        latency_ms=int((time.time() - state["t0"]) * 1000),
    )
    return {"result": result}


def node_respond(state: TriageState) -> dict:
    result = {
        "case_id": state["case_id"],
        "esi_tier": state["esi_tier"],
        "tier_bucket": "NOW" if state["esi_tier"] <= 2 else "SOON" if state["esi_tier"] == 3 else "WAIT",
        "confidence": state["confidence"],
        "red_flags": state["red_flags"],
        "rationale": state["gen_answer"],
        "citations": state["gen_citations"],
        "similar_cases": [
            {"source_id": h["case_id"], "snippet": (h.get("snippet") or "")[:200]}
            for h in state["hits"][:3]
        ],
        "human_review_required": state["esi_tier"] == 1 or state["confidence"] < 0.7
            or any(f.startswith("safety_floor:") for f in state["red_flags"]),
        "mode": "ai_assist",
        "latency_ms": int((time.time() - state["t0"]) * 1000),
        "warnings": state["gen_warnings"],
    }
    return {"result": result}


# ── Routing ──────────────────────────────────────────────────────────────────

def route_after_validate(state: TriageState) -> str:
    if state["requires_hitl"]:
        return "hitl"
    if state["escalate"]:
        return "escalate"
    return "respond"


# ── Graph assembly ────────────────────────────────────────────────────────────

def build_graph(checkpointer=None):
    g = StateGraph(TriageState)

    g.add_node("intake", node_intake)
    g.add_node("retrieve", node_retrieve)
    g.add_node("generate", node_generate)
    g.add_node("validate", node_validate)
    g.add_node("hitl", node_hitl)
    g.add_node("escalate", node_escalate)
    g.add_node("respond", node_respond)

    g.set_entry_point("intake")
    g.add_edge("intake", "retrieve")
    g.add_edge("retrieve", "generate")
    g.add_edge("generate", "validate")
    g.add_conditional_edges("validate", route_after_validate, {
        "hitl": "hitl",
        "escalate": "escalate",
        "respond": "respond",
    })
    g.add_edge("hitl", END)
    g.add_edge("escalate", END)
    g.add_edge("respond", END)

    saver = checkpointer or MemorySaver()
    return g.compile(checkpointer=saver)


# Singleton graph — shared across requests in same process
_GRAPH = None

def get_graph():
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = build_graph()
    return _GRAPH


def triage_stateful(case: dict, *, case_id: str = "anon") -> dict:
    """Run triage via LangGraph stateful graph.

    Same interface as workflows.triage_assistant.triage() so the router
    can swap between implementations via feature flag.

    thread_id = case_id enables state continuity: if the same case is
    re-submitted (e.g. after HITL approval), the graph resumes from the
    last checkpoint rather than starting over.
    """
    graph = get_graph()
    initial_state: TriageState = {
        "case": case,
        "case_id": case_id,
        "hits": [],
        "query": "",
        "esi_tier": 4,
        "confidence": 0.0,
        "red_flags": [],
        "gen_answer": "",
        "gen_citations": [],
        "gen_warnings": [],
        "requires_hitl": False,
        "hitl_reason": "",
        "escalate": False,
        "result": None,
        "t0": time.time(),
    }
    config = {"configurable": {"thread_id": case_id}}
    final = graph.invoke(initial_state, config=config)
    return final["result"]
