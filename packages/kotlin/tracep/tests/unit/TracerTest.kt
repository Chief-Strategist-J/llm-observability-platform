package io.tracep

import io.mockk.every
import io.mockk.mockk
import io.mockk.slot
import io.mockk.verify
import io.opentelemetry.api.common.AttributeKey
import io.opentelemetry.api.common.Attributes
import io.opentelemetry.api.trace.Span
import io.opentelemetry.api.trace.SpanBuilder
import io.opentelemetry.api.trace.SpanKind
import io.opentelemetry.api.trace.StatusCode
import io.opentelemetry.sdk.testing.exporter.InMemorySpanExporter
import io.opentelemetry.sdk.trace.SdkTracerProvider
import io.opentelemetry.sdk.trace.export.SimpleSpanProcessor
import org.junit.jupiter.api.AfterEach
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertNotNull
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.TestInstance
import java.util.concurrent.TimeUnit

@TestInstance(TestInstance.Lifecycle.PER_METHOD)
class TracerTest {

    // -----------------------------------------------------------------------
    // Helpers: build a Tracer backed by an in-memory exporter so tests
    // don't need a real OTLP endpoint.
    // -----------------------------------------------------------------------

    private lateinit var inMemoryExporter: InMemorySpanExporter
    private lateinit var testProvider: SdkTracerProvider
    private lateinit var tracer: Tracer

    @BeforeEach
    fun setUp() {
        inMemoryExporter = InMemorySpanExporter.create()
        testProvider = SdkTracerProvider.builder()
            .addSpanProcessor(SimpleSpanProcessor.create(inMemoryExporter))
            .build()

        // We can construct the Tracer normally; in tests we swap out its
        // sdkTracerProvider by direct field manipulation is not ideal,
        // so instead we leverage a thin subclass factory.
        tracer = TracerTestFactory.create(testProvider)
    }

    @AfterEach
    fun tearDown() {
        runCatching { tracer.close() }
        testProvider.shutdown().join(3, TimeUnit.SECONDS)
        inMemoryExporter.reset()
    }

    // -----------------------------------------------------------------------
    // Test: start() returns a non-empty, 32-char hex trace-id
    // -----------------------------------------------------------------------

    @Test
    fun `startReturnsNonEmptyTid`() {
        val tid = tracer.start("test-flow")
        assertTrue(tid.isNotBlank(), "tid must not be blank")
        assertEquals(32, tid.length, "tid must be 32 hex chars (W3C trace-id)")
        assertTrue(tid.all { it.isDigit() || it in 'a'..'f' }, "tid must be lowercase hex")
    }

    // -----------------------------------------------------------------------
    // Test: trace() with an unknown tid is silently ignored (no exception)
    // -----------------------------------------------------------------------

    @Test
    fun `traceWithUnknownTidIsIgnored`() {
        // Should not throw – fire and forget drops unknown tids
        tracer.trace(
            tid = "00000000000000000000000000000000",
            cls = "SomeClass",
            function = "someMethod",
            step = "step.one",
            message = "should be ignored",
        )
        Thread.sleep(200)   // let coroutine settle
        // No spans should have been recorded
        assertTrue(inMemoryExporter.finishedSpanItems.isEmpty())
    }

    // -----------------------------------------------------------------------
    // Test: end() with an unknown tid is silently ignored (no exception)
    // -----------------------------------------------------------------------

    @Test
    fun `endWithUnknownTidIsIgnored`() {
        // Should not throw
        tracer.end("deadbeefdeadbeefdeadbeefdeadbeef", "ok")
        Thread.sleep(200)
        assertTrue(inMemoryExporter.finishedSpanItems.isEmpty())
    }

    // -----------------------------------------------------------------------
    // Test: trace() records an event on the span
    // -----------------------------------------------------------------------

    @Test
    fun `traceAddsEventToSpan`() {
        val tid = tracer.start("event-test-flow")

        tracer.trace(
            tid = tid,
            cls = "OrderService",
            function = "placeOrder",
            step = "order.created",
            message = "Order #99 created",
            level = "info",
        )

        // end flushes everything
        tracer.end(tid, "ok")

        // Give the coroutine + simple processor a moment to finish
        Thread.sleep(500)

        val spans = inMemoryExporter.finishedSpanItems
        assertTrue(spans.isNotEmpty(), "At least one span should have been exported")

        // Find the child span (not the root)
        val childSpan = spans.firstOrNull { it.name == "OrderService.placeOrder" }
        assertNotNull(childSpan, "Child span 'OrderService.placeOrder' should exist")

        val events = childSpan!!.events
        assertTrue(events.isNotEmpty(), "Child span must have at least one event")

        val evt = events.first { it.name == "order.created" }
        assertEquals("Order #99 created", evt.attributes.get(AttributeKey.stringKey("message")))
        assertEquals("info", evt.attributes.get(AttributeKey.stringKey("level")))

        // Verify code.namespace and code.function attributes
        assertEquals("OrderService", childSpan.attributes.get(AttributeKey.stringKey("code.namespace")))
        assertEquals("placeOrder", childSpan.attributes.get(AttributeKey.stringKey("code.function")))
    }

    // -----------------------------------------------------------------------
    // Test: MockK-based verification that start() interacts with SdkTracerProvider
    // -----------------------------------------------------------------------

    @Test
    fun `startCallsTracerProviderGet`() {
        // Use MockK to verify the interaction
        val mockProvider = mockk<SdkTracerProvider>(relaxed = true)
        val mockOtelTracer = mockk<io.opentelemetry.api.trace.Tracer>(relaxed = true)
        val mockSpanBuilder = mockk<SpanBuilder>(relaxed = true)
        val mockSpan = mockk<Span>(relaxed = true)
        val mockSpanContext = mockk<io.opentelemetry.api.trace.SpanContext>(relaxed = true)

        every { mockProvider.get(any<String>()) } returns mockOtelTracer
        every { mockOtelTracer.spanBuilder(any()) } returns mockSpanBuilder
        every { mockSpanBuilder.setSpanKind(any()) } returns mockSpanBuilder
        every { mockSpanBuilder.setAttribute(any<AttributeKey<String>>(), any()) } returns mockSpanBuilder
        every { mockSpanBuilder.startSpan() } returns mockSpan
        every { mockSpan.spanContext } returns mockSpanContext
        every { mockSpanContext.traceId } returns "abcdef12abcdef12abcdef12abcdef12"

        val mockTracer = TracerTestFactory.create(mockProvider)
        val tid = mockTracer.start("mocked-flow")

        assertEquals("abcdef12abcdef12abcdef12abcdef12", tid)
        verify(exactly = 1) { mockProvider.get("io.tracep") }
    }
}

// ---------------------------------------------------------------------------
// Internal test factory — creates a Tracer whose sdkTracerProvider is
// replaced with a caller-supplied instance (in-memory or mock).
// ---------------------------------------------------------------------------

internal object TracerTestFactory {
    fun create(provider: SdkTracerProvider): Tracer {
        // Build a real Tracer but override its provider via subclassing
        return object : Tracer(
            endpoint = "http://localhost:4318",
            apiKey = "test-key",
            service = "test-service",
        ) {
            // Shadow the provider property so all getOrCreate calls go through
            // the supplied test provider.
            override val sdkTracerProvider: SdkTracerProvider = provider
        }
    }
}
