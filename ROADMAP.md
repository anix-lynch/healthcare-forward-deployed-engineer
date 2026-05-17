# Roadmap — Incremental Population from Monorepo

Source of truth: [`healthcare-genai-fullstack`](https://github.com/anix-lynch/healthcare-genai-fullstack).
This file tracks what landed in the FDE view, in small commits.

**Sequencing principle:** customer-facing docs FIRST, then integrations, then
the one workflow, then operational polish + CI. The FDE story is the runbook
+ acceptance tests, not the model internals.

---

## Target scaffold (FDE lens)

```
healthcare-forward-deployed-engineer/
├── docs/                       customer-facing deliverables (the FDE artifact)
│   ├── customer-brief.md
│   ├── solution-design.md
│   ├── deployment-plan.md
│   ├── runbook.md
│   └── handoff-guide.md
├── demo/                       walkthrough materials
│   ├── loom-script.md
│   └── sample-client-scenarios.md
├── integrations/               customer-system adapters
│   ├── ehr_adapter.py · fhir_transform.py · identity_mapper.py
│   ├── auth/oauth_client.py · service_account.py
│   └── sync_jobs.py
├── app/                        deployable service
│   ├── main.py
│   └── routers/{ask,status,admin}.py
├── workflows/                  the one job this deployment runs
│   ├── triage_assistant.py
│   └── fallback_logic.py
├── retrieval/                  BM25 only (no dense — customer-VPC dep minimization)
├── generation/                 grounded answer + citation validation
├── guardrails/                 input · output · pii (recycled from genai-engineer)
├── data/raw/                   shared 497-row enriched corpus
├── evaluation/                 customer success criteria (NOT ML metrics)
│   ├── acceptance_tests.py
│   └── eval_dataset.json
├── observability/              structured audit logging
│   └── logging.py
├── deployment/                 shippable unit
│   ├── Dockerfile · docker-compose.yml
│   ├── smoke_test.sh
│   └── env/dev.env · prod.env.example
├── postmortems/
│   └── integration_failure_example.md
├── tests/                      pytest FastAPI TestClient smoke
├── .github/workflows/acceptance.yml      CI: make test + make acceptance on PR
└── Makefile · requirements.txt · README · ROADMAP
```

---

## Phase status (phase = dependency order, NOT calendar)

```
☑️ Phase 1 — scaffold                                     commits 10f6164 → 8c181f9
   ☑ repo + README + ROADMAP + .gitignore + folder tree

☑️ Phase 2 — customer-facing docs                          commit ca3fd3d
   ☑ docs/customer-brief.md       business problem · constraints · success metrics
   ☑ docs/solution-design.md      end-to-end flow + component status
   ☑ docs/deployment-plan.md      12-phase rollout
   ☑ docs/runbook.md              alert ladder · escalation · safety floors
   ☑ docs/handoff-guide.md         ownership matrix + 90-day plan

☑️ Phase 3 — workflow (the one job)                        commit ca3fd3d (same)
   ☑ workflows/triage_assistant.py    rule-based ESI + retrieval + grounded
   ☑ workflows/fallback_logic.py       should_escalate + to_rules_fallback

☑️ Phase 4 — integrations (honest mocks)                   commit ca3fd3d (same)
   ☑ integrations/ehr_adapter.py      Epic-like FHIR endpoint stub
   ☑ integrations/fhir_transform.py   FHIR resource → canonical schema
   ☑ integrations/identity_mapper.py  MRN ↔ patient_id resolver
   ☑ integrations/auth/oauth_client.py + service_account.py
   ☑ integrations/sync_jobs.py        scheduled identity refresh + index warm

☑️ Phase 5 — FastAPI surface                                commit ca3fd3d (same)
   ☑ app/main.py + routers/{ask,status,admin}.py

☑️ Phase 6 — deployment unit                                commit ca3fd3d (same)
   ☑ deployment/Dockerfile           python:3.11-slim + HEALTHCHECK
   ☑ deployment/docker-compose.yml
   ☑ deployment/smoke_test.sh         5 curl checks
   ☑ deployment/env/dev.env + prod.env.example

☑️ Phase 7 — postmortem template + demo materials           commit ca3fd3d (same)
   ☑ postmortems/integration_failure_example.md
   ☑ demo/loom-script.md
   ☑ demo/sample-client-scenarios.md

☑️ Phase 8 — operational polish + CI                        commit bdda195 + pending
   ☑ .github/workflows/acceptance.yml — make test + make acceptance on PR
   ☑ README reframe (drop "presentation cut", lead with artifact)
   ☑ README "Built for" line + flow diagram + sample JSON
   ☑ README "How to think about this repo" Q&A table
   ☑ asciinema "Record your own demo" section
   ☑ ROADMAP updated to mark phases 2-8 done with commit hashes
```

---

## Why this order (FDE-specific)

```
WRONG ORDER                          RIGHT ORDER
─────────────────────────────────────────────────────────────────────
"impressive AI workflow"             customer brief + runbook FIRST
   ↓                                    ↓
"sure, but can you deploy it?"       "she walked into the hospital
                                        with the runbook ready"
```

The runbook + handoff guide are what distinguish FDE from a pure AI engineer.
The workflow is the easy part; the deployment-context wrapper is the role.

---

## Anti-overbuild reminders

- Recycle from monorepo. Do not rewrite.
- Honest mocks > fake "production" claims. Mark integrations as stubs explicitly.
- One workflow (triage). NOT multi-workflow / multi-tenant / multi-customer.
- Customer acceptance criteria > ML metrics in the foreground.
- BM25-only retrieval (no dense) — minimize customer-VPC dependency footprint.
- Phase order = dependency. No calendar implication.
