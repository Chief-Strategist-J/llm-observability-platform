---
trigger: manual
---

### Strict Coding Rules (Concise List)

#### Type Casting

1. No implicit narrowing conversions
2. Explicit casting only when unavoidable
3. Mandatory type check before downcasting
4. No chained or multiple casts in one expression
5. Do not cast to fix type design issues
6. Avoid unnecessary primitive ↔ object casting
7. No invalid/incompatible type casts
8. Centralize risky casts in helper methods
9. No silent data loss during casting
10. Every cast must be justified in review

---

#### Null Handling

11. Null values must always be handled explicitly
12. No dereferencing without null checks
13. Prefer non-null types by default
14. Use safe defaults instead of returning null where possible
15. Validate all external inputs for null
16. Avoid deep null-check chains; refactor instead
17. Use optional/nullable wrappers where supported
18. Document any nullable field or return value

---

#### No Data Assumption

19. Never assume input data is valid
20. Always validate boundaries and formats
21. Do not assume collection sizes (check before access)
22. Do not assume object state is initialized
23. Handle all failure/error cases explicitly
24. Do not trust external systems or APIs blindly
25. Avoid hardcoded assumptions about data ranges or values
26. Always include fallback or error handling paths

---

#### List Handling

27. Always check for null or empty lists before use
28. Validate index bounds before accessing elements
29. Do not modify a list while iterating unless explicitly safe
30. Prefer immutable/read-only lists where possible
31. Handle duplicate elements explicitly if relevant
32. Avoid relying on list order unless guaranteed
33. Validate list size constraints (min/max limits)

---

#### Edge Case Handling

34. Always handle boundary values (min, max, zero, negative)
35. Handle empty input scenarios explicitly
36. Consider single-element cases separately if logic differs
37. Guard against overflow/underflow conditions
38. Handle unexpected or invalid formats safely
39. Ensure graceful failure with clear error handling
40. Test extreme and rare scenarios, not just normal flow

### Additional Strict Coding Rules

41. No magic numbers; use named constants
42. No duplicated logic; extract shared code immediately
43. No empty catch blocks
44. Never ignore returned values or errors
45. Every loop must have a clear termination condition
46. No infinite loops unless explicitly intended and documented
47. Do not use global mutable state unless unavoidable
48. Avoid side effects in utility functions
49. Keep functions single-purpose only
50. No deeply nested conditions; refactor after 2–3 levels
51. Do not suppress warnings without justification
52. Every public method must validate its inputs
53. Every output must be deterministic unless randomness is required
54. Do not depend on order unless the contract guarantees it
55. Never hardcode environment-specific values
56. Handle timeouts, retries, and failures explicitly
57. Do not expose internal implementation details in APIs
58. Use clear, consistent naming for variables and methods
59. Log failures with enough context, but never log secrets
60. Any workaround must have a removal plan

### Stricter one-line rule

> “Code must be explicit, validated, deterministic, testable, and safe under null, empty, boundary, failure, and retry conditions.”
