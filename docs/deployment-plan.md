# Deployment Plan — Phased Rollout

> 12-week rollout from contract signing to full live deployment.
> Designed for low-blast-radius and clinician trust-building.

---

## Phases

```
PHASE              WEEKS    GOAL                                BLAST RADIUS
─────────────────────────────────────────────────────────────────────────────
0  Discovery      0–2       understand workflows + Epic schema    ZERO (read-only)
1  Connection    2–4       Epic FHIR feed + identity map         ZERO (no patient impact)
2  Shadow        4–6       AI runs · clinicians don't see        ZERO (comparison only)
3  Soft launch   6–8       AI visible · 1 shift/day · daily review  LOW (1 shift, supervised)
4  Pilot        8–10       AI on all shifts · daily review        MEDIUM (full ER, monitored)
5  Full         10–12      All campuses · weekly review            FULL
6  Handoff       12+       customer team owns ops                  N/A
```

---

## Phase 0 — Discovery (week 0–2)

```
GOAL    understand customer workflows, data realities, constraints
TASKS   - 3 shadow shifts with charge nurses (no laptop, just watch)
        - interview ED medical director · ED ops director · IT
        - audit Epic FHIR endpoints we can use
        - audit identity mapping options (MRN vs Epic patient_id)
        - review hospital's AI-assist policy + legal review status
OUTPUT  - customer-brief.md (this folder)
        - one-page risk register
        - GO/NO-GO for Phase 1
ROLLBACK n/a (no code shipped)
```

## Phase 1 — Connection (week 2–4)

```
GOAL    EHR feed + identity mapper running in customer VPC, no live use
TASKS   - integrations/ehr_adapter.py wires to real Epic FHIR endpoint
        - integrations/fhir_transform.py normalizes to canonical schema
        - integrations/identity_mapper.py builds first MRN ↔ patient_id map
        - integrations/sync_jobs.py runs every 15 min
        - observability/logging.py captures every transformation
OUTPUT  - data flow visible in observability dashboard
        - identity map populated with ≥ 30 days of historical encounters
ROLLBACK kill sync_jobs cron → data stops moving (no patient impact)
```

## Phase 2 — Shadow (week 4–6)

```
GOAL    AI runs on every triage. Clinicians do not see the suggestion.
        Daily review: AI suggestion vs clinician decision.
TASKS   - workflows/triage_assistant.py runs on every intake
        - app/routers/ask receives every door entry
        - outputs logged for comparison, NOT shown to clinicians
        - daily 30-min review meeting: customer ED director + FDE
        - accept-rate proxy computed: AI ESI vs final clinician ESI
        - failures get postmortems
EXIT    - 14 days run
        - AI-vs-clinician agreement ≥ 75% on ESI 1-2
        - zero pediatric < 1y down-triages
        - zero suicidal ideation down-triages
ROLLBACK POST /admin/mode {"mode": "off"} → AI stops running (no patient impact, never shown)
```

## Phase 3 — Soft launch (week 6–8)

```
GOAL    AI suggestion visible to one charge nurse per day shift, supervised.
TASKS   - UI shows AI suggestion next to clinician input
        - clinician can accept / reject / override
        - daily review continues
        - charge nurses trained 2h on the UI
        - one assigned ED attending available for "AI says X, what do I do" questions
EXIT    - 14 days run
        - clinician accept-rate ≥ 60% (proxy for usefulness)
        - zero P0 safety incidents
ROLLBACK POST /admin/mode {"mode": "off"} → banner: "AI temporarily unavailable"
```

## Phase 4 — Pilot (week 8–10)

```
GOAL    AI on all shifts at flagship campus, daily review continues
TASKS   - 24/7 coverage
        - on-call FDE on pager
        - daily morning review → weekly review by Phase 4 end
EXIT    - 14 days run
        - accept-rate stable ≥ 60%
        - down-triage rate ≤ 3% (from 4% baseline)
        - zero P0 safety incidents
ROLLBACK Same as Phase 3
```

## Phase 5 — Full deployment (week 10–12)

```
GOAL    All 4 campuses (1 flagship + 3 community)
TASKS   - rollout one community campus per week
        - per-campus shadow mode for 3 days before live
        - shared on-call between FDE + customer IT
EXIT    - all 4 campuses live ≥ 7 days
        - global accept-rate ≥ 60%
        - global down-triage rate ≤ 2%
        - regression gate green for 14 consecutive days
ROLLBACK per-campus shutoff: POST /admin/mode/{campus_id} {"mode": "off"}
```

## Phase 6 — Handoff (week 12+)

```
GOAL    customer internal team operates without FDE day-to-day
TASKS   - handoff meeting per [handoff-guide.md](handoff-guide.md)
        - customer runs eval cycle solo
        - customer authors first postmortem solo (any P1+ event)
DURATION 60 days FDE on retainer for emergency support
THEN    quarterly check-ins only
```

---

## Cross-references

- Risk register: [`runbook.md`](runbook.md) (alert ladder section)
- Handoff: [`handoff-guide.md`](handoff-guide.md)
- Customer brief: [`customer-brief.md`](customer-brief.md)
