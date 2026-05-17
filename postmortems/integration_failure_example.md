# Postmortem #001 — Example: Epic FHIR Feed Lag → Triage Suggestions on Stale Vitals

> **Status:** EXAMPLE / TEMPLATE. Use this shape for real incidents.
> **Date:** 2026-XX-XX
> **Severity:** P1
> **Author:** on-call FDE
> **Reviewed by:** customer IT lead + customer ED director

---

## TL;DR

For ~47 minutes on 2026-XX-XX, the triage assistant was making ESI
suggestions based on vitals that were 5–7 minutes stale. No safety
incidents resulted, but the AI accept-rate dropped from 71% to 38%
during the window, indicating clinicians correctly distrusted the
suggestions while the underlying feed was lagging.

---

## Timeline (UTC)

```
14:02   Epic FHIR feed begins lagging (5+ min behind real time)
14:09   integrations/sync_jobs.py last_success_ts > 5 min — P2 alert fires
14:11   on-call FDE acks the P2, opens ticket with customer IT
14:18   P1 alert fires: clinician accept-rate < 50% rolling 1h
14:21   on-call FDE switches to stale_data_warning mode
        POST /admin/mode {"mode": "stale_data_warning"}
        Charge nurses see banner: "Vitals may be stale — verify manually"
14:34   customer IT confirms Epic-side reverse proxy was OOM'd
14:41   Epic-side restart complete, FHIR feed catches up
14:48   sync_jobs.py last_success_ts < 60s — feed healthy
14:49   on-call FDE flips back to ai_assist mode
        POST /admin/mode {"mode": "ai_assist"}
14:51   accept-rate recovers to 68% rolling 15-min
```

Total degraded window: 47 minutes
Total stale-data window: 39 minutes (after banner went up)

---

## Root cause

Epic's reverse proxy in the customer's VPC ran out of memory due to a config
change earlier in the day (heap size lowered from 4G to 2G to free RAM for
another service). When traffic hit normal peak, the proxy OOM-killed and
restarted on a loop. Each restart took ~6 min for the FHIR queue to drain.

This was a customer-side change with no notification to FDE.

---

## What worked

- Two-stage alert ladder (P2 at 5 min lag, P1 at accept-rate drop) caught
  the issue WITHOUT a P0 outage
- stale_data_warning mode let clinicians keep working with awareness
- No safety incidents — the banner did its job

---

## What didn't work

- **47 min** is too long for "no notification of customer infra changes."
  Customer IT should have given FDE a heads-up on the heap-size change.
- The accept-rate alert was reactive (triggered AFTER 1h of degraded data).
  We should detect upstream lag and proactively warn, not wait for
  downstream symptoms.
- The `stale_data_warning` mode banner text was generic — clinicians
  didn't know the lag was on the Epic side, so some assumed our service
  was broken.

---

## Corrective actions

```
ACTION                                                  OWNER       ETA
─────────────────────────────────────────────────────────────────────
[1] Customer IT to add FDE to infra-change Slack channel  CIO         this week
[2] Upgrade P2 → P1 if feed lag exceeds 8 min             FDE         next sprint
[3] Banner text shows source-system name when known       FDE         next sprint
[4] Add eval acceptance test for stale-data scenario     FDE         next sprint
[5] Document this in runbook.md alert ladder              FDE         done in this commit
```

---

## Customer impact assessment

```
Patient impact:         NONE (banner shown, no decisions made on stale data without
                                clinician override)
Override-rate impact:   transient drop in AI accept-rate; recovered fully in 15 min
Audit log impact:       47 audit rows tagged `mode=stale_data_warning`
Legal review needed:    NO (no PHI exposure, no autonomous decisions)
```

---

## Use this template for real incidents

Copy this file structure:
1. TL;DR (3 sentences max)
2. Timeline (UTC, granular)
3. Root cause (one paragraph)
4. What worked / What didn't (bulleted)
5. Corrective actions (table with owner + ETA)
6. Customer impact assessment

Sign off with: on-call FDE + customer counterpart.
