> **How to use this template**
> One-line *"Why it's critical"* notes explain each section's purpose — strip them before sharing. Unlike the other templates, an ADR is meant to be **short and one-decision-per-file** — resist the urge to bundle multiple decisions into one record.

---

# ADR-[NNN]: [Decision Title — phrased as the decision made, e.g., "Use PostgreSQL for primary datastore"]

| Field | Value |
|---|---|
| Status | Proposed / Accepted / Deprecated / Superseded by ADR-XXX |
| Date | |
| Deciders | |
| Related ADRs | |
| Related System | link to Solution Architecture Doc |

---

## 1. Context
*Why it's critical: without this, the decision looks arbitrary to anyone reading it 18 months later — this is the section that prevents "why did we ever do it this way?"*

What is the issue we're seeing that motivates this decision? Include relevant constraints (technical, business, team, timeline).

---

## 2. Decision Drivers
*Why it's critical: makes the evaluation criteria explicit so the "winning" option isn't just whichever the loudest person in the room preferred.*

| Driver | Why It Matters |
|---|---|
| e.g., Team familiarity | Reduces onboarding/ops risk |
| e.g., Cost at scale | Budget constraint for Y1 |
| e.g., Vendor lock-in | Strategic preference for portability |

---

## 3. Considered Options
*Why it's critical: shows the decision was actually a decision, not a default — critical for audits, onboarding, and revisiting the choice later.*

| Option | Pros | Cons | Cost/Effort |
|---|---|---|---|
| Option A | | | |
| Option B | | | |
| Option C (do nothing / status quo) | | | |

---

## 4. Decision Outcome

**Chosen option:** [Option X]

**Rationale:** why this option best satisfies the decision drivers above.

---

## 5. Consequences
*Why it's critical: every architecture decision has a cost — naming it up front means it doesn't get "discovered" as a surprise later and blamed on the decision itself.*

| Positive | Negative / Risk Accepted |
|---|---|
| | |

---

## 6. Compliance / Validation
*Why it's critical: turns the decision into something checkable — e.g., a lint rule, CI check, or review checklist item — instead of relying on institutional memory.*

- How will adherence to this decision be verified (code review checklist, architecture fitness function, CI gate)?

---

## 7. Related Decisions
- Supersedes: ADR-XXX
- Related to: ADR-YYY
- Superseded by: (fill in when deprecated)

---

## 8. Appendix
- **A. Links:** spike/prototype results, benchmark data, vendor docs
- **B. Discussion notes / meeting reference**