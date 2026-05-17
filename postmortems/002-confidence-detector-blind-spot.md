# Postmortem #002 — Confidence-Detector Blind Spot (Brief↔Code Drift)

> **Status:**   AUDIT FINDING — NOT a production incident.
> **Date:**     2026-05-17
> **Severity:** P1 (latent — would have been P0 had it shipped to production)
> **Author:**   on-call FDE (proactive brief↔code drift audit)
> **Reviewed by:** vendor lead + customer safety officer (mock sign-off)

---

## TL;DR

A pre-Cowork hiring-scorecard audit of `workflows/triage_assistant.py` revealed
that the `confidence` value returned to the charge nurse was a CONSTANT — 0.85
when any red flag fired, 0.65 otherwise. The downstream `fallback_logic.should_escalate`
function checked `if confidence < 0.5`, which could NEVER fire. The "low-confidence
hand-off to human" path advertised in `customer-brief.md` SAFETY section and the
P1-drift alert ladder in `runbook.md` L18 was effectively dead code.

No patient harm — the bug was caught during a proactive audit, not in
production. Fixed and shipped before any customer integration.

---

## Timeline (UTC)

```
12:01   pre-Cowork audit reads workflows/triage_assistant.py L75:
            confidence = 0.85 if red_flags else 0.65
        → notes confidence is constant in {0.85, 0.65}
12:02   audit reads workflows/fallback_logic.py L23:
            if confidence < 0.5: return True
        → notes: 0.5 threshold can NEVER fire with constant confidence
12:04   audit confirms runbook.md L18 P1-drift entry depends on
        clinician-vs-AI accept-rate, which depends on AI fallback
        firing on low-confidence cases
12:05   classify as brief↔code drift bug, severity P1 latent
12:09   patch authored: _compute_confidence(*, hits, red_flags, vitals)
        with evidence-weighted formula, range [0.0, 0.95]
12:09   acceptance test ACC-009 added (fails-by-design if formula
        regresses to constant)
12:10   commit 5c7b6f9 — `sec(fde): close 3 P0 hardening gaps...`
        Tests: 7/7 unit + 9/9 acceptance · 0 regressions
12:11   CI green
```

Total: discovery → patch → green CI in ~10 minutes.

---

## Root cause

The confidence value was originally added as a UI display field — "show 85%
when the AI is confident, 65% otherwise." That made sense in isolation.

Later, the fallback path (`should_escalate(esi, confidence, red_flags)`) was
added with a `confidence < 0.5` threshold, copying the pattern from a
reference implementation that returned a properly-weighted score from the
retrieval+vitals signal.

NEITHER author realized the upstream confidence was still the original
constant — the contract LOOKED right (a `float` between 0 and 1), but the
semantics had drifted: one side treated it as a calibrated probability, the
other as a flag.

This is the classic **brief↔code drift** failure mode:
- the customer brief promises behavior X (drift detection via low-confidence escalation)
- the code has a function shaped like X
- the function never actually fires because an upstream constant blocks it
- nobody runs an end-to-end test of the dead branch because nobody thinks
  to test "does the function fire at all"

---

## What worked

- The audit pass that caught this was a SCHEDULED activity — Cowork's
  hiring-scorecard pass treats brief↔code drift as a P0 review dimension.
  The audit found the bug because the audit was structured to look for it.
- The fix shipped as ONE commit with a unit test that fails-by-design
  if the formula regresses. The next person who tries to "simplify"
  `_compute_confidence` back to a constant will see ACC-009 break in CI.
- The acceptance test suite already had a discipline of testing customer-
  contract behaviors, NOT ML metrics. Adding ACC-009 fit the existing
  pattern (each test maps to an `evaluation/eval_dataset.json` criterion
  with a named owner).

---

## What didn't work

- The original code review of the fallback_logic.py PR didn't catch this.
  The reviewer saw "confidence < 0.5 → escalate" and read it as a
  reasonable threshold, without tracing back to confirm confidence
  could actually reach that range.
- No previous acceptance test exercised the dead branch. The test suite
  covered the HAPPY path (escalation fires when ESI=1 or pediatric)
  but not the LOW-CONFIDENCE path. Coverage was a lie because the
  branch couldn't fire.
- The internal "latency_ms" was being honestly measured but
  confidence wasn't — different reliability standards for adjacent
  metrics in the same response payload.

---

## Corrective actions

```
ACTION                                                  OWNER       STATUS
─────────────────────────────────────────────────────────────────────────────
[1] Replace constant confidence with                    vendor      ✅ shipped
    _compute_confidence(hits, red_flags, vitals)        FDE         commit 5c7b6f9
    Formula: 0.30 base + retrieval + flags + vitals,
             clamp [0.0, 0.95]
[2] Add ACC-009 acceptance test:                        vendor      ✅ shipped
    _compute_confidence([], [], None) < 0.5             FDE         commit 5c7b6f9
    fails-by-design if formula regresses
[3] Update fallback_logic.should_escalate docstring     vendor      ✅ shipped
    to document the confidence band table               FDE         commit 2d27dae
[4] Add this postmortem to the running record           vendor      ✅ this file
    (so future contributors see the failure mode)       FDE
[5] Quarterly brief↔code drift audit                    vendor +    NEW PROCESS
    Every quarter, cross-reference every "MUST" in       customer    every 90d
    customer-brief.md against a passing acceptance       safety
    test. Gap = ticket.                                   officer
```

---

## Customer impact assessment

```
Patient impact:              NONE (caught pre-production, no live deployment)
SLO impact:                   NONE
Audit log impact:             NONE
Legal review needed:          NO (no PHI, no autonomous decisions)
Trust impact (CMO debrief):   NEUTRAL+ — surfacing the bug in a postmortem
                              BEFORE production strengthens trust ("we audit
                              our own work, we ship the fix with a test that
                              prevents the regression")
```

---

## Why ship this as a postmortem

A real customer would ask: "what's your QA story?" The honest answer is
"we run brief↔code drift audits and write up what we find, even when no
patient was harmed — same template, real receipts." This file is that answer.

The corrective action `[5] Quarterly brief↔code drift audit` becomes a
**new operational practice** the vendor commits to. That's the FDE
deliverable shape: turn an audit finding into a sustained QA habit, not
just a one-off patch.

---

## Use this template for real (and proactive) audits

Same structure as `001-integration-failure-example.md`:
1. TL;DR (3 sentences)
2. Timeline (UTC, granular)
3. Root cause (one paragraph)
4. What worked / What didn't (bulleted)
5. Corrective actions (table with owner + status)
6. Customer impact assessment

Both reactive incidents AND proactive audit findings should land here.
The discipline is the same; the trigger is different.

Sign-off: vendor FDE + customer safety officer when patient-facing.
