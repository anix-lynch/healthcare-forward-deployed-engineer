# TITAN HANDOVER — FDE Portco Build Direction
**JD:** Forward Deployed Engineer (Agentic Systems) — Titan Holdings Group | $120–210k  
**Date:** 2026-05-31  
**Purpose:** Gap analysis + next build priorities to make this repo match Titan's actual bar

---

## WHAT TITAN WANTS vs WHAT EXISTS

```
TITAN REQUIREMENT              REPO STATE          GAP
─────────────────────────────────────────────────────────────────
LangGraph stateful agent       workflows/           ❌ Custom, not LangGraph
  checkpointed across sessions triage_assistant.py     No state persistence
  
HITL approval gate             ❌ Not implemented       Must add explicit human
  human-in-the-loop controls                           approval step pattern

Tool registry                  integrations/        ⚠️  EHR/FHIR only
  Slack/SQL/SharePoint/SF       ehr_adapter.py          No Slack/SQL/SharePoint
  named connectors                                      connectors

Retry/timeout decorator        workflows/           ⚠️  fallback_logic.py exists
  idempotency keys              fallback_logic.py       but no @retry decorator
  checkpoint/resume on fail                             no idempotency keys

OpenTelemetry tracing          observability/       ❌ Custom logging only
  structured prompt+tool tags   logging.py              No OTEL spans

Cost/latency dashboard         ❌ Not built             Langfuse or custom needed

Dataset replay pipeline        evaluation/          ⚠️  eval_dataset.json exists
  offline regression suite      acceptance_tests.py     but not framed as "replay"

Temporal/Cadence               ❌ Not in stack           Acceptable gap —
  workflow engine                                        frame Dagster/Airflow
```

---

## WHAT'S ALREADY STRONG (keep, just name it right)

```
guardrails/pii_masker.py       → "PII masking + compliance hooks" ✅
integrations/auth/oauth_client → "Enterprise auth layer (OAuth/RBAC)" ✅
observability/audit_report.py  → "Append-only audit log" ✅
evaluation/acceptance_tests.py → "Acceptance-gated CI" ✅
docs/customer-brief.md         → "Discovery → solution design arc" ✅
postmortems/                   → "Production failure postmortem" ✅ rare proof point
```

---

---

## BEFORE / AFTER — changes shipped 2026-05-31

| Signal | Before | After |
|---|---|---|
| Stateful agent | Custom `triage()` fn, no state graph, no checkpoint | LangGraph `StateGraph` 8-node graph, `MemorySaver` checkpoint, thread_id = case_id → resumes mid-flow |
| HITL gate | `human_review_required` flag in response only | `hitl_gate.py` — pauses execution, persists to SQLite, `/admin/review` to approve/reject, TTL auto-escalate |
| Reliability | `fallback_logic.py` (escalation only) | `reliability.py` — `@retry(exponential)`, `@idempotent(sha256 key)`, `@with_timeout` decorators |
| Observability | Custom JSONL audit logging | + OTEL spans on `fde.triage.decision` (case_id, esi_tier, confidence, mode, latency_ms, red_flag_count) |
| Eval framing | `acceptance_tests.py` + `eval_dataset.json` | + `replay_pipeline.py` — dataset replay, pass-rate regression gate (exit 1 if < 85%), matches Titan's exact phrase |
| Deploy | Cloud Run @ healthcare-fde | Re-deployed ✅ smoke test passed: ESI 2 / conf 0.95 / chest pain + diaphoresis + hypotension |

**Live URL:** `https://healthcare-fde-2ihyeqmb6q-uw.a.run.app`

**Smoke test result (2026-05-31):**
```json
{
  "esi_tier": 2, "tier_bucket": "NOW", "confidence": 0.95,
  "red_flags": ["chest pain", "diaphoresis", "hypotension"],
  "mode": "ai_assist", "human_review_required": true
}
```

---

## NEXT BUILD PRIORITIES (ordered by Titan signal strength)

### P1 — LangGraph stateful agent (biggest gap, biggest signal)
Replace `workflows/triage_assistant.py` with LangGraph StateGraph:
```python
# workflows/langgraph_triage.py
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver  # checkpointing

# nodes: intake → retrieve → generate → validate → HITL_gate → respond
# edges: validate fails → retry; HITL rejects → escalate
```
Proof point: "stateful agent with checkpoint/resume" = Titan's exact ask

### P2 — HITL approval gate
Add `workflows/hitl_gate.py`:
- Pause execution, write pending state to SQLite
- Resume on approval signal (webhook or CLI flag)
- Frame as: "human approval before high-risk tool calls"

### P3 — @retry + idempotency decorator  
Add `workflows/reliability.py`:
```python
@retry(max_attempts=3, backoff=exponential)
@idempotent(key_fn=lambda call: hash(call.tool + call.args))
def execute_tool(call): ...
```
One file, huge signal on reliability

### P4 — OpenTelemetry spans (partial is fine)
Add OTEL to `observability/logging.py`:
```python
from opentelemetry import trace
tracer = trace.get_tracer("fde.triage")
with tracer.start_as_current_span("llm.generate") as span:
    span.set_attribute("prompt.version", version)
    span.set_attribute("model", model_name)
```
Even partial = "OTEL-instrumented" on resume

### P5 — Frame eval as "dataset replay pipeline"
Rename/wrap `evaluation/acceptance_tests.py` → add `evaluation/replay_pipeline.py`:
- Load `eval_dataset.json`
- Replay each case through live pipeline
- Compare output vs expected → regression gate
Exact phrase Titan used: "dataset replay pipeline"

---

## RESUME KEYWORD PATCH (ATS gaps for this JD)

Add these exact phrases to resume bullet points:
```
❌ LangGraph (stateful, checkpointed)     → add after healthcare agent work
❌ HITL controls                           → add to guardrails/workflow section
❌ Idempotency / retry / checkpointing     → add to reliability section
❌ OpenTelemetry                           → add to observability section
❌ Dataset replay pipeline                 → frame existing Ragas eval as this
❌ Enterprise integration (OAuth/RBAC/audit) → already built, just name it
```

---

## THE ONE THING THAT WINS THIS JD

The repo already proves the **arc**: discovery brief → solution design → deployment → eval → postmortem.

Titan's exact ask: *"0→1 enterprise deployer who owns the full arc"*

That story is already here. The code gaps (LangGraph, OTEL) are addable in 1-2 sittings.  
The **arc proof** — most candidates can't show this at all.

---

*Next session: start with P1 (LangGraph stateful agent). Everything else follows.*
