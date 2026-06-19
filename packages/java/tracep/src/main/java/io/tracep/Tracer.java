package io.tracep;

import io.opentelemetry.api.common.AttributeKey;
import io.opentelemetry.api.common.Attributes;
import io.opentelemetry.api.trace.Span;
import io.opentelemetry.api.trace.SpanContext;
import io.opentelemetry.api.trace.SpanKind;
import io.opentelemetry.api.trace.StatusCode;
import io.opentelemetry.api.trace.TraceFlags;
import io.opentelemetry.api.trace.TraceState;
import io.opentelemetry.context.Context;
import io.opentelemetry.exporter.otlp.http.trace.OtlpHttpSpanExporter;
import io.opentelemetry.sdk.resources.Resource;
import io.opentelemetry.sdk.trace.SdkTracerProvider;
import io.opentelemetry.sdk.trace.export.BatchSpanProcessor;

import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * Fire-and-forget OTel-backed tracer.
 *
 * <h2>Lifecycle</h2>
 * <ol>
 *   <li>Construct once – sets up {@link SdkTracerProvider} + OTLP/HTTP exporter.</li>
 *   <li>Call {@link #start(String)} to open a root trace; hold the returned <em>tid</em>.</li>
 *   <li>Call {@link #trace(String, String, String, String, String)} (or the overload with
 *       {@code parent} / {@code level}) repeatedly to record events.</li>
 *   <li>Call {@link #end(String, String)} with {@code "ok"} or {@code "error"} to close.</li>
 *   <li>Call {@link #close()} once at application shutdown to flush &amp; release resources.</li>
 * </ol>
 *
 * <h2>Thread safety</h2>
 * All public methods are thread-safe.  Span operations are dispatched to an internal
 * single-thread executor so they never block the caller.
 */
public class Tracer implements AutoCloseable {

    // ── attribute keys ────────────────────────────────────────────────────────
    static final AttributeKey<String> CODE_NAMESPACE = AttributeKey.stringKey("code.namespace");
    static final AttributeKey<String> CODE_FUNCTION   = AttributeKey.stringKey("code.function");
    static final AttributeKey<String> ATTR_MESSAGE    = AttributeKey.stringKey("message");
    static final AttributeKey<String> ATTR_LEVEL      = AttributeKey.stringKey("level");
    static final AttributeKey<String> SERVICE_NAME    = AttributeKey.stringKey("service.name");

    private static final Logger LOG = Logger.getLogger(Tracer.class.getName());

    // ── OTel infrastructure ───────────────────────────────────────────────────
    private final SdkTracerProvider      tracerProvider;
    private final io.opentelemetry.api.trace.Tracer otelTracer;

    // ── state ─────────────────────────────────────────────────────────────────
    /**
     * Keyed by trace-id hex string.
     * Each {@link TraceContext} holds the root span plus a per-(class,function) child-span map.
     */
    private final ConcurrentHashMap<String, TraceContext> traces = new ConcurrentHashMap<>();

    /** All Tracer public methods post work here – never blocks the caller. */
    private final ExecutorService executor;

    // ── inner state holder ────────────────────────────────────────────────────

    /** Holds all state for a single root trace. */
    private static final class TraceContext {
        final Span                              rootSpan;
        /** Keyed by "class::function" */
        final ConcurrentHashMap<String, Span>  childSpans = new ConcurrentHashMap<>();

        TraceContext(Span rootSpan) { this.rootSpan = rootSpan; }
    }

    // ── constructors ──────────────────────────────────────────────────────────

    /**
     * Convenience constructor – uses all {@link TracerOptions} defaults.
     *
     * @param endpoint Base URL of the OTLP collector, e.g. {@code http://localhost:4318}
     * @param apiKey   Bearer token for the {@code Authorization} header
     * @param service  Logical service name ({@code service.name} resource attribute)
     */
    public Tracer(String endpoint, String apiKey, String service) {
        this(TracerOptions.of(endpoint, apiKey, service));
    }

    /**
     * Full constructor accepting a {@link TracerOptions} instance.
     */
    public Tracer(TracerOptions options) {
        this(options, null);
    }

    /**
     * Package-private constructor that allows tests to inject a pre-built
     * {@link SdkTracerProvider} (e.g. backed by an in-memory exporter).
     */
    Tracer(TracerOptions options, SdkTracerProvider injectedProvider) {
        if (injectedProvider != null) {
            this.tracerProvider = injectedProvider;
        } else {
            // ── Build OTLP/HTTP exporter ──────────────────────────────────────
            String tracesEndpoint = normaliseEndpoint(options.getEndpoint()) + "/v1/traces";

            OtlpHttpSpanExporter exporter = OtlpHttpSpanExporter.builder()
                    .setEndpoint(tracesEndpoint)
                    .addHeader("Authorization", "Bearer " + options.getApiKey())
                    // The OTel SDK's HTTP exporter has built-in retry logic;
                    // the retry interceptor is enabled by default (3 attempts, exp back-off).
                    .build();

            // ── Batch processor ───────────────────────────────────────────────
            BatchSpanProcessor bsp = BatchSpanProcessor.builder(exporter)
                    .setMaxExportBatchSize(options.getMaxExportBatchSize())
                    .setScheduleDelay(options.getScheduleDelay())
                    .build();

            // ── Resource ──────────────────────────────────────────────────────
            Resource resource = Resource.getDefault()
                    .merge(Resource.create(Attributes.of(SERVICE_NAME, options.getService())));

            // ── TracerProvider ────────────────────────────────────────────────
            this.tracerProvider = SdkTracerProvider.builder()
                    .addSpanProcessor(bsp)
                    .setResource(resource)
                    .build();
        }

        this.otelTracer = tracerProvider.get("io.tracep");

        // Single background thread for all OTel operations – fire-and-forget
        this.executor = Executors.newSingleThreadExecutor(r -> {
            Thread t = new Thread(r, "tracep-worker");
            t.setDaemon(true);   // does not prevent JVM shutdown
            return t;
        });
    }

    // ── public API ────────────────────────────────────────────────────────────

    /**
     * Opens a new root trace.
     *
     * @param name Human-readable span name
     * @return Trace-ID as a 32-character lowercase hex string (OTel trace-id)
     */
    public String start(String name) {
        // Root span is created synchronously so the caller gets a valid tid immediately.
        Span rootSpan = otelTracer.spanBuilder(name)
                .setSpanKind(SpanKind.SERVER)
                .startSpan();

        String tid = rootSpan.getSpanContext().getTraceId();   // 32-char hex
        traces.put(tid, new TraceContext(rootSpan));
        return tid;
    }

    /**
     * Records a trace event with default level {@code "info"} and no parent span link.
     *
     * @param tid      Trace ID returned by {@link #start(String)}
     * @param cls      Logical class / component name ({@code code.namespace})
     * @param function Method / function name ({@code code.function})
     * @param step     Span-event name
     * @param message  Human-readable message attached to the event
     */
    public void trace(String tid, String cls, String function, String step, String message) {
        trace(tid, cls, function, step, message, null, "info");
    }

    /**
     * Records a trace event.
     *
     * @param tid      Trace ID returned by {@link #start(String)}
     * @param cls      Logical class / component name ({@code code.namespace})
     * @param function Method / function name ({@code code.function})
     * @param step     Span-event name
     * @param message  Human-readable message attached to the event
     * @param parent   Optional span-id hex of a parent span (may be {@code null})
     * @param level    Severity label, e.g. {@code "info"}, {@code "warn"}, {@code "error"}
     */
    public void trace(String tid, String cls, String function,
                      String step, String message,
                      String parent, String level) {

        executor.submit(() -> {
            try {
                TraceContext ctx = traces.get(tid);
                if (ctx == null) {
                    // Unknown tid – silently ignore
                    return;
                }

                String spanKey = cls + "::" + function;
                Span childSpan = ctx.childSpans.computeIfAbsent(spanKey, k ->
                        buildChildSpan(ctx, cls, function, parent));

                // Add event to the child span
                String effectiveLevel = (level != null && !level.isBlank()) ? level : "info";
                childSpan.addEvent(step, Attributes.of(
                        ATTR_MESSAGE, message,
                        ATTR_LEVEL,   effectiveLevel));

            } catch (Exception ex) {
                LOG.log(Level.FINE, "tracep: trace() error (suppressed)", ex);
            }
        });
    }

    /**
     * Closes all spans for the given trace, sets their status, and flushes the exporter.
     *
     * @param tid    Trace ID returned by {@link #start(String)}
     * @param status {@code "ok"} or {@code "error"}
     */
    public void end(String tid, String status) {
        executor.submit(() -> {
            try {
                TraceContext ctx = traces.remove(tid);
                if (ctx == null) {
                    // Unknown tid – silently ignore
                    return;
                }

                StatusCode code = "error".equalsIgnoreCase(status)
                        ? StatusCode.ERROR : StatusCode.OK;

                // End child spans first (reverse insertion order is not guaranteed,
                // but OTel collectors handle out-of-order endings gracefully).
                ctx.childSpans.values().forEach(span -> {
                    span.setStatus(code);
                    span.end();
                });

                ctx.rootSpan.setStatus(code);
                ctx.rootSpan.end();

                // Force-flush so the exporter ships data before we return to caller.
                tracerProvider.forceFlush().join(10, TimeUnit.SECONDS);

            } catch (Exception ex) {
                LOG.log(Level.FINE, "tracep: end() error (suppressed)", ex);
            }
        });
    }

    /**
     * Shuts down the background worker and the OTel {@link SdkTracerProvider}.
     * Call once at application shutdown (or use try-with-resources).
     */
    @Override
    public void close() {
        executor.shutdown();
        try {
            if (!executor.awaitTermination(5, TimeUnit.SECONDS)) {
                executor.shutdownNow();
            }
        } catch (InterruptedException e) {
            executor.shutdownNow();
            Thread.currentThread().interrupt();
        }
        tracerProvider.shutdown().join(10, TimeUnit.SECONDS);
    }

    // ── private helpers ───────────────────────────────────────────────────────

    /**
     * Creates a child span rooted under {@code ctx.rootSpan}, optionally linked to
     * the span identified by {@code parentSpanId}.
     */
    private Span buildChildSpan(TraceContext ctx, String cls, String function, String parentSpanId) {
        io.opentelemetry.api.trace.SpanBuilder sb = otelTracer
                .spanBuilder(cls + "." + function)
                .setSpanKind(SpanKind.INTERNAL)
                .setAttribute(CODE_NAMESPACE, cls)
                .setAttribute(CODE_FUNCTION,  function);

        if (parentSpanId != null && !parentSpanId.isBlank()) {
            // Reconstruct parent SpanContext and set it as the remote parent
            SpanContext parentCtx = SpanContext.createFromRemoteParent(
                    ctx.rootSpan.getSpanContext().getTraceId(),
                    parentSpanId,
                    TraceFlags.getSampled(),
                    TraceState.getDefault());

            if (parentCtx.isValid()) {
                Context remoteCtx = Context.root().with(Span.wrap(parentCtx));
                sb.setParent(remoteCtx);
            } else {
                // Fall back to root span as parent
                sb.setParent(Context.root().with(ctx.rootSpan));
            }
        } else {
            sb.setParent(Context.root().with(ctx.rootSpan));
        }

        return sb.startSpan();
    }

    /** Strips trailing slashes from the base URL. */
    private static String normaliseEndpoint(String endpoint) {
        if (endpoint == null) return "";
        return endpoint.replaceAll("/+$", "");
    }
}
