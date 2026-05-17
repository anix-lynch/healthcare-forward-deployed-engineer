# Loom Walkthrough Script — 5 minutes

> Script for recording a 5-minute walkthrough of the FDE-style deployment.
> Use OBS / Loom. Keep camera off; just terminal + browser + voice.

---

## Opening (30 sec)

> "This is the customer-deployment cut of a healthcare triage assistant.
> The architecture is a Forward Deployed Engineer's view: not just the
> AI internals, but every piece a customer needs to actually deploy this
> into a hospital VPC. The point is to show how the AI sits inside a real
> system — auth, integration, runbook, postmortems — not just the model."

Show: top-level repo tree.

---

## Customer brief (45 sec)

> "Customer is a mid-size health system. ER triage takes too long, 4% of
> patients get down-triaged after waiting. They want an assistant that
> gives the charge nurse a structured second opinion at the door."

Show: docs/customer-brief.md — scroll to the constraints + success metrics.

> "Constraints are realistic: Epic EHR, customer VPC deployment (not SaaS),
> HIPAA, 14-day shadow mode before going live. Success metrics are
> customer-defined, not ML metrics."

---

## Architecture (1 min)

Show: docs/solution-design.md ASCII flow diagram.

> "One patient at the door triggers this flow: EHR adapter pulls intake,
> FHIR transform normalizes, identity mapper resolves patient_id,
> guardrails sanitize, the workflow runs, output guardrails validate,
> the response goes back to the nurse, and observability logs an audit row."

> "Honest scope: integrations are mocks. The real engagement would wire
> them to live Epic. Everything else is real working code."

---

## Live demo (90 sec)

Terminal:

```bash
make docker-up
sleep 5
./deployment/smoke_test.sh
```

> "Container is up. Smoke test verifies health, status, valid /ask, the
> empty-CC blocker, and the admin mode switch."

> "All five checks pass."

Then a curl /v1/ask with a real case:

```bash
curl -X POST http://localhost:8000/v1/ask \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "DEMO-001",
    "chief_complaint": "chest pain with sweating",
    "hpi": "62yo M substernal pressure with diaphoresis, jaw radiation",
    "age": 62,
    "gender": "male",
    "vitals": {"bp_sys": 95, "hr": 122, "spo2": 92}
  }' | jq
```

> "Response: ESI 2, escalate true, four red flags (chest_pain, diaphoresis,
> hypotension, hypoxia, tachycardia), rationale grounded in three similar
> past cases. Latency under 100ms."

---

## Ops surface (45 sec)

Show: docs/runbook.md alert ladder section.

> "Day-to-day ops are documented. P0/P1/P2 alerts with paging windows.
> Most importantly, the safety floor: pediatric < 1y and suicidal ideation
> NEVER get down-triaged by the assistant."

Terminal:

```bash
curl -X POST http://localhost:8000/admin/mode \
  -H "Content-Type: application/json" \
  -d '{"mode": "rules_fallback"}'
```

> "And on-call can flip the assistant into rules_fallback mode without
> restarting the service. Charge nurses get the banner immediately."

---

## Postmortems + handoff (30 sec)

Show: postmortems/integration_failure_example.md and docs/handoff-guide.md.

> "Every incident gets a postmortem. There's a worked example showing the
> shape. And the handoff guide details what customer team owns post-engagement —
> the goal is they don't need us for day-to-day."

---

## Close (30 sec)

> "Summary: this is a Forward Deployed Engineer's deployment package.
> Working AI inside a customer-context envelope. Integrations are mocked
> for demo. The runbook, the acceptance tests, and the postmortems are
> the differentiators — they show the FDE knows what shape these pieces
> have, not just the model internals."

> "Repo link is in the description. Thanks for watching."

---

## Total run length target: 5:00–5:30

Practice once before recording. Don't edit; one take.
