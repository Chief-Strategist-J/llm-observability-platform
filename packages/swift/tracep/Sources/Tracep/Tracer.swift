import Foundation
import OpenTelemetryApi
import OpenTelemetrySdk
import OpenTelemetryProtocolExporterHTTP

// ---------------------------------------------------------------------------
// MARK: - Tracer
// ---------------------------------------------------------------------------

/// A fire-and-forget OTel tracing client.
///
/// ```swift
/// let tracer = Tracer(endpoint: "http://localhost:4318",
///                     apiKey: "my-key",
///                     service: "my-service")
///
/// let tid = tracer.start(name: "user-login")
/// tracer.trace(tid: tid, cls: "AuthService", function: "login",
///              step: "validate", message: "Checking credentials")
/// tracer.end(tid: tid, status: "ok")
/// tracer.close()
/// ```
public final class Tracer {

    // MARK: - Private state

    private let tracerProvider: TracerProviderSdk
    private let otelTracer: OpenTelemetryApi.Tracer

    /// Thread-safe dictionary of active TraceContexts keyed by hex trace-id.
    private var activeTraces: [String: TraceContext] = [:]
    private let traceLock = NSLock()

    /// Background queue for all OTel operations (fire-and-forget).
    private let queue = DispatchQueue(label: "com.tracep.background", qos: .background)

    // MARK: - Init

    /// Creates a new `Tracer` and bootstraps the OTel pipeline.
    ///
    /// - Parameters:
    ///   - endpoint: Base URL of the OTLP collector, e.g. `"http://collector:4318"`.
    ///   - apiKey:   API key sent as `Authorization: Bearer <apiKey>`.
    ///   - service:  Value for the `service.name` OTel resource attribute.
    public init(endpoint: String, apiKey: String, service: String) {
        // ----------------------------------------------------------------
        // 1. Build the OTLP/HTTP exporter
        // ----------------------------------------------------------------
        let tracesEndpoint = endpoint.hasSuffix("/")
            ? "\(endpoint)v1/traces"
            : "\(endpoint)/v1/traces"

        guard let url = URL(string: tracesEndpoint) else {
            fatalError("[Tracep] Invalid endpoint URL: \(tracesEndpoint)")
        }

        let otlpConfig = OtlpConfiguration(
            timeout: OtlpConfiguration.DefaultTimeoutInterval,
            headers: [("Authorization", "Bearer \(apiKey)")]
        )

        let exporter = OtlpHttpTraceExporter(
            endpoint: url,
            config: otlpConfig
        )

        // ----------------------------------------------------------------
        // 2. Wrap with a BatchSpanProcessor (buffer 512, schedule 1 s)
        // ----------------------------------------------------------------
        let batchConfig = BatchSpanProcessorConfiguration(
            maxExportBatchSize: 512,
            scheduledDelayMillis: 1_000,
            exportTimeoutMillis: 30_000,
            maxQueueSize: 2_048
        )
        let processor = BatchSpanProcessor(
            spanExporter: exporter,
            meterProvider: nil,
            configuration: batchConfig
        )

        // ----------------------------------------------------------------
        // 3. Create a TracerProvider with the service.name resource
        // ----------------------------------------------------------------
        let resource = Resource(attributes: [
            ResourceAttributes.serviceName: AttributeValue.string(service)
        ])

        tracerProvider = TracerProviderSdk(
            resource: resource,
            spanProcessors: [processor]
        )

        // Register as the global OTel provider so helper calls work.
        OpenTelemetry.registerTracerProvider(tracerProvider: tracerProvider)

        otelTracer = tracerProvider.get(
            instrumentationName: "tracep",
            instrumentationVersion: "1.0.0"
        )
    }

    // MARK: - Public API

    /// Begins a new root trace and returns an opaque trace-ID string.
    ///
    /// - Parameter name: Human-readable name for the root span.
    /// - Returns: Hex trace-ID that must be passed to subsequent calls.
    @discardableResult
    public func start(name: String) -> String {
        let rootSpan = otelTracer
            .spanBuilder(spanName: name)
            .setSpanKind(spanKind: .client)
            .startSpan()

        let traceIdHex = rootSpan.context.traceId.hexString

        let ctx = TraceContext(traceId: traceIdHex, rootSpan: rootSpan)

        traceLock.lock()
        activeTraces[traceIdHex] = ctx
        traceLock.unlock()

        return traceIdHex
    }

