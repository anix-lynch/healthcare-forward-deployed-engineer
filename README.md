# healthcare-forward-deployed-engineer

> **Focused presentation cut of [`healthcare-genai-fullstack`](https://github.com/anix-lynch/healthcare-genai-fullstack) — Forward Deployed Engineer lens.**

This repo presents the **customer-deployment** slice of the master monorepo, narrowed for the Forward Deployed Engineer (FDE) interview signal:

- one scoped customer problem (ER triage at a sample hospital)
- one integration path (EHR adapter → canonical schema → workflow)
- one deployable workflow (with fallback + handoff)
- acceptance tests written as customer success criteria
- runbook + handoff guide
- one realistic postmortem

The point: **make AI work inside a messy enterprise**, not just demo it in a notebook.

It does **not** duplicate the full monorepo. The full 7-pattern coverage and Layer 1 data backbone live in the master repo.

---

## Status

🚧 Work in progress — incrementally extracted from the master monorepo.  
See [`ROADMAP.md`](ROADMAP.md) for what is landing next, in small commits.

> This repo is intentionally **lighter** in Phase 1 than the other two lenses.  
> It populates after GenAI Engineer and AI Data Engineer scaffolds are in place.

---

## Master monorepo

Full architecture context (3 layers · 7 patterns · multi-cloud adapter):

→ https://github.com/anix-lynch/healthcare-genai-fullstack

---

## Source of truth

This repo is a **presentation lens**, not an independent codebase.  
When in doubt, the monorepo is authoritative.

The goal here is **interview clarity** for the FDE role specifically,  
not a parallel customer-product project.
