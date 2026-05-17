# Customer Brief — ER Triage Assistant Deployment

> **Stand-in customer:** mid-size US health system, ~400-bed flagship hospital + 3 community hospitals. Existing Epic EHR. Not naming names; this is a synthetic deployment scenario.

---

## Business problem

ER charge nurses triage ~280 patients per day across the flagship campus.
Current pain:

- 11% of patients wait > 90 minutes for first clinician contact
- 4% of those eventually get down-triaged (initial ESI 3 → final ESI 4),
  burning physician time on lower-acuity work while ESI 2 patients wait
- Charge nurses cannot search "similar past cases like this one" without
  digging through individual chart history

The customer wants an **AI-assisted triage assistant** that gives the charge
nurse a structured second opinion at the door:

1. classify ESI 1-5
2. surface 3-5 similar past cases with rationale
3. flag obvious escalation triggers (sepsis-shaped, pediatric < 1y,
   suicidal ideation, chest pain syndromes)
4. respect clinician override 100% of the time — assistant, not decision-maker

---

## Constraints

```
DATA           EHR is Epic. No direct DB access; must use FHIR/HL7 feeds.
               PHI must redact on ingest. 7-year audit retention.

INTEGRATION    SSO via SAML (Epic identity provider).
               Service deployed in customer VPC, NOT vendor-hosted SaaS.

AVAILABILITY   Triage doesn't stop. Target P95 latency 800ms door-to-suggestion.
               Graceful degradation to rules-based fallback when AI unavailable.

REGULATORY     HIPAA. State privacy law variations.
               Hospital legal already reviewed AI-assist scope (not autonomous).

CHANGE MGMT    14-day shadow mode before going live.
               Charge nurses train 2 hours on the UI.
               Daily override-rate review for first 30 days.
```

---

## Success metrics (customer-defined, not ML metrics)

```
PRIMARY
   median triage-to-first-clinician time     reduce by 15 min in 90 days
   down-triage rate (initial → final)        below 2% (current 4%)
   ESI 1-2 escalation page within 2 min      99%+

SECONDARY
   charge nurse satisfaction (NPS)            > 30 at day 60
   AI suggestion accepted by clinician        > 70% (rejection = signal,
                                                       not bug)
   override-rate < 30% per ESI tier           proxy for AI quality

SAFETY (non-negotiable)
   zero AI-initiated down-triage of pediatric < 1 y
   zero AI-initiated down-triage of suicidal ideation
   zero PHI leak in audit logs
```

---

## What this deployment is NOT

```
❌ Autonomous decisioning (assistant only, clinician retains authority)
❌ FDA-cleared diagnostic device
❌ Free-form chatbot for patients
❌ A replacement for ESI training
❌ A black box ("I cannot tell you WHY this case is ESI 2" = blocker)
```

---

## Phasing

```
WEEK 0-2    discovery + Epic connection setup + identity mapping
WEEK 2-4    shadow deployment (assistant runs, clinicians do NOT see it,
            we compare AI suggestion vs clinician decision daily)
WEEK 4-6    soft launch (assistant visible, one shift per day, daily review)
WEEK 6-12   full deployment + 30-day adjustment window
WEEK 12+    handoff to customer internal team + quarterly check-ins
```

Source-of-truth runbook: [`runbook.md`](runbook.md)  
Architecture: [`solution-design.md`](solution-design.md)  
Handoff: [`handoff-guide.md`](handoff-guide.md)  
Deployment plan: [`deployment-plan.md`](deployment-plan.md)
