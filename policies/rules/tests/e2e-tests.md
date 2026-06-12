E2E Tests — Full Feature Slice

One test per user-facing flow — not one test per endpoint.
Tests the complete path: HTTP request → handler → service → repository → DB → response.
Uses real infra via docker-compose.test.yaml — real DB, real cache if applicable.
No mocks inside the feature — the full stack runs.
Each test is fully independent — no reliance on previous test state.
Tests verify the actual response body matches the contract exactly.
Tests verify that side effects occurred — events published, emails enqueued, audit rows written.
