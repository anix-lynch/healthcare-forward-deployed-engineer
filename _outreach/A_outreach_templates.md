# A — Outreach Templates (Forward Deployed Engineer, AI vendor / health-tech)

> Hook stack (in order of strength):
> 1. **Postmortem #002 — brief↔code drift caught in my own audit** ← rarest signal (most candidates can't audit themselves)
> 2. **Owner-mapped acceptance tests (safety_officer / CMO / IT_lead)** ← second rarest (real customer-shape, not ML metrics)
> 3. **Phased rollout w/ per-phase blast radius + rollback** ← solid FDE signal (deployment-plan.md)
> 4. **Runbook w/ P0/P1/P2 alert ladder + safety floors + admin mode flip** ← table stakes for senior, but most candidates skip
> 5. **PHI-aware split-sink audit log (metadata sink + restricted PHI archive)** ← health-tech moat
> 6. **FHIR transform w/ LOINC vitals map** ← domain proof for health-tech roles
> 7. **Healthcare domain** ← moat for health-tech FDE / liability for generalist FDE (skip mention if target is Palantir/Databricks/non-health)
>
> Always lead with #1 or #2. Everyone has a repo. Nobody has a postmortem of their own code shipped before the customer saw it.

---

## 1. Cold email — hiring manager (NOT recruiter)

**Subject:** FDE w/ runbook + own-bug postmortem receipts — for `<TEAM/COMPANY>`

```
Hi <Name>,

Saw <Company> is building <specific product / role / public post>.
I'm an FDE-shaped engineer focused on the deliverable shape most
candidates skip — customer brief → runbook → acceptance tests with
named owners → postmortem template — not just the model.

Built a healthcare ER triage deployment package that:
  • ships a 12-week phased rollout w/ per-phase blast radius +
    rollback, including 14-day shadow mode before any live traffic
  • runs 8 acceptance tests mapped to customer roles
    (safety_officer / CMO / IT lead) — contract tests, not ML metrics
  • split-sink audit log: metadata sink for cloud index,
    restricted PHI archive (7-yr retention) — no PHI in stdout
  • includes Postmortem #002 of a brief↔code drift bug I found in
    my OWN repo via pre-deployment audit (P1 latent, fixed before
    customer saw it) — that's the FDE pitch with receipts

Repo + worked postmortem:
  https://github.com/anix-lynch/healthcare-forward-deployed-engineer

Worth a 20-min chat about your <field engineering / deployment /
customer-engagement> setup?

— Anix
```

**Length:** 7 sentences. Under 150 words. The own-bug postmortem is the line that separates this from every other "I built a demo" pitch.

**Personalization slots** (mandatory — 2 min of LinkedIn skim per target):
- `<specific product / role / public post>` ← something that signals you actually looked
- swap bullets to match what their JD/blog emphasizes (drop healthcare for non-health shops)
- end with `<field engineering / deployment / customer-engagement>` matched to their team name

---

## 2. LinkedIn DM — short (under 300 char, mobile-friendly)

```
Hey <Name> — saw <Company> is hiring an FDE. I build the deliverable
shape most candidates skip: customer brief → phased rollout → owner-
mapped acceptance tests → postmortem of my own bug caught pre-prod.
Repo: github.com/anix-lynch/healthcare-forward-deployed-engineer

Open to a 20-min chat?
```

**Where to send:** hiring manager OR an FDE/field-eng IC on the team (NOT the recruiter — they filter on keywords, FDE hiring managers filter on "would this person survive Week 2 at a customer site").

---

## 3. LinkedIn DM — longer (when you've engaged with their content first)

```
Hi <Name>,

Your post on <topic — deployment, customer trust, healthcare AI,
brownfield integration, whatever> last week resonated — specifically
your point about <specific angle they raised>.

Quick context: <Company> is one of ~12 FDE-shaped roles I'm targeting
in 2026 because you all seem to care about <the customer envelope
around the AI, not just the AI itself / regulated-industry deployment /
field engineering as a craft — pick the one that's true>.

I just shipped a healthcare ER triage deployment package that I think
shows the kind of thinking you'd value:
  - customer-brief.md → solution-design.md → deployment-plan.md
    (12-week phased rollout, per-phase blast radius + rollback)
  - acceptance_tests.py: 8 contract tests w/ named customer-role
    owners (safety_officer / CMO / IT lead) — NOT ML metrics
  - runbook.md w/ P0/P1/P2 alert ladder + safety floors
    (pediatric < 1y, suicidal ideation = zero tolerance)
  - PHI-aware split-sink audit logging (metadata + restricted PHI)
  - Postmortem #002: I audited my own repo pre-submission, found a
    brief↔code drift bug (confidence dead-code), wrote it up using
    the same template I'd use for a real customer incident.
    That's the FDE pitch with receipts.

→ https://github.com/anix-lynch/healthcare-forward-deployed-engineer

Would a 20-min chat about <their team / their customer base / their
deployment cadence> make sense? Happy to dig into the postmortem
methodology specifically — that's where the FDE skill lives, not in
the model internals.

— Anix
```

