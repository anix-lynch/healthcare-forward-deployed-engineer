# Sample Client Scenarios — interview / discovery rehearsal

Use these to walk a customer or interviewer through the assistant.
Each is a one-paragraph clinical scenario + the AI's expected response.

---

## Scenario 1 — High-risk chest pain

**Setup:** 62yo male walks into ER, ambulance bypass. Substernal chest
pressure 30 min, diaphoresis, radiates to jaw. Vitals: BP 95/60, HR 122,
SpO2 92.

**Expected AI response:**
- ESI 2 (emergent)
- escalate: true
- red flags: chest_pain, diaphoresis, hypotension, hypoxia, tachycardia
- similar cases: 3 prior chest-pain admissions with similar vitals
- human_review_required: true
- mode: ai_assist

---

## Scenario 2 — Pediatric safety floor

**Setup:** 8-month-old female brought by parent. High fever 39.8C,
lethargy, poor feeding for 6 hours.

**Expected AI response:**
- ESI 2 (pediatric < 1y safety floor — never down-triaged below 2)
- escalate: true
- red flags: pediatric_under_1y
- human_review_required: true
- mode: ai_assist

---

## Scenario 3 — Routine well-visit (anti-escalation)

**Setup:** 26yo female walks in for annual physical, asymptomatic, well
controlled chronic conditions.

**Expected AI response:**
- ESI 4 or 5 (well visit, no acuity)
- escalate: false
- red flags: []
- human_review_required: false (high-confidence non-urgent)
- mode: ai_assist

---

## Scenario 4 — Stale data fallback

**Setup:** Same as Scenario 1, but Epic FHIR feed is lagging 6 minutes
(P2 → P1 alert). On-call has flipped mode to stale_data_warning.

**Expected AI response:**
- Same ESI/escalation logic runs
- mode: stale_data_warning (overrides ai_assist)
- warnings: ["vitals may be 5+ min stale — clinician must verify manually"]
- Banner shown in charge nurse UI

---

## Scenario 5 — Outage / hard rules_fallback

**Setup:** Service is in rules_fallback mode (vector store unavailable,
LLM provider 5xx).

**Expected AI response:**
- ESI tier from rule-only scoring (no retrieval, no LLM)
- mode: rules_fallback
- rationale: "AI assistant unavailable — rules-based ESI suggestion"
- warnings: ["assistant in fallback mode — clinician must verify"]
- Banner shown in UI

---

## Interview pivot lines

When asked **"how does the AI work?"** →
*"At a high level: retrieve similar past cases by BM25, classify ESI with
rules, generate a grounded rationale that cites the retrieved source_ids.
But the FDE story is how this sits inside the customer's hospital, not
the retrieval algorithm itself. The runbook, the postmortems, the
acceptance tests are where the role lives."*

When asked **"what happens when it breaks?"** →
*"That's the most important question. Let me walk you through
runbook.md."*

When asked **"how would you deploy this to a different customer?"** →
*"Customer-brief.md becomes the contract. Solution-design.md becomes the
architecture review. Phase 0 discovery + Phase 1 connection move at the
customer's IT speed. By Phase 2 we're shadow-running. Walk through
deployment-plan.md."*
