---
trigger: manual
---

### DRY (Don’t Repeat Yourself) – Strict Rules

1. No duplicated logic across functions, classes, or modules
2. No copy-paste code; reuse or refactor immediately
3. Single source of truth for every piece of logic
4. Shared logic must be extracted into reusable functions/modules
5. Constants must be defined once and reused everywhere
6. Configuration values must not be duplicated
7. Validation logic must not be repeated; centralize it
8. Business rules must exist in only one place
9. Avoid duplicate condition checks across code paths
10. Repeated code blocks (>2 times) must be refactored

---

### Structural DRY Rules

11. Use utility/helper classes for common operations
12. Use inheritance or composition to eliminate duplication
13. Prefer generic/templated solutions over repeated implementations
14. Avoid duplicate data models or DTOs
15. Keep API contracts consistent; don’t redefine structures

---

### Data & Logic DRY

16. Do not duplicate database queries; centralize access logic
17. Avoid repeating serialization/deserialization logic
18. Reuse mapping/transform logic via mappers
19. Keep business logic out of controllers/UI to prevent duplication
20. Avoid duplicating test logic; use shared test utilities

---

### Exception Handling DRY

21. Centralize error handling mechanisms
22. Do not repeat try-catch blocks with identical handling
23. Use common error/logging utilities

---

### Anti-Patterns (Strictly Disallowed)

24. Copy-paste with minor changes
25. Duplicate if/else chains across files
26. Rewriting the same algorithm in multiple places
27. Hardcoding same values in multiple locations

---

### Enforcement Rule

28. If the same logic appears **more than once**, it must be refactored
29. If duplication is unavoidable, it must be documented with justification

---