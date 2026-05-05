---
trigger: always_on
---
## Single Responsibility Principle — strict rules (feature-based, in depth)

### 0. Core invariant

A unit (file/class/module) must have:

* **one responsibility**
* **one reason to change**
* **one primary actor (stakeholder)**

If any of these > 1 → split.

---

## 1. Responsibility boundaries (non-negotiable separation)

Treat these as **orthogonal axes**. A unit may own **exactly one**:

1. **Input handling** (controllers/adapters)
2. **Application orchestration** (use cases/services)
3. **Domain rules/invariants** (models/domain services)
4. **Persistence** (repositories)
5. **External integration** (email, payments, APIs)
6. **Object construction** (factories/mappers)
7. **State representation** (UI/app state)
8. **Type/shape definitions** (DTOs/types)

**Hard rule:** No unit spans multiple axes.

---

## 2. Layer isolation rules

* **Presentation (controllers/state)** must not contain business rules or persistence.
* **Application (use cases)** must not contain infrastructure details or UI concerns.
* **Domain (models/rules)** must not perform I/O or depend on frameworks.
* **Infrastructure (repositories/integrations)** must not contain business decisions.

**Violation trigger:** any upward or lateral leakage of concerns.

---

## 3. Controller rules (input adapters)

* Accept, normalize, and forward input only.
* Perform **schema/shape validation only** (no business validation).
* Map transport ↔ application types.
* No branching on business rules.
* No direct calls to repositories or external services.
* No state mutation beyond request scope.

**Change reason allowed:** API/transport contract changes only.

---

## 4. Use case / service rules (application layer)

* Orchestrate **one use case** (one user-intent).
* Sequence collaborators; do not embed their logic.
* Depend on **ports/interfaces**, not implementations.
* No formatting/presentation logic.
* No direct DB/network/file access.
* Keep decision points tied to the **single use case goal** only.

**Change reason allowed:** workflow of that use case.

---

## 5. Domain model rules

* Encapsulate **state + invariants**.
* Enforce consistency locally (e.g., validity constraints).
* No persistence, no HTTP, no messaging.
* No knowledge of DTOs or UI.
* Deterministic behavior; side-effect free (except internal state).

**Change reason allowed:** domain rules for that entity.

---

## 6. Repository rules (persistence)

* Map domain ↔ storage and perform CRUD/query.
* No business validation or decisions.
* No orchestration across aggregates.
* No formatting for UI.
* Hide storage specifics behind the interface.

**Change reason allowed:** storage schema/technology/query changes.

---

## 7. External integration rules (email, payments, APIs)

* Implement a **single external capability**.
* Translate domain calls → provider API calls.
* Handle provider-specific errors/retries.
* No business branching unrelated to the integration.
* No persistence except what is intrinsic to the integration.

**Change reason allowed:** provider/API changes.

---

## 8. Factory / mapper rules

* Create or transform objects only.
* No I/O, no orchestration, no policy.
* Deterministic mapping (input → output).

**Change reason allowed:** construction/mapping shape changes.

---

## 9. Ports (interfaces) rules

* Define contracts for dependencies.
* No logic, no defaults with behavior.
* No framework coupling.

**Change reason allowed:** contract evolution only.

---

## 10. Types / DTO rules

* Pure data shapes.
* No methods/behavior.
* Separate types per boundary (transport vs domain vs persistence).

**Change reason allowed:** data contract changes.

---

## 11. State rules (UI/app state)

* Represent **state snapshots** only.
* No side effects, no I/O.
* No business decisions.
* No cross-feature data ownership.

**Change reason allowed:** UI state model changes.

---

## 12. Orchestrator constraint

* A coordinator is allowed to depend on multiple concerns **only to call them**.
* It must remain **thin**:

  * no embedded domain logic
  * no persistence logic
  * no integration logic
* If logic grows, push it down to the owning unit.

---

## 13. Dependency rules

* Depend **inward** (presentation → application → domain).
* Infrastructure depends on domain contracts (ports), not vice versa.
* A unit must not depend on collaborators from **multiple axes** unless it is the thin orchestrator.
* Minimize collaborators; each dependency should map to the same responsibility.

---

## 14. Change-based decomposition (operational rule)

Split when any of the following occurs:

* Different **release cadence** (e.g., email template vs DB schema).
* Different **stakeholders** request changes.
* Different **failure modes** (network vs validation).
* Different **testing strategies** required.
* Different **runtime environments** (client vs server).

---

## 15. Naming discipline

* Names must encode a **single responsibility**.
* Disallow vague aggregators as justification: `Manager`, `Helper`, generic `Service`.
* Prefer role-specific names tied to the axis: `Controller`, `UseCase`, `Repository`, `Validator`, `Sender`, `Factory`, `Mapper`, `State`.

---

## 16. Anti-patterns (automatic SRP violations)

* “God” classes (large surface area across axes).
* Transaction scripts mixing validation + persistence + integration.
* Repositories performing business rules.
* Controllers branching on domain logic.
* Models calling APIs or databases.
* Utilities with mixed concerns (“do everything” helpers).

---

## 17. Review checklist (binary tests)

A unit is **non-compliant** if any answer is “yes”:

* Does it mix **two axes** (e.g., business + persistence)?
* Can it change due to **two unrelated reasons**?
* Does it serve **multiple actors**?
* Does it require **unrelated dependencies** (DB + email + formatter)?
* Is its purpose describable only with **“and”**?
* Would a change in an external system (DB/API/UI) force edits here **without changing its core job**?

---

## 18. Final enforcement rule

> **One file, one feature, one concern, one reason to change.**

Any deviation requires decomposition until each unit satisfies all constraints above.
