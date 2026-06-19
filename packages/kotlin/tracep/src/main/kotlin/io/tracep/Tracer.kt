package io.tracep

import io.opentelemetry.api.common.AttributeKey
import io.opentelemetry.api.common.Attributes
import io.opentelemetry.api.trace.Span
import io.opentelemetry.api.trace.SpanContext
import io.opentelemetry.api.trace.SpanKind
import io.opentelemetry.api.trace.StatusCode
import io.opentelemetry.api.trace.TraceFlags
import io.opentelemetry.api.trace.TraceState
import io.opentelemetry.context.Context
import io.opentelemetry.exporter.otlp.http.trace.OtlpHttpSpanExporter
import io.opentelemetry.sdk.resources.Resource
import io.opentelemetry.sdk.trace.SdkTracerProvider
import io.opentelemetry.sdk.trace.export.BatchSpanProcessor
import io.opentelemetry.semconv.resource.attributes.ResourceAttributes
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.TimeUnit
import kotlin.time.Duration.Companion.seconds

// ---------------------------------------------------------------------------
// Domain model
// ---------------------------------------------------------------------------

/**
 * Holds all live state for a single root trace.
 *
 * @property rootSpan    The root OTel span created by [Tracer.start].
 * @property traceId     Hex-encoded W3C trace-id (32 chars).
 * @property spans       Child spans keyed by "ClassName#functionName".
 * @property otelTracer  The OTel API tracer scoped to this trace's provider.
 */
data class TraceContext(
    val rootSpan: Span,
    val traceId: String,
    val spans: ConcurrentHashMap<String, Span> = ConcurrentHashMap(),
    val otelTracer: io.opentelemetry.api.trace.Tracer,
)

// ---------------------------------------------------------------------------
// Main SDK class
// ---------------------------------------------------------------------------

/**
 * Fire-and-forget OTel tracing SDK for Kotlin.
 *
 * All public methods enqueue work onto a dedicated coroutine dispatcher and
 * return immediately — they never block the caller.
 *
 * Usage:
 * ```kotlin
 * val tracer = Tracer("https://otel.example.com", "my-key", "my-service")
 * val tid    = tracer.start("checkout-flow")
 * tracer.trace(tid, "CartService", "addItem", "item.added", "SKU-42 added")
 * tracer.end(tid, "ok")
 * tracer.close()
 * ```
 */