**Use when:** you've liked/commented on 2-3 of their posts in the prior week. Don't send cold.

---

## 4. Referral ask — when you have a warm intro

```
Hey <Mutual>,

Quick ask — would you be open to a soft intro to <Name> at <Company>?
I'm targeting Forward Deployed Engineer roles at AI vendors and
health-tech shops where the customer envelope (runbook, rollback,
phased rollout, postmortems) matters as much as the model.

Just shipped a repo that I think speaks for itself:
  github.com/anix-lynch/healthcare-forward-deployed-engineer
  (12-wk phased rollout · 8 owner-mapped acceptance tests · runbook ·
   own-bug postmortem caught in pre-deployment audit)

Happy to draft the intro paragraph for you — just need a yes and
I'll send a one-liner you can forward.

Thanks 🙏
— Anix
```

**Critical:** offer to write the intro paragraph. Removes the friction. ~3x conversion vs "would you intro me?"

---

## Send cadence — what actually works

```
WEEK 1   20 targeted messages   ← FDE seats are scarcer than data eng
                                  fewer absolute targets, but higher
                                  intent per target
WEEK 2   20 more + 5 follow-ups on Week 1
WEEK 3   20 more + 10 follow-ups
WEEK 4   review what's working, double down on best-converting hook

EXPECTED REPLY RATE  15-25% on personalized outreach (FDE is small
                      community, your repo gets passed around)
EXPECTED MEETING RATE  5-8% (1-2 calls / week from 20 sends)
EXPECTED OFFER RATE  1 offer per ~30-50 quality conversations
                     (FDE is hot in 2026 + small candidate pool)
```

---

## Follow-up template (Day 5-7 after no reply)

```
Hi <Name> — bumping this in case it got buried.

The 90-second TL;DR: I build the FDE-deliverable shape — customer
brief, runbook, phased rollout, owner-mapped acceptance tests, and
postmortems for my own bugs. Repo:
github.com/anix-lynch/healthcare-forward-deployed-engineer

If now's not the right time, totally understand — happy to circle
back in Q3.

— Anix
```

**Single follow-up. Then move on.** Don't be that person who sends 4 follow-ups.

---

## What NOT to do (FDE-specific)

```
❌ Don't pitch yourself as "AI engineer who also deploys"
   ← FDE is a DIFFERENT role, not AI-eng + deployment combo
❌ Don't lead with the model architecture
   ← FDE hiring managers want "would this person survive at a hospital
      site for 12 weeks" — that's the runbook + customer envelope
❌ Don't list every framework you've used
   ← FDE = T-shape (deep on customer engagement, broad on systems)
❌ Don't send the same message to a Palantir FDE and a health-tech FDE
   ← Palantir wants pure systems chops; health-tech wants HIPAA fluency
❌ Don't mention TC expectations in the cold message
❌ Don't apologize for "interrupting"
❌ Don't attach a resume in the first message
   ← FDE candidates with repos > FDE candidates with resumes
❌ Don't lead with "I know Python and FastAPI" — commodity
❌ Don't claim "production experience" without specific customer-
   facing artifacts (brief, runbook, postmortem)
   ← FDE interviewers WILL ask "show me your runbook"

✅ DO send to hiring managers + FDE/field-eng ICs
✅ DO personalize the first line (proves you looked)
✅ DO link the repo, not a resume
✅ DO close with a specific ask (20-min chat about THEIR setup)
✅ DO follow up exactly once
✅ DO lead with the postmortem — it's the rarest FDE signal
✅ DO mention healthcare ONLY if target is health-tech / regulated
✅ DO drop healthcare for Palantir/Databricks/non-health — lead
   with phased rollout + runbook + acceptance tests instead
```

---

## Target taxonomy — who actually hires FDEs

