# Handoff Guide — Transitioning Ownership to Customer Team

> What the customer's internal team owns after the FDE engagement ends.
> Aim: customer can run + iterate on this system without us.

---

## Ownership matrix

```
SURFACE                              FDE (during engagement)       CUSTOMER (after handoff)
─────────────────────────────────────────────────────────────────────────────────────────
Triage assistant service             build + deploy                operate + monitor
EHR integrations                      build + first config          maintain + reconnect on Epic upgrades
Identity mapper                       build                          run nightly
Guardrails (input + output + PII)    build + initial config        operate + update PII patterns as needed
Workflows (triage + fallback)        build + tune                  iterate on tier rules
Eval harness                         build + baseline               run weekly + investigate regressions
Observability + logging              build                          read + alert
Deployment (docker-compose / cloud)  build + first deploy           manage env vars + restart cycles
Runbook                              author                         follow + update from learnings
Postmortems                          author first one              author all subsequent
Acceptance tests                     define with customer           run + extend
```

---

## What the customer needs to know

### 1. Where the code lives

```
this repo                            implementation
docs/runbook.md                       day-to-day ops
docs/customer-brief.md                business framing
docs/solution-design.md               architecture
docs/deployment-plan.md               rollout phases
postmortems/                          incident learnings
```

### 2. How to run

```
# Local dev
make install
make serve        # uvicorn on :8000
make demo         # one sample triage decision

# Production-shaped (docker-compose)
make docker-up
make docker-down
make smoke         # post-deploy sanity (deployment/smoke_test.sh)

# Customer acceptance gate
make test          # pytest tests/ — FastAPI surface smoke
make acceptance    # pytest evaluation/acceptance_tests.py
                   # — the CONTRACT tests (safety + perf + schema).
                   # A failure blocks merge per .github/workflows/acceptance.yml.
```

### 3. How to deploy a change

```
1. branch + commit + PR
2. CI runs `make test` + `make acceptance`
3. CI blocks merge on any acceptance failure
4. merge → CD pipeline → shadow mode for 24h → live
5. monitor accept-rate + override-rate for 7 days
```

### 4. How to add an acceptance test

When a new failure mode shows up in production, add it to
`evaluation/acceptance_tests.py` so the regression gate catches it next time.

```python
def test_pediatric_under_1_never_downtriaged():
    """Added 2026-XX-YY after incident #003."""
    case = {...}
    out = client.post("/v1/ask", json=case).json()
    assert out["esi_tier"] <= 2, "pediatric < 1y must never be down-triaged"
```

---

## Risk transfer notes

After handoff, the customer is operationally responsible for:

```
- HIPAA compliance of the deployed service
- 7-year audit retention infra (we recommend Cloud Logging / App Insights /
  CloudWatch sink — customer picks per their cloud)
- Adverse event reporting per state law
- Quarterly red-team review (eval/eval_dataset.json is the starter set)
- Annual penetration test
```

We remain available for:
```
- Quarterly check-ins (architectural advice, NOT operational ownership)
- Emergency support during the first 60 days post-handoff (paid retainer)
- New deployment to another campus (separate engagement)
```

---

## First 90 days post-handoff — recommended customer milestones

```
DAY 0      handoff meeting · runbook walkthrough · contact list confirmed
DAY 7      customer runs first eval cycle solo
DAY 14     customer authors first postmortem solo (any P1+ event)
DAY 30     customer-initiated retraining cycle (if drift seen)
DAY 60     customer extends eval golden set with their own learnings
DAY 90     architectural review · scope renegotiation for new lanes
```
