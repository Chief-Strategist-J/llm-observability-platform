import Foundation
import OpenTelemetryApi
import OpenTelemetrySdk

/// Holds every live span for a single root trace.
public final class TraceContext {

    /// The hex string returned to callers from `start()`.
    public let traceId: String

    /// The root span created by `start()`.
    public let rootSpan: Span

    /// Child spans keyed by `"\(cls).\(function)"`.
    private var childSpans: [String: Span] = [:]

    /// Ordered list so we can end children before root.
    private var spanOrder: [String] = []

    private let lock = NSLock()

    public init(traceId: String, rootSpan: Span) {
        self.traceId = traceId
        self.rootSpan = rootSpan
    }

    // MARK: - Child span management

    /// Returns an existing child span or creates one via `factory`.
    public func getOrCreateSpan(key: String, factory: () -> Span) -> Span {
        lock.lock()
        defer { lock.unlock() }
        if let existing = childSpans[key] {
            return existing
        }
        let span = factory()
        childSpans[key] = span
        spanOrder.append(key)
        return span
    }

    /// Ends all child spans (in creation order), then the root span.
    /// - Parameter status: `"ok"` or `"error"`
    public func endAll(status: String) {
        lock.lock()
        let orderedKeys = spanOrder
        let children = childSpans
        lock.unlock()

        let otelStatus: Status = (status.lowercased() == "error")
            ? .error(description: "error")
            : .ok

        // End children in reverse creation order
        for key in orderedKeys.reversed() {
            if let span = children[key] {
                span.status = otelStatus
                span.end()
            }
        }

        rootSpan.status = otelStatus
        rootSpan.end()
    }
}
