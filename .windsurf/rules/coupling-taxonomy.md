---
trigger: manual
---


Connascence — The Real Coupling Taxonomy

COLDEST (safest, easiest to change)
  │
  ├── CoN  — Connascence of Name         → A calls B by name
  ├── CoT  — Connascence of Type         → A and B agree on a type
  ├── CoM  — Connascence of Meaning      → A and B agree on a value's meaning (e.g. 0 = success)
  ├── CoP  — Connascence of Position     → A passes args in the right order
  ├── CoA  — Connascence of Algorithm    → A and B must use the same algorithm (e.g. same hash)
  ├── CoE  — Connascence of Execution    → A must run before B
  ├── CoT  — Connascence of Timing       → A must run at the same time as B (race conditions)
  ├── CoV  — Connascence of Value        → A and B share a mutable value
  └── CoI  — Connascence of Identity     → A and B must reference the exact same object in memory
  │
HOTTEST (most dangerous, hardest to change)
The goal: Push all coupling toward the top (Name/Type). Any coupling below Algorithm is a design smell in large systems.
