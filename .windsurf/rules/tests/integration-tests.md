Integration Tests — Feature Repository Layer

One test file per repository method.
Each test gets a clean, isolated database — no shared state between tests.
Migrations run on the clean database before the test suite starts.
Seeds load only the data this test needs — not a global fixture.
Tests verify that the SQL or query produces the correct result, not just that it ran.
Tests verify that soft-delete semantics are correct — deleted records are not returned.
Tests verify that ordering, pagination, and filtering work correctly.
The real database vendor is used — no SQLite substitute for a Postgres repo.
