---
trigger: manual
---
---

### Function Parameter Limit Rule

**1. Maximum limit**

* A function/method **must not have more than 5 parameters**.

**2. Preferred limit**

* A function/method **should have no more than 3 parameters**.

**3. Mandatory refactor trigger**

* If parameters exceed **3**, you **must justify it in code review**.
* If parameters exceed **5**, you **must refactor** before merging.

**4. Refactoring requirements**
When exceeding limits, you must:

* Group related parameters into a **single object/struct**
* Or split the function into **smaller functions**
* Or use **named parameter objects (DTO/config objects)**

**5. Prohibited patterns**

* Long positional parameter lists (e.g., `func(a, b, c, d, e, f)`)
* Passing multiple unrelated primitives
* Boolean flags controlling multiple behaviors (e.g., `isAdmin, isActive, isTest`)

**6. Exceptions (rare, must be documented)**
Allowed only if ALL conditions are met:

* Performance-critical low-level code
* No logical grouping possible
* Clearly documented with comment explaining why

---

### One-line rule (for linting/docs)

> “No function shall have more than 5 parameters; prefer ≤3. Exceeding requires refactoring or explicit justification.”

