# Roadmap — Incremental Population from Monorepo

Source of truth: [`healthcare-genai-fullstack`](https://github.com/anix-lynch/healthcare-genai-fullstack).  
This file tracks what lands in this presentation cut, in small steps.

> **Note:** this scaffold is intentionally lighter in Phase 1 than the GenAI Engineer and AI Data Engineer cuts. It populates after those two are in place.

---

## Target scaffold (Forward Deployed Engineer lens)

```
healthcare-forward-deployed-engineer/
├── docs/
│   ├── customer-brief.md          # business problem · constraints · success
│   ├── solution-design.md
│   ├── deployment-plan.md
│   ├── runbook.md
│   └── handoff-guide.md
├── demo/
│   ├── loom-script.md
│   └── sample-client-scenarios.md
├── integrations/
│   ├── ehr_adapter.py
│   ├── identity_mapper.py
│   ├── fhir_transform.py
│   ├── auth/
│   │   ├── oauth_client.py
│   │   └── service_account.py
│   └── sync_jobs.py
├── app/
│   ├── main.py
│   └── routers/
├── workflows/
│   ├── triage_assistant.py
│   └── fallback_logic.py
├── evaluation/
│   ├── acceptance_tests.py
│   └── eval_dataset.json
├── observability/
│   └── logging.py
├── deployment/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── smoke_test.sh
├── tests/
└── postmortems/
    └── integration_failure_example.md
```

---

## Phase status

- [x] **Phase 1:** repo + README + ROADMAP + minimal folder tree
- [ ] **Phase 2:** docs/ — write customer-brief / solution-design / runbook (reframe from monorepo `docs/05_patient_lifecycle.md` + `docs/failure_modes.md`)
- [ ] **Phase 3:** workflows/triage_assistant.py — reframe `apps/er-triage/` into workflow form
- [ ] **Phase 4:** integrations/ — small adapter stubs (EHR mock + FHIR transform + auth)
- [ ] **Phase 5:** app/main.py — copy FastAPI surface from monorepo `services/rag-api/`
- [ ] **Phase 6:** deployment/ — Dockerfile + smoke_test.sh
- [ ] **Phase 7:** postmortems/ — one example reframed from `outputs/failure_demos.json`

Each phase = one commit. No phase invents new architecture.

---

## Anti-overbuild reminders

- Recycle from monorepo. Do not rewrite.
- Customer-deployment framing throughout. NOT "model internals" framing.
- Runbook over README polish. Customer brief over architecture diagram.
- One use case, one customer, one workflow. NOT all 7 patterns.
