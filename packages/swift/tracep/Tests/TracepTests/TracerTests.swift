import XCTest
@testable import Tracep

final class TracerTests: XCTestCase {

    // -------------------------------------------------------------------------
    // Helpers
    // -------------------------------------------------------------------------

    /// A dummy endpoint that won't actually export — tests focus on local
    /// state / API behaviour, not network connectivity.
    private let endpoint = "http://localhost:4318"
    private let apiKey   = "test-api-key"
    private let service  = "test-service"

    // -------------------------------------------------------------------------
    // Tests
    // -------------------------------------------------------------------------

    /// `start()` must return a non-empty, lowercase hex string.
    func testStartReturnsNonEmptyTid() {
        let tracer = Tracer(endpoint: endpoint, apiKey: apiKey, service: service)
        defer { tracer.close() }

        let tid = tracer.start(name: "test-trace")

        XCTAssertFalse(tid.isEmpty, "tid must not be empty")
        XCTAssertTrue(
            tid.allSatisfy { $0.isHexDigit },
            "tid must be a hex string, got: \(tid)"
        )
        XCTAssertGreaterThanOrEqual(tid.count, 16,
            "tid should be at least 16 hex chars (OTel trace-id is 32)")
    }

    /// Calling `trace()` with an unknown tid must not crash or throw.
    func testTraceWithUnknownTidIsIgnored() {
        let tracer = Tracer(endpoint: endpoint, apiKey: apiKey, service: service)
        defer { tracer.close() }

        // Deliberately use a tid that was never returned by start().
        let fakeTid = "deadbeefdeadbeefdeadbeefdeadbeef"

        // Should complete without crashing.
        tracer.trace(
            tid: fakeTid,
            cls: "SomeClass",
            function: "someMethod",
            step: "step1",
            message: "this should be silently ignored"
        )

        // Give the background queue a moment to process the no-op.
        Thread.sleep(forTimeInterval: 0.1)

        // If we reach here without a crash the test passes.
        XCTAssertTrue(true)
    }

    /// Calling `end()` with an unknown tid must not crash or throw.
    func testEndWithUnknownTidIsIgnored() {
        let tracer = Tracer(endpoint: endpoint, apiKey: apiKey, service: service)
        defer { tracer.close() }

        let fakeTid = "cafebabecafebabecafebabecafebabe"

        tracer.end(tid: fakeTid, status: "ok")

        Thread.sleep(forTimeInterval: 0.1)

        XCTAssertTrue(true)
    }

    /// Starting multiple traces must return distinct tids.
    func testMultipleStartsReturnDistinctTids() {
        let tracer = Tracer(endpoint: endpoint, apiKey: apiKey, service: service)
        defer { tracer.close() }

        let tid1 = tracer.start(name: "trace-a")
        let tid2 = tracer.start(name: "trace-b")
        let tid3 = tracer.start(name: "trace-c")

        let unique = Set([tid1, tid2, tid3])
        XCTAssertEqual(unique.count, 3, "Each start() must yield a unique tid")
    }

    /// Full happy-path: start → trace → end should complete without errors.
    func testFullHappyPath() {
        let tracer = Tracer(endpoint: endpoint, apiKey: apiKey, service: service)
        defer { tracer.close() }

        let tid = tracer.start(name: "happy-path")

        tracer.trace(
            tid: tid,
            cls: "OrderService",
            function: "placeOrder",
            step: "validate",
            message: "Validating order payload",
            level: "info"
        )
        tracer.trace(
            tid: tid,
            cls: "OrderService",
            function: "placeOrder",
            step: "persist",
            message: "Saving order to DB",
            level: "debug"
        )

        tracer.end(tid: tid, status: "ok")

        // Give the background queue time to drain.
        Thread.sleep(forTimeInterval: 0.2)

        XCTAssertTrue(true, "Happy-path completed without crash")
    }
}
