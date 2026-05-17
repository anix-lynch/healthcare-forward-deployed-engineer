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

## Cross-references

- Customer context: [`customer-brief.md`](customer-brief.md)
- Day-to-day ops: [`runbook.md`](runbook.md)
- Rollout phases: [`deployment-plan.md`](deployment-plan.md)
- Handoff back to customer team: [`handoff-guide.md`](handoff-guide.md)
