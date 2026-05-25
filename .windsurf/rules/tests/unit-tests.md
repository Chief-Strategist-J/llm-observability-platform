Unit Tests — Feature Service Layer

One test file per service method.
Every test describes one behaviour — not one function.
All dependencies are injected mocks implementing the port interface.
Every happy path is tested.
Every error path is tested — invalid input, dependency failure, not-found, conflict.
Every business rule is tested — boundary values, edge cases.
No test touches the database, network, or filesystem.
Coverage minimum 80% on service files. 100% is the target for critical business rules.
