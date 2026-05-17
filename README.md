# healthcare-forward-deployed-engineer

> **Customer-deployable ER triage assistant** — one hospital problem, one integration path, one workflow, one runbook, one postmortem. Designed for VPC deployment behind a hospital firewall, NOT vendor SaaS. The full "make AI work inside a messy enterprise" loop, not just the model internals.

[![acceptance-gate](https://github.com/anix-lynch/healthcare-forward-deployed-engineer/actions/workflows/acceptance.yml/badge.svg)](https://github.com/anix-lynch/healthcare-forward-deployed-engineer/actions/workflows/acceptance.yml)

**Built for:** AI vendor + health-tech field engineering teams who deploy AI into customer environments. The artifacts here mirror what an FDE actually owns at a hospital site — discovery brief, solution design, runbook, integrations, acceptance tests, smoke deploy, postmortem template.

```
Hospital intake event
  ↓ integrations/ehr_adapter.py            (Epic-like FHIR mock; live swap path documented)
  ↓ integrations/fhir_transform.py         (FHIR Patient/Encounter/Observation → canonical)
  ↓ integrations/identity_mapper.py        (MRN ↔ patient_id, SHA256 short hash)
  ↓ guardrails/{input,output,pii}          (sanitize · injection · citation · PHI redact)
  ↓ workflows/triage_assistant.py          (rule-based ESI + retrieval + grounded rationale)
  ↓ workflows/fallback_logic.py            (escalate-or-fallback decision)
  ↓ app/routers/ask.py                     (FastAPI surface — POST /v1/ask)
  ↓ observability/logging.py               (structured audit row → outputs/audit.jsonl)
  ↓ JSON to charge-nurse UI
```

---

## Quick demo (no server needed)

```bash
git clone https://github.com/anix-lynch/healthcare-forward-deployed-engineer
cd healthcare-forward-deployed-engineer
make install
make demo
```

Output (live, just run it):

```json
{
  "case_id": "DEMO-001",
  "esi_tier": 2,
  "tier_bucket": "NOW",
  "confidence": 0.85,
  "red_flags": [
    "high_risk_keyword:chest pain",
    "high_risk_keyword:diaphoresis",
    "tachycardia"
  ],
  "rationale": "Based on similar past records, the most relevant precedent is L1-000085: \"62yo Male, Hypertension, Emergency admission, treated with Aspirin, test results Abnormal\". Additional supporting precedents: L1-000121, L1-000149. ...",
  "citations": ["L1-000085", "L1-000121", "L1-000149"],
  "similar_cases": [
    {"source_id": "L1-000085", "snippet": "62yo Male, Hypertension, Emergency admission..."}
  ],
  "human_review_required": false,
  "mode": "ai_assist",
  "latency_ms": 6,
  "warnings": []
}
```

Or with Docker:

```bash
make docker-up
sleep 5
make smoke              # post-deploy curl checks (5 smoke tests)
```

---

## What's inside (FDE deliverables)

```
docs/                         5 customer-facing deliverables
   customer-brief.md           business problem · constraints · success metrics
   solution-design.md          end-to-end flow + component status table
   deployment-plan.md          12-phase rollout (discovery → shadow → soft → pilot → full → handoff)
   runbook.md                  P0/P1/P2 alert ladder · escalation contacts · safety floors
   handoff-guide.md            customer-team ownership matrix + first-90-day plan

demo/
   loom-script.md              5-minute walkthrough script
   sample-client-scenarios.md  5 clinical scenarios + expected AI response

integrations/                 customer-system adapters (honest mocks)
   ehr_adapter.py              Epic-like FHIR endpoint stand-in
   fhir_transform.py           FHIR Patient/Encounter/Observation → canonical
   identity_mapper.py           MRN ↔ patient_id (SHA256 short hash)
   auth/oauth_client.py         OAuth client-credentials flow stub
   auth/service_account.py      workload identity stub
   sync_jobs.py                 scheduled identity-map refresh + index warm-up

app/                          FastAPI surface (deployable service)
   main.py                      mount routers
   routers/ask.py               POST /v1/ask — the one workflow
   routers/status.py            GET /health · GET /status
   routers/admin.py             POST /admin/mode — ai_assist | rules_fallback | stale_data | off

workflows/                    the one job this deployment runs
   triage_assistant.py          rule-based ESI + retrieval + grounded rationale
                                 + pediatric/suicidal/chest-pain safety floors
   fallback_logic.py            should_escalate() + to_rules_fallback()

guardrails/                   recycled from healthcare-genai-engineer
   input_validator · output_validator · pii_masker

retrieval/                    BM25 only (no dense — minimize customer-VPC deps)
generation/                   template grounded answer + citation validation
data/raw/                     497-row enriched corpus (shared with sibling repos)

evaluation/                   customer success criteria (NOT ML metrics)
   acceptance_tests.py          5 contract tests
   eval_dataset.json            8 criteria with category + owner

observability/                structured audit logging
   logging.py                   writes outputs/audit.jsonl + stdout JSON line

deployment/                   shippable unit
   Dockerfile                   python:3.11-slim + HEALTHCHECK on /health
   docker-compose.yml           single service · :8000 · audit log volume mount
   smoke_test.sh                5 curl checks after deploy
   env/dev.env + prod.env.example

postmortems/
   integration_failure_example.md   real-shaped P1 example w/ timeline + corrective actions

tests/                        pytest — FastAPI TestClient smoke (5 tests)
Makefile · requirements.txt
```

---

## Customer acceptance tests (committed at `evaluation/acceptance_tests.py`)

These are NOT ML metrics. They're the customer-defined success criteria the
contract specifies. If any fail, the deployment isn't done.

```
✅ test_pediatric_under_1y_never_downtriaged    SAFETY · zero-tolerance per runbook
✅ test_chest_pain_with_diaphoresis_not_downtriaged  SAFETY · high-risk pattern
✅ test_well_visit_not_uptriaged                EFFICIENCY · don't burn ER resources
✅ test_p95_latency_under_target                PERFORMANCE · < 800ms target
✅ test_response_shape_complete                 CONTRACT · all required fields
```

The CI workflow (`.github/workflows/acceptance.yml`) runs these on every PR.
A failure blocks merge.

---

## How to think about this repo (FDE lens)

```
ASK                                  ANSWER (where to look)
─────────────────────────────────────────────────────────────────────
"Who's the customer?"                docs/customer-brief.md
"What problem are they solving?"     docs/customer-brief.md (Phase 1 discovery)
"How does data get IN from Epic?"    integrations/ehr_adapter.py + fhir_transform.py
"How does auth work?"                integrations/auth/oauth_client.py + service_account.py
"What does the AI actually do?"      workflows/triage_assistant.py (one workflow, scoped)
"What if AI is wrong?"               workflows/fallback_logic.py + docs/runbook.md
"How do you deploy it?"              deployment/Dockerfile + docker-compose.yml + smoke_test.sh
"How do you debug at 3am?"           docs/runbook.md alert ladder + observability/logging.py
"How does the customer take over?"   docs/handoff-guide.md (ownership matrix + 90-day plan)
"What if it breaks in production?"   postmortems/integration_failure_example.md
"What did your last go-live do?"     docs/deployment-plan.md (phases + rollback per phase)
```

---

## Common commands

```bash
make install      # pip install requirements
make serve        # uvicorn app/main on :8000
make demo         # one /v1/ask via TestClient + print JSON
make test         # pytest tests/
make acceptance   # pytest evaluation/acceptance_tests.py (customer criteria)
make docker-up    # docker-compose up -d (build + run on :8000)
make docker-down  # docker-compose down
make smoke        # bash deployment/smoke_test.sh (5 curl checks)
```

---

## Honest scope

```
WHAT THIS REPO IS                      WHAT IT'S NOT
─────────────────────────────────────────────────────────────────────
✅ one customer-deployment package      ❌ multi-customer SaaS
✅ Epic-like FHIR adapter (mocked)      ❌ real Epic API integration
✅ OAuth + workload identity stubs      ❌ live auth against customer IdP
✅ ER triage workflow with safety       ❌ FDA-cleared clinical decision tool
✅ structured audit log (JSONL)         ❌ HIPAA-compliant 7-year retention infra
✅ runbook + postmortem example         ❌ on-call rotation actually staffed
✅ acceptance tests as contract         ❌ customer signed off (this is a demo customer)
✅ Dockerfile + smoke test               ❌ production K8s deployment
```

The repo is **the FDE deliverable shape**, not a live production deployment.
What it proves: this person knows what an FDE engagement actually requires —
integrations, runbook, deployment phases, handoff, postmortem — not just
"build the model and throw it over the wall."

---

## Record your own demo (asciinema)

```bash
brew install asciinema     # one-time
asciinema rec demo.cast
# inside the recording:
make demo
# Ctrl-D to stop
asciinema upload demo.cast    # free public link
```

Plain-text `.cast` embeds cleanly in any markdown reader.

---

## Roadmap

See [ROADMAP.md](ROADMAP.md) for the phase-ordered audit trail (Phase 1 → 8,
each with the commit hash that shipped it).

---

## Related repos

- [healthcare-genai-engineer](https://github.com/anix-lynch/healthcare-genai-engineer) — Layer 2 GenAI runtime (RAG + evals + guardrails + FastAPI)
- [healthcare-ai-data-engineer](https://github.com/anix-lynch/healthcare-ai-data-engineer) — Layer 1 data backbone (dbt medallion + FastAPI + enrichment + quality gate)
- [healthcare-genai-fullstack](https://github.com/anix-lynch/healthcare-genai-fullstack) — full 3-layer monorepo

---

## License

MIT.