```
TIER 1 — Highest match for your repo
─────────────────────────────────────────────────────────────────
Health-tech AI vendors        Abridge · Hippocratic AI · Layer Health ·
deploying to providers          Suki · Nuance/DAX · Notable · Innovaccer
                              → your healthcare narrative IS the moat

Clinical-data AI vendors      Truveta · Epic vendors · Datavant ·
                              Komodo Health · Veeva (life sciences)
                              → frame as "I speak FHIR + know HIPAA"

TIER 2 — Strong match, healthcare optional
─────────────────────────────────────────────────────────────────
Enterprise GenAI vendors      OpenAI FDE · Anthropic FDE · Cohere FDE
                              → drop healthcare bullets, lead with
                                phased rollout + acceptance tests +
                                postmortem methodology

Vertical AI vendors           Sierra (CX) · Hebbia (legal) · Harvey
deploying to F500              (legal) · Glean (knowledge)
                              → frame as "customer envelope around AI"

TIER 3 — Possible, more competitive
─────────────────────────────────────────────────────────────────
Big-tech FDE-shaped           Palantir FDE · Databricks FDE ·
roles                         Snowflake field-eng · Stripe solutions eng
                              → drop healthcare entirely, lead with
                                systems depth (FHIR transform + LOINC +
                                split-sink audit shows you can do the
                                generic version of this)
```

---

## Channel-specific tweaks

```
HEALTH-TECH FDE HIRES         Reference HIPAA / FHIR / clinical workflow.
                              Send to BOTH the FDE hiring manager AND
                              the clinical lead (MD/RN on the team).
                              The clinician will be the unblocker.

PALANTIR-STYLE FDE            Don't mention healthcare. Lead with
                              phased rollout + brownfield integration +
                              own-bug postmortem. Reference their
                              "deployment is the product" thesis if
                              you've read their blog.

CONFERENCE SPEAKERS           "Saw your <Field Engineering Meetup /
                              QCon / Software Engineering Daily> talk"
                              + specific quote. FDE community is small,
                              speakers remember who actually listened.

OPEN-SOURCE MAINTAINERS       Open an issue on their adapter / SDK /
                              integration toolkit BEFORE the DM. The DM
                              then references the issue. Conversion ~5x
                              vs cold.

EX-COLLEAGUES OF FOUNDERS     Find a mutual on LinkedIn, send the
                              referral template above. FDE shops hire
                              heavily through warm intros — bigger
                              uplift than for IC roles.

ANGELLIST / WELLFOUND         Filter for "forward deployed" / "field
                              engineering" / "solutions engineer" /
                              "deployment engineer" / "customer eng".
                              FDE has 4+ title variants — search all.
```

---

## Interview pivot lines (when they ask "tell me about your project")

```
30-SECOND PITCH (use first):
"I built the deliverable shape an FDE actually ships at a hospital
site — customer brief, solution design, 12-week phased rollout,
acceptance tests mapped to customer-role owners, runbook with safety
floors, and a postmortem of a brief↔code drift bug I caught in my own
repo during a pre-deployment audit. The point isn't the AI; it's the
envelope around it."

WHEN THEY ASK "what's the hardest part of FDE":
"Brief↔code drift. The customer signs off on a 10-page brief that
promises behavior X. The code ships a function shaped like X.
Six months later in production, someone notices X never actually
fires because an upstream constant blocks the signal. That's the
failure mode I tried to instrument against — every 'MUST' in the
brief maps to an acceptance test with a named customer owner.
Postmortem #002 in my repo is exactly this pattern caught on my
own code."

WHEN THEY ASK "what would Week 1 look like for you at <Company>":
"Read your existing customer briefs. Find the gaps between what
the brief promises and what the code does. Write up the first
brief↔code drift audit by end of Week 2. That's the artifact that
proves I can do this without supervision."
```

---

## Tracking spreadsheet — minimum viable columns

```
COL                  EXAMPLE
─────────────────────────────────────────────────
Company              Abridge
Role                 Forward Deployed Engineer (Clinical)
Hiring manager       <name> — LinkedIn URL
Sent date            2026-05-17
Channel              LinkedIn DM (longer template)
Hook used            #1 postmortem
Personalization      Referenced their Series E post + ambient AI
Reply (Y/N)          —
Meeting (Y/N)        —
Outcome              —
Next action          Follow up 2026-05-24
```

Track reply-rate by hook (#1 vs #2 vs #3). Double down on what's working in Week 4.
