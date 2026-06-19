package io.tracep;

import io.opentelemetry.api.common.Attributes;
import io.opentelemetry.api.trace.SpanKind;
import io.opentelemetry.sdk.testing.exporter.InMemorySpanExporter;
import io.opentelemetry.sdk.trace.SdkTracerProvider;
import io.opentelemetry.sdk.trace.data.SpanData;
import io.opentelemetry.sdk.trace.export.SimpleSpanProcessor;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Timeout;

import java.util.List;
import java.util.concurrent.TimeUnit;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Unit tests for {@link Tracer}.
 *
 * <p>Uses {@link InMemorySpanExporter} (from {@code opentelemetry-sdk-testing}) to
 * capture exported spans without any real network traffic.  A fresh {@link Tracer}
 * is injected with a pre-built {@link SdkTracerProvider} via the package-private
 * constructor so we can use Mockito-style assertions on span data.
 */
@Timeout(value = 10, unit = TimeUnit.SECONDS)
class TracerTest {

    private InMemorySpanExporter spanExporter;
    private SdkTracerProvider    testProvider;
    private Tracer               tracer;

    // ── lifecycle ─────────────────────────────────────────────────────────────

    @BeforeEach
    void setUp() {
        spanExporter = InMemorySpanExporter.create();

        // SimpleSpanProcessor exports synchronously – ideal for unit tests
        testProvider = SdkTracerProvider.builder()
                .addSpanProcessor(SimpleSpanProcessor.create(spanExporter))
                .build();

        // Use the package-private constructor to inject the test provider
        TracerOptions opts = TracerOptions.of(
                "http://localhost:4318", "test-key", "test-service");
        tracer = new Tracer(opts, testProvider);
    }

    @AfterEach
    void tearDown() throws Exception {
        tracer.close();
        spanExporter.reset();
    }

    // ── tests ─────────────────────────────────────────────────────────────────

    @Test
    @DisplayName("start() returns a non-null, 32-char hex trace ID")
    void testStartReturnsValidTraceId() {
        String tid = tracer.start("test-trace");

        assertNotNull(tid, "tid must not be null");
        assertFalse(tid.isBlank(), "tid must not be blank");
        assertEquals(32, tid.length(),
                "OTel trace IDs are 128-bit = 32 hex chars, got: " + tid);
        assertTrue(tid.matches("[0-9a-f]{32}"),
                "tid must be lowercase hex, got: " + tid);

        tracer.end(tid, "ok");
    }

    @Test
    @DisplayName("start() creates a root span that is eventually exported")
    void testStartCreatesRootSpan() throws InterruptedException {
        String tid = tracer.start("my-root-span");
        tracer.end(tid, "ok");

        // Give the async executor time to end + flush
        Thread.sleep(300);

        List<SpanData> spans = spanExporter.getFinishedSpanItems();
        assertFalse(spans.isEmpty(), "At least one span should have been exported");

        SpanData root = spans.stream()
                .filter(s -> "my-root-span".equals(s.getName()))
                .findFirst()
                .orElseThrow(() -> new AssertionError("Root span 'my-root-span' not found"));

        assertEquals(SpanKind.SERVER, root.getKind());
    }

    @Test
    @DisplayName("trace() with a known tid succeeds silently and records a span event")
    void testTraceWithKnownTidSucceeds() throws InterruptedException {
        String tid = tracer.start("trace-test");

        // Should not throw
        assertDoesNotThrow(() ->
                tracer.trace(tid, "MyClass", "myMethod", "step-1", "hello world"));

        tracer.end(tid, "ok");
        Thread.sleep(300);

        List<SpanData> spans = spanExporter.getFinishedSpanItems();
        SpanData child = spans.stream()
                .filter(s -> "MyClass.myMethod".equals(s.getName()))
                .findFirst()
                .orElseThrow(() -> new AssertionError("Child span 'MyClass.myMethod' not found"));

        // Verify code.namespace and code.function attributes
        assertEquals("MyClass",  child.getAttributes().get(Tracer.CODE_NAMESPACE));
        assertEquals("myMethod", child.getAttributes().get(Tracer.CODE_FUNCTION));

        // Verify the span event was recorded
        assertFalse(child.getEvents().isEmpty(), "Child span should have at least one event");
        assertEquals("step-1", child.getEvents().get(0).getName());
        assertEquals("hello world",
                child.getEvents().get(0).getAttributes().get(Tracer.ATTR_MESSAGE));
        assertEquals("info",
                child.getEvents().get(0).getAttributes().get(Tracer.ATTR_LEVEL));
    }

