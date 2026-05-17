# Solution Design

> Architectural overview of the ER triage assistant deployment. Honest about
> what runs today vs what is scaffold.

---

## End-to-end flow (one patient at the door)

```
┌─────────────────────────────────────────────────────────────────────┐
│  Patient arrives at ER door                                          │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  EHR intake event (Epic)                                             │
│  → integrations/ehr_adapter.py                                       │
│  → integrations/fhir_transform.py   (FHIR → canonical schema)        │
│  → identity_mapper resolves patient_id                               │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  guardrails/input_validator   sanitize + injection scan + PII mask   │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  workflows/triage_assistant.py                                       │
│     1) retrieval.query_pipeline.retrieve(case)                      │
│     2) classifier (ESI rule + LLM optional)                          │
│     3) generation.generate_answer(case, hits)                        │
│     4) workflows.fallback_logic if confidence < threshold            │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  guardrails/output_validator  citations valid · forbidden actions    │
│                                · min length                          │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  app/routers/ask  →  JSON response to charge nurse UI                │
│                       + observability/logging emits audit row         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component status

```
COMPONENT                                STATUS         REUSED FROM
─────────────────────────────────────────────────────────────────────
integrations/ehr_adapter.py             ⚠️ mock         NEW
integrations/fhir_transform.py          ⚠️ mock         NEW
integrations/identity_mapper.py         ✅ working       layer1 patient_identity.py
integrations/auth/oauth_client.py       ⚠️ stub          NEW (OAuth flow shape)
integrations/auth/service_account.py    ⚠️ stub          NEW
integrations/sync_jobs.py                ⚠️ stub          NEW

app/main.py + routers/                   ✅ working       healthcare-genai-engineer
retrieval/                               ✅ working       healthcare-genai-engineer (BM25 only)
generation/                              ✅ working       healthcare-genai-engineer
guardrails/                              ✅ working       healthcare-genai-engineer
workflows/triage_assistant.py           ⚠️ scaffold      NEW (reframes er-triage logic)
workflows/fallback_logic.py             ⚠️ scaffold      NEW

evaluation/acceptance_tests.py          ⚠️ scaffold      NEW (customer success criteria)
observability/logging.py                ⚠️ scaffold      NEW (structured request log)

deployment/Dockerfile                    ✅ working       NEW
deployment/docker-compose.yml            ✅ working       NEW
deployment/smoke_test.sh                 ✅ working       NEW

postmortems/integration_failure.md      ✅ documented    reframe failure_demos.json
```

---

## Honest scope

```
✅ shipped       things you can run locally today (docker-compose up)
⚠️ scaffold      interface + intent + small example body — would need
                  customer-specific build-out in a real engagement
❌ not in repo   PHI redaction at ingest (regex baseline only) ·
                  HIPAA BAA execution · live Epic credentials · 
                  multi-tenant isolation · 7-year audit retention infra
```

The repo is a **presentation cut**, not a production deployment.
The point: show that the FDE knows what shape these pieces have,
not that they're prod-ready in this synthetic context.

---

## case_id contract

`POST /v1/ask` takes a `case_id` field. Contract:

```
WHO SETS IT       caller (vendor integration / charge-nurse UI)
WHAT IT MUST BE   a pre-hashed, non-PHI identifier
                    examples:  encounter-3f4a2b · DEMO-001 · case-2026-04-17-7
                    NOT OK:    raw MRN · patient SSN · DOB · name
WHY               case_id is indexed into the metadata audit sink (audit.jsonl)
                  which flows to cloud logging. A raw MRN there = PHI in
                  cloud logs = HIPAA-adjacent.
```

Defensive boundary: `app/routers/ask.py` runs a regex on every incoming
`case_id`. If it matches an MRN shape (≥6 consecutive digits OR starts
with "MRN"), the endpoint rewrites it via
`integrations.identity_mapper.patient_id_from_mrn` and adds a warning
to the response payload (`"case_id appeared MRN-shaped; hashed at API
boundary"`). Better to over-hash than to leak.

This is fail-closed: the contract is documented here AND enforced at
the code boundary. The caller can't accidentally bypass it.

---

## Cross-references

- Customer context: [`customer-brief.md`](customer-brief.md)
- Day-to-day ops: [`runbook.md`](runbook.md)
- Rollout phases: [`deployment-plan.md`](deployment-plan.md)
- Handoff back to customer team: [`handoff-guide.md`](handoff-guide.md)
