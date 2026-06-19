//! Unit tests for the [`tracep::Tracer`] struct.
//!
//! These tests do **not** require a live OTLP collector.  The SDK is
//! initialised against a non-existent endpoint; failed exports are dropped
//! silently after retries – which is the intended fire-and-forget behaviour.

use tracep::Tracer;

/// Convenience helper: build a tracer pointed at a local dummy endpoint.
fn make_tracer() -> Tracer {
    Tracer::new(
        "http://127.0.0.1:14318", // nothing listening here – that's fine
        "test-api-key",
        "tracep-unit-tests",
    )
    .expect("Tracer::new should succeed even with an unreachable endpoint")
}

// ── start() ──────────────────────────────────────────────────────────────────

#[tokio::test]
async fn start_returns_non_empty_hex_string() {
    let tracer = make_tracer();
    let tid = tracer.start("test-root-span");

    assert!(!tid.is_empty(), "tid must not be empty");
    assert_eq!(tid.len(), 32, "OTel trace-id hex is always 32 chars");
    assert!(
        tid.chars().all(|c| c.is_ascii_hexdigit()),
        "tid must contain only hex digits, got: {tid}"
    );

    tracer.close();
}

#[tokio::test]
async fn start_returns_unique_tids() {
    let tracer = make_tracer();
    let tid1 = tracer.start("span-a");
    let tid2 = tracer.start("span-b");

    assert_ne!(tid1, tid2, "each start() call must produce a unique tid");

    tracer.end(&tid1, "ok");
    tracer.end(&tid2, "ok");
    tracer.close();
}

// ── trace() ──────────────────────────────────────────────────────────────────

#[tokio::test]
async fn trace_unknown_tid_is_silently_ignored() {
    let tracer = make_tracer();

    // Must not panic or return an error.
    tracer.trace(
        "0000000000000000ffffffffffffffff", // unknown tid
        "SomeClass",
        "some_fn",
        "step-x",
        "should be ignored",
        None,
        None,
    );

    tracer.close();
}

#[tokio::test]
async fn trace_adds_event_to_known_tid() {
    let tracer = make_tracer();
    let tid = tracer.start("operation");

    // Should complete without panicking.
    tracer.trace(
        &tid,
        "MyClass",
        "my_function",
        "step-1",
        "hello from step 1",
        None,
        Some("debug"),
    );

    tracer.end(&tid, "ok");
    tracer.close();
}

#[tokio::test]
async fn trace_with_parent_span_key() {
    let tracer = make_tracer();
    let tid = tracer.start("parent-child-test");

    // Create the parent span.
    tracer.trace(
        &tid,
        "ParentClass",
        "parent_fn",
        "parent-step",
        "parent message",
        None,
        None,
    );

    // Create a child that references the parent span.
    tracer.trace(
        &tid,
        "ChildClass",
        "child_fn",
        "child-step",
        "child message",
        Some("ParentClass::parent_fn"),
        Some("warn"),
    );

    tracer.end(&tid, "ok");
    tracer.close();
}

// ── end() ────────────────────────────────────────────────────────────────────

#[tokio::test]
async fn end_with_ok_status_does_not_panic() {
    let tracer = make_tracer();
    let tid = tracer.start("ending-ok");
    tracer.end(&tid, "ok");
    tracer.close();
}

#[tokio::test]
async fn end_with_error_status_does_not_panic() {
    let tracer = make_tracer();
    let tid = tracer.start("ending-error");
    tracer.end(&tid, "error");
    tracer.close();
}

#[tokio::test]
async fn end_unknown_tid_is_silently_ignored() {
    let tracer = make_tracer();
    // Must not panic.
    tracer.end("deadbeefdeadbeefdeadbeefdeadbeef", "ok");
    tracer.close();
}

#[tokio::test]
async fn end_twice_is_silently_ignored() {
    let tracer = make_tracer();
    let tid = tracer.start("double-end");
    tracer.end(&tid, "ok");
    // Second call: tid already removed from map → silent no-op.
    tracer.end(&tid, "ok");
    tracer.close();
}

// ── full round-trip ───────────────────────────────────────────────────────────

#[tokio::test]
async fn full_round_trip() {
    let tracer = make_tracer();

    let tid = tracer.start("full-round-trip");
    assert!(!tid.is_empty());

    tracer.trace(&tid, "ServiceA", "handle_request", "validate", "input ok", None, Some("info"));
    tracer.trace(&tid, "ServiceA", "handle_request", "process",  "done",     None, Some("info"));
    tracer.trace(
        &tid,
        "ServiceB",
        "call_db",
        "query",
        "rows=42",
        Some("ServiceA::handle_request"),
        Some("debug"),
    );

    tracer.end(&tid, "ok");
    tracer.close();
}