    @Test
    @DisplayName("trace() overload with parent + level records correct level")
    void testTraceWithLevelAndParent() throws InterruptedException {
        String tid = tracer.start("level-test");

        // Use a dummy parent span-id (16 hex chars = 64-bit span-id)
        assertDoesNotThrow(() ->
                tracer.trace(tid, "Svc", "process", "checkpoint", "something failed",
                        "0000000000000001", "error"));

        tracer.end(tid, "error");
        Thread.sleep(300);

        List<SpanData> spans = spanExporter.getFinishedSpanItems();
        SpanData child = spans.stream()
                .filter(s -> "Svc.process".equals(s.getName()))
                .findFirst()
                .orElseThrow(() -> new AssertionError("Child span 'Svc.process' not found"));

        assertEquals("error",
                child.getEvents().get(0).getAttributes().get(Tracer.ATTR_LEVEL));
    }

    @Test
    @DisplayName("trace() with an unknown tid is silently ignored (no exception)")
    void testTraceWithUnknownTidIsIgnored() throws InterruptedException {
        assertDoesNotThrow(() ->
                tracer.trace("deadbeefdeadbeefdeadbeefdeadbeef",
                        "Ghost", "nowhere", "step", "should be dropped"));

        // No spans should be created
        Thread.sleep(200);
        assertTrue(spanExporter.getFinishedSpanItems().isEmpty(),
                "No spans should be exported for an unknown tid");
    }

    @Test
    @DisplayName("end() with an unknown tid is silently ignored (no exception)")
    void testEndWithUnknownTidIsIgnored() {
        assertDoesNotThrow(() ->
                tracer.end("cafebabecafebabecafebabecafebabe", "ok"));
    }

    @Test
    @DisplayName("end() with status 'error' exports spans with ERROR status")
    void testEndWithErrorStatus() throws InterruptedException {
        String tid = tracer.start("error-trace");
        tracer.trace(tid, "ErrSvc", "failMethod", "fail-step", "boom");
        tracer.end(tid, "error");
        Thread.sleep(300);

        List<SpanData> spans = spanExporter.getFinishedSpanItems();
        spans.forEach(s ->
                assertEquals(io.opentelemetry.api.trace.StatusCode.ERROR,
                        s.getStatus().getStatusCode(),
                        "All spans should have ERROR status"));
    }

    @Test
    @DisplayName("Multiple start() calls return distinct trace IDs")
    void testMultipleStartsReturnDistinctIds() {
        String tid1 = tracer.start("trace-a");
        String tid2 = tracer.start("trace-b");
        String tid3 = tracer.start("trace-c");

        assertNotEquals(tid1, tid2);
        assertNotEquals(tid2, tid3);
        assertNotEquals(tid1, tid3);

        tracer.end(tid1, "ok");
        tracer.end(tid2, "ok");
        tracer.end(tid3, "ok");
    }

    @Test
    @DisplayName("Same class+function reuses the same child span")
    void testSameClassFunctionReusesChildSpan() throws InterruptedException {
        String tid = tracer.start("reuse-test");
        tracer.trace(tid, "Cls", "fn", "step-a", "first call");
        tracer.trace(tid, "Cls", "fn", "step-b", "second call");
        tracer.end(tid, "ok");
        Thread.sleep(300);

        long childCount = spanExporter.getFinishedSpanItems().stream()
                .filter(s -> "Cls.fn".equals(s.getName()))
                .count();
        assertEquals(1, childCount, "Same class+function should produce exactly one child span");

        long eventCount = spanExporter.getFinishedSpanItems().stream()
                .filter(s -> "Cls.fn".equals(s.getName()))
                .mapToLong(s -> s.getEvents().size())
                .sum();
        assertEquals(2, eventCount, "Child span should have 2 events");
    }

    @Test
    @DisplayName("Tracer is AutoCloseable via try-with-resources")
    void testAutoCloseable() {
        // Should not throw
        assertDoesNotThrow(() -> {
            TracerOptions opts = TracerOptions.of(
                    "http://localhost:4318", "key", "svc");
            try (Tracer t = new Tracer(opts, testProvider)) {
                String tid = t.start("auto-close-trace");
                t.end(tid, "ok");
            }
        });
    }

    // ── helper: allow checked exception in lambda ─────────────────────────────

    @FunctionalInterface
    interface ThrowingRunnable {
        void run() throws Exception;
    }

    private static void assertDoesNotThrow(ThrowingRunnable r) {
        try {
            r.run();
        } catch (Exception e) {
            fail("Unexpected exception: " + e);
        }
    }
}
