# Runbook — On-Call Operations

> Day-to-day operational playbook for the ER triage assistant deployment.
> If you only read one doc when paged, read this one.

---

## Alert ladder

```
SEVERITY        TRIGGER                                  PAGING WINDOW
─────────────────────────────────────────────────────────────────────
P0  outage     /health returns 5xx for > 60s             page on-call FDE immediately
                                                          + customer IT lead
P0  safety    pediatric < 1y down-triaged by assistant   page customer safety officer
                                                          + customer CMO + FDE
P1  drift     accept-rate by clinician < 50% rolling 1h  page on-call FDE within 15m
P1  perf      P95 latency > 1.5s rolling 5m              page on-call FDE within 30m
P2  upstream  Epic FHIR feed lag > 5m                    log + email · review next morning
P2  data      checkpoint.py exits 1 on nightly run       log + email · review same day
P3  capacity  vector_store size growing > 10% per week    log only · monthly review
```

---

## P0 — service outage

```
1. Confirm scope: customer-side only? our service down?
   curl https://<customer-vpc>/triage-assistant/health
   → if 5xx: it's us. If timeout: network/customer-side.

2. Fall back to rules-based mode (charge nurses keep working):
   curl -X POST https://<host>/admin/mode \
     -H "Authorization: Bearer $ADMIN_BEARER_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"mode": "rules_fallback"}'
   → assistant still surfaces ESI suggestion via deterministic rules
   → token is in customer secret manager; on-call FDE has it via pager handoff

3. Page customer IT lead. Confirm they see the same.

4. Restart loop:
   docker-compose -f deployment/docker-compose.yml restart
   → wait 60s, re-curl /health
   → if still bad: check logs in observability/, escalate to backend lead

5. Post-restoration: write a postmortem at postmortems/<date>-outage.md
   Include: timeline · root cause · customer impact · fix · prevention
```

---

## P0 — safety: pediatric < 1y down-triage

```
ZERO TOLERANCE. The assistant must never down-triage pediatric < 1y.
If this fires:

1. Immediately disable assistant:
   curl -X POST https://<host>/admin/mode \
     -H "Authorization: Bearer $ADMIN_BEARER_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"mode": "off"}'
   Charge nurses see "AI assistant unavailable" banner.

2. Page customer safety officer + CMO within 5 minutes.

3. Pull the exact request: grep observability/logs for the case_id.
   Save full audit trail to postmortems/<date>-pediatric-safety.md.

4. Do NOT re-enable until:
   a) root cause identified
   b) test case added to evaluation/acceptance_tests.py
   c) customer safety officer signs off

5. Mandatory state report: was anyone harmed? If yes, follow customer's
   adverse-event protocol.
```

---

## P1 — drift: clinician accept-rate dropping

```
TRIGGER: accept-rate (clinician chose AI suggestion) < 50% over 1h

This usually means the AI is suggesting wrong tiers consistently.

1. Pull the last hour's traces:
   python observability/audit_report.py --hours 1

2. Group by ESI tier suggested. Where's the disagreement?
   - if mostly ESI 3 → ESI 2 promotions: AI over-cautious. Often OK.
   - if mostly ESI 2 → ESI 3 demotions: AI under-cautious. SAFETY CONCERN.
   - if uniform: model degradation or data drift.

3. Check upstream:
   - Epic FHIR feed lag > 5m? (vitals stale)
   - patient_identity_map.json refresh stale > 24h?
   - holdout eval regression gate firing?

4. If under-cautious: switch to rules_fallback per P0 step 2 + page.
   If over-cautious: notify + monitor, no immediate action.
```

---

## P2 — upstream: Epic FHIR feed lag

```
Symptom: integrations/sync_jobs.py last_success_ts > 5 minutes ago.

1. Check Epic connector status (customer IT dashboard).
2. Manually trigger one sync: python integrations/sync_jobs.py --force
3. If still lagging: open ticket with customer IT, downgrade assistant
   to "stale data" banner mode:
   curl -X POST https://<host>/admin/mode \
     -H "Authorization: Bearer $ADMIN_BEARER_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"mode": "stale_data_warning"}'
```

---

## Daily ops checklist

```
☐ 06:00   review overnight checkpoint.py report (data quality gate)
☐ 06:15   review observability accept-rate by ESI tier (rolling 24h)
☐ 06:30   verify Epic FHIR feed lag < 60s
☐ 12:00   spot-check 5 random triage decisions vs clinician final
☐ 18:00   review any P1+ alerts from previous 12h
☐ 22:00   confirm tomorrow's on-call rota
```

---

## Escalation contacts

```
ROLE                  CONTACT                            WHEN
─────────────────────────────────────────────────────────────────────
on-call FDE            <fde-pager>                       all P0/P1
customer IT lead       <customer-it-lead>                P0 outage
customer safety officer<customer-safety-officer>          P0 safety
customer CMO           <customer-cmo>                     P0 safety
backend lead           <backend-lead>                     P0 escalation
legal counsel          <customer-counsel>                 PHI leak, adverse event
```

(Real contact info populated per customer at handoff time.)

---

## Log volumes & PHI

```
SINK                            CONTENT                       ACCESS
─────────────────────────────────────────────────────────────────────
outputs/audit.jsonl             metadata only                 standard
  + stdout mirror                 esi_tier, confidence, mode,    cloud
                                  latency_ms, red_flag_count,    logging
                                  citation_count, tier_bucket    OK to index
                                NO rationale, NO snippets

outputs/phi_archive.jsonl       full triage payload            RESTRICTED
  (NO stdout)                     rationale + similar_cases    volume +
                                  snippets — these ARE         access audit
                                  past-patient text             + 7-yr retention
                                                                (HIPAA Safe Harbor)
```

Production wiring:
- audit.jsonl → Cloud Logging / App Insights / CloudWatch (indexed, queryable, 30-90d).
- phi_archive.jsonl → restricted-ACL volume; mount read-only for the on-call
  CLI; access events themselves audited via cloud KMS or equivalent.
- stdout (container logs) → goes to the cloud log sink but ONLY carries
  metadata, never PHI.

On-call drill-down with PHI access:
```
python observability/audit_report.py --case-id <id> --include-phi
```
Prints a stderr warning when --include-phi fires (access should leave a trail
in the on-call ticket; quote the ticket id when invoking).

---

## Sample postmortem template

Located at: [`../postmortems/integration_failure_example.md`](../postmortems/integration_failure_example.md)
