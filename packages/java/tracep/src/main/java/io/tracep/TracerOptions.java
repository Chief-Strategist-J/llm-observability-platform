package io.tracep;

import java.time.Duration;
import java.util.Objects;

/**
 * Immutable configuration for {@link Tracer}.
 *
 * <p>Use the nested {@link Builder} to construct instances:
 * <pre>{@code
 * TracerOptions opts = TracerOptions.builder()
 *     .endpoint("http://collector:4318")
 *     .apiKey("my-key")
 *     .service("my-service")
 *     .maxExportBatchSize(50)
 *     .scheduleDelay(Duration.ofSeconds(1))
 *     .build();
 * }</pre>
 */
public final class TracerOptions {

    // ── required ──────────────────────────────────────────────────────────────
    private final String endpoint;
    private final String apiKey;
    private final String service;

    // ── batch / flush ─────────────────────────────────────────────────────────
    private final int maxExportBatchSize;
    private final Duration scheduleDelay;

    // ── retry ─────────────────────────────────────────────────────────────────
    private final int maxRetries;

    private TracerOptions(Builder b) {
        this.endpoint            = Objects.requireNonNull(b.endpoint,  "endpoint must not be null");
        this.apiKey              = Objects.requireNonNull(b.apiKey,    "apiKey must not be null");
        this.service             = Objects.requireNonNull(b.service,   "service must not be null");
        this.maxExportBatchSize  = b.maxExportBatchSize;
        this.scheduleDelay       = b.scheduleDelay;
        this.maxRetries          = b.maxRetries;
    }

    // ── accessors ─────────────────────────────────────────────────────────────

    /** OTLP collector base URL (e.g. {@code http://localhost:4318}). */
    public String getEndpoint() { return endpoint; }

    /** Bearer token sent in the {@code Authorization} header. */
    public String getApiKey() { return apiKey; }

    /** Logical service name attached to every span as {@code service.name}. */
    public String getService() { return service; }

    /** Maximum number of spans in a single export batch (default: 50). */
    public int getMaxExportBatchSize() { return maxExportBatchSize; }

    /** How often the {@link io.opentelemetry.sdk.trace.export.BatchSpanProcessor}
     *  flushes pending spans (default: 1 s). */
    public Duration getScheduleDelay() { return scheduleDelay; }

    /** Maximum retry attempts before a batch is silently dropped (default: 3). */
    public int getMaxRetries() { return maxRetries; }

    // ── factory ───────────────────────────────────────────────────────────────

    /**
     * Convenience factory – equivalent to calling {@code builder().endpoint(…).apiKey(…)
     * .service(…).build()} with default values for everything else.
     */
    public static TracerOptions of(String endpoint, String apiKey, String service) {
        return builder().endpoint(endpoint).apiKey(apiKey).service(service).build();
    }

    public static Builder builder() { return new Builder(); }

    // ── Builder ───────────────────────────────────────────────────────────────

    public static final class Builder {
        private String   endpoint;
        private String   apiKey;
        private String   service;
        private int      maxExportBatchSize = 50;
        private Duration scheduleDelay      = Duration.ofSeconds(1);
        private int      maxRetries         = 3;

        private Builder() {}

        public Builder endpoint(String endpoint) {
            this.endpoint = endpoint;
            return this;
        }

        public Builder apiKey(String apiKey) {
            this.apiKey = apiKey;
            return this;
        }

        public Builder service(String service) {
            this.service = service;
            return this;
        }

        /**
         * Maximum number of spans buffered before an export is forced.
         * Must be between 1 and 2048.
         */
        public Builder maxExportBatchSize(int size) {
            if (size < 1 || size > 2048) {
                throw new IllegalArgumentException("maxExportBatchSize must be between 1 and 2048");
            }
            this.maxExportBatchSize = size;
            return this;
        }

        /**
         * How long the batch processor waits before flushing.
         * Must be positive.
         */
        public Builder scheduleDelay(Duration delay) {
            Objects.requireNonNull(delay, "scheduleDelay must not be null");
            if (delay.isNegative() || delay.isZero()) {
                throw new IllegalArgumentException("scheduleDelay must be positive");
            }
            this.scheduleDelay = delay;
            return this;
        }

        /**
         * Number of retry attempts on transient export failures.
         * Set to 0 to disable retries.
         */
        public Builder maxRetries(int maxRetries) {
            if (maxRetries < 0) {
                throw new IllegalArgumentException("maxRetries must be >= 0");
            }
            this.maxRetries = maxRetries;
            return this;
        }

        public TracerOptions build() { return new TracerOptions(this); }
    }
}