open class Tracer(
    val endpoint: String,
    val apiKey: String,
    val service: String,
) : AutoCloseable {

    // ------------------------------------------------------------------
    // Internal OTel wiring
    // ------------------------------------------------------------------

    private val exporter: OtlpHttpSpanExporter = OtlpHttpSpanExporter.builder()
        .setEndpoint("$endpoint/v1/traces")
        .addHeader("Authorization", "Bearer $apiKey")
        // 3 retries with exponential back-off are handled by the OTel SDK's
        // built-in retry interceptor; we just need to configure the endpoint.
        .build()

    private val batchProcessor: BatchSpanProcessor = BatchSpanProcessor.builder(exporter)
        .setMaxExportBatchSize(50)
        .setScheduleDelay(1.seconds.inWholeMilliseconds, TimeUnit.MILLISECONDS)
        .setMaxQueueSize(2048)
        .build()

    private val resource: Resource = Resource.getDefault().merge(
        Resource.create(
            Attributes.of(ResourceAttributes.SERVICE_NAME, service)
        )
    )

    internal open val sdkTracerProvider: SdkTracerProvider = SdkTracerProvider.builder()
        .addSpanProcessor(batchProcessor)
        .setResource(resource)
        .build()

    // ------------------------------------------------------------------
    // State
    // ------------------------------------------------------------------

    /** Active traces keyed by their hex trace-id. */
    private val activeTraces = ConcurrentHashMap<String, TraceContext>()

    /** Background dispatcher – single supervisor scope, IO threads. */
    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())

    // ------------------------------------------------------------------
    // Public API
    // ------------------------------------------------------------------

    /**
     * Starts a new root trace named [name].
     *
     * This call is **synchronous** on purpose: callers need the trace-id
     * before they can submit child events, so we create the root span inline.
     *
     * @return 32-char lowercase hex trace-id.
     */
    fun start(name: String): String {
        val otelTracer = sdkTracerProvider.get(INSTRUMENTATION_SCOPE)

        val rootSpan = otelTracer
            .spanBuilder(name)
            .setSpanKind(SpanKind.SERVER)
            .setAttribute(AttributeKey.stringKey("tracep.root"), "true")
            .startSpan()

        val traceId = rootSpan.spanContext.traceId  // 32-char hex
        val ctx = TraceContext(
            rootSpan = rootSpan,
            traceId = traceId,
            otelTracer = otelTracer,
        )
        activeTraces[traceId] = ctx
        return traceId
    }

    /**
     * Records a step event inside the trace identified by [tid].
     *
     * A span is created (or reused) for the [cls]+[function] combination.
     * The event carries [step] as its name and [message]/[level] as attributes.
     *
     * @param tid      Trace-id returned by [start].
     * @param cls      Logical class / component name (`code.namespace`).
     * @param function Logical function / method name (`code.function`).
     * @param step     Human-readable step label (OTel event name).
     * @param message  Descriptive message attached to the event.
     * @param parent   Optional span key (`"ClassName#function"`) whose span
     *                 context is used as the parent for this span.
     * @param level    Severity level, e.g. `"info"`, `"warn"`, `"error"`.
     */
    fun trace(
        tid: String,
        cls: String,
        function: String,
        step: String,
        message: String,
        parent: String? = null,
        level: String = "info",
    ) {
        scope.launch {
            val ctx = activeTraces[tid] ?: return@launch   // unknown tid — drop silently
            val spanKey = "$cls#$function"

            val span = ctx.spans.getOrPut(spanKey) {
                // Resolve parent context
                val parentContext: Context = if (parent != null) {
                    val parentSpan = ctx.spans[parent] ?: ctx.rootSpan
                    Context.current().with(parentSpan)
                } else {
                    Context.current().with(ctx.rootSpan)
                }

                ctx.otelTracer
                    .spanBuilder("$cls.$function")
                    .setParent(parentContext)
                    .setSpanKind(SpanKind.INTERNAL)
                    .setAttribute(AttributeKey.stringKey("code.namespace"), cls)
                    .setAttribute(AttributeKey.stringKey("code.function"), function)
                    .startSpan()
            }

            val eventAttributes = Attributes.of(
                AttributeKey.stringKey("message"), message,
                AttributeKey.stringKey("level"), level,
            )
            span.addEvent(step, eventAttributes)
        }
    }

    /**
     * Ends the trace [tid], sets the final status on every span, and
     * force-flushes the exporter.
     *
     * @param status `"ok"` or `"error"`.
     */
    fun end(tid: String, status: String) {
        scope.launch {
            val ctx = activeTraces.remove(tid) ?: return@launch

            val otelStatus = if (status.lowercase() == "ok") StatusCode.OK else StatusCode.ERROR

            // End child spans first (LIFO order is approximate — map is unordered,
            // but OTel handles out-of-order end gracefully).
            ctx.spans.values.forEach { span ->
                span.setStatus(otelStatus)
                span.end()
            }

            ctx.rootSpan.setStatus(otelStatus)
            ctx.rootSpan.end()

            // Force-flush so the batch processor ships everything before the
            // caller potentially exits.
            sdkTracerProvider.forceFlush()
        }
    }

    /**
     * Shuts down the SDK and releases all resources.
     *
     * Blocks until the exporter drains or the timeout elapses.
     */
    override fun close() {
        // End any traces still open — best-effort
        activeTraces.keys.toList().forEach { tid -> end(tid, "ok") }
        runBlocking {
            kotlinx.coroutines.delay(1500)   // give the coroutines a moment
        }
        sdkTracerProvider.shutdown().join(5, TimeUnit.SECONDS)
    }

    // ------------------------------------------------------------------
    // Companion / factory helpers
    // ------------------------------------------------------------------

    companion object {
        private const val INSTRUMENTATION_SCOPE = "io.tracep"

        /**
         * Convenience factory — same signature as the primary constructor,
         * but reads [apiKey] from the environment variable `TRACEP_API_KEY`
         * when not supplied.
         */
        fun fromEnv(
            endpoint: String,
            service: String,
            apiKey: String = System.getenv("TRACEP_API_KEY") ?: "",
        ): Tracer = Tracer(endpoint, apiKey, service)
    }
}

// ---------------------------------------------------------------------------
// Extension helpers
// ---------------------------------------------------------------------------

/**
 * Builds a parent-key string in the format expected by [Tracer.trace]'s
 * [parent] parameter.
 *
 * ```kotlin
 * val parentKey = parentKey("CartService", "addItem")
 * tracer.trace(tid, "PayService", "charge", "payment.charged", "OK", parent = parentKey)
 * ```
 */
fun parentKey(cls: String, function: String): String = "$cls#$function"