    /// Adds a span event to the span keyed by `cls + function` within `tid`.
    ///
    /// - Parameters:
    ///   - tid:      Trace-ID returned by `start()`.
    ///   - cls:      Class / module name (becomes `code.namespace` attribute).
    ///   - function: Function name (becomes `code.function` attribute).
    ///   - step:     Name of the span event.
    ///   - message:  Human-readable message attached to the event.
    ///   - parent:   Optional parent span key (`"\(cls).\(function)"` of parent span).
    ///   - level:    Severity string, default `"info"`.
    public func trace(
        tid: String,
        cls: String,
        function: String,
        step: String,
        message: String,
        parent: String? = nil,
        level: String = "info"
    ) {
        queue.async { [weak self] in
            guard let self else { return }

            self.traceLock.lock()
            let ctx = self.activeTraces[tid]
            self.traceLock.unlock()

            guard let ctx else {
                // Unknown tid — drop silently per spec.
                return
            }

            let spanKey = "\(cls).\(function)"

            // Resolve parent context if a parentKey was supplied.
            let parentSpan: Span?
            if let parentKey = parent {
                // If a specific parent span key is given, try to find it;
                // fall back to the root span.
                parentSpan = ctx.getOrCreateSpan(key: parentKey) {
                    // We should not create new spans for a parent hint that
                    // doesn't exist yet; return root as a safe fallback.
                    ctx.rootSpan
                }
            } else {
                parentSpan = nil
            }

            // Find or create the child span.
            let childSpan = ctx.getOrCreateSpan(key: spanKey) {
                var builder = self.otelTracer
                    .spanBuilder(spanName: "\(cls).\(function)")
                    .setSpanKind(spanKind: .internal)

                if let ps = parentSpan {
                    // Propagate the parent span's context.
                    builder = builder.setParent(ps)
                } else {
                    // Link to the root span.
                    builder = builder.setParent(ctx.rootSpan)
                }

                let span = builder.startSpan()
                span.setAttribute(key: "code.namespace", value: cls)
                span.setAttribute(key: "code.function",  value: function)
                return span
            }

            // Add a span event with message + level attributes.
            let eventAttributes: [String: OpenTelemetryApi.AttributeValue] = [
                "message": .string(message),
                "level":   .string(level),
            ]
            childSpan.addEvent(name: step, attributes: eventAttributes)
        }
    }

    /// Ends the trace identified by `tid`, flushing all spans to the exporter.
    ///
    /// - Parameters:
    ///   - tid:    Trace-ID returned by `start()`.
    ///   - status: `"ok"` (default) or `"error"`.
    public func end(tid: String, status: String) {
        queue.async { [weak self] in
            guard let self else { return }

            self.traceLock.lock()
            let ctx = self.activeTraces.removeValue(forKey: tid)
            self.traceLock.unlock()

            guard let ctx else { return }

            ctx.endAll(status: status)

            // Force-flush so events are exported before the caller moves on.
            _ = self.tracerProvider.forceFlush(timeout: 5)
        }
    }

    /// Shuts down the tracer provider, flushing any remaining spans.
    /// Call once when the process is about to exit.
    public func close() {
        queue.sync {
            // End any still-active traces as "ok".
            traceLock.lock()
            let remaining = activeTraces
            activeTraces.removeAll()
            traceLock.unlock()

            for (_, ctx) in remaining {
                ctx.endAll(status: "ok")
            }

            _ = tracerProvider.forceFlush(timeout: 10)
            tracerProvider.shutdown()
        }
    }
}

// ---------------------------------------------------------------------------
// MARK: - Retry-aware export (wraps exporter with 3× exponential back-off)
// ---------------------------------------------------------------------------

/// A `SpanExporter` decorator that retries up to `maxAttempts` times with
/// exponential back-off, then drops the batch silently on final failure.
final class RetrySpanExporter: SpanExporter {

    private let wrapped: SpanExporter
    private let maxAttempts: Int
    private let baseDelaySeconds: Double

    init(wrapped: SpanExporter, maxAttempts: Int = 3, baseDelaySeconds: Double = 1.0) {
        self.wrapped = wrapped
        self.maxAttempts = maxAttempts
        self.baseDelaySeconds = baseDelaySeconds
    }

    func export(spans: [SpanData], explicitTimeout: TimeInterval?) -> SpanExporterResultCode {
        var attempt = 0
        while attempt < maxAttempts {
            let result = wrapped.export(spans: spans, explicitTimeout: explicitTimeout)
            if result == .success {
                return .success
            }
            attempt += 1
            if attempt < maxAttempts {
                let delay = baseDelaySeconds * pow(2.0, Double(attempt - 1))
                Thread.sleep(forTimeInterval: delay)
            }
        }
        // Drop silently after maxAttempts.
        return .failure
    }

    func flush() -> SpanExporterResultCode { wrapped.flush() }
    func shutdown() { wrapped.shutdown() }
}
