//! Core [`Tracer`] implementation.
//!
//! Every public method is fire-and-forget: the caller is never blocked by
//! network I/O.  All OTel flushing happens via a Tokio runtime that is owned
//! by the [`Tracer`] instance.

use std::{
    collections::HashMap,
    error::Error,
    sync::{Arc, Mutex},
    time::Duration,
};

use opentelemetry::{
    global,
    trace::{
        Span, SpanKind, Status, TraceContextExt, Tracer as OtelTracer,
    },
    Context, KeyValue,
};
use opentelemetry_otlp::WithExportConfig;
use opentelemetry_sdk::{
    runtime,
    trace::{BatchConfig, Config},
};
use tokio::runtime::Runtime;

// ── internal span book-keeping ────────────────────────────────────────────────

/// One active trace: the root span plus every child span created by `trace()`.
struct TraceEntry {
    /// Root span (created by `start()`).
    root_span: opentelemetry_sdk::trace::Span,
    /// Child spans keyed by `"class::function"`.
    child_spans: HashMap<String, opentelemetry_sdk::trace::Span>,
}

// ── public API ────────────────────────────────────────────────────────────────

/// Fire-and-forget OTel tracer.
///
/// Construct once with [`Tracer::new`], then call [`Tracer::start`] /
/// [`Tracer::trace`] / [`Tracer::end`] from any thread.  All spans are
/// exported via OTLP/HTTP JSON to `<endpoint>/v1/traces`.
pub struct Tracer {
    /// OTel tracer.
    otel_tracer: opentelemetry_sdk::trace::Tracer,
    /// All in-flight traces, keyed by trace-id hex string.
    traces: Arc<Mutex<HashMap<String, TraceEntry>>>,
    /// Dedicated Tokio runtime used for async force-flush calls.
    rt: Runtime,
}

impl Tracer {
    // ── constructor ──────────────────────────────────────────────────────────

    /// Create a new [`Tracer`].
    ///
    /// # Arguments
    ///
    /// * `endpoint` – Base URL of the OTLP collector, e.g. `"http://localhost:4318"`.
    ///   `/v1/traces` is appended automatically.
    /// * `api_key`  – Bearer token sent as `Authorization: Bearer <api_key>`.
    /// * `service`  – Logical service name embedded in every span.
    pub fn new(endpoint: &str, api_key: &str, service: &str) -> Result<Self, Box<dyn Error>> {
        // Build the Tokio runtime first; we need it for the OTLP exporter's
        // reqwest HTTP client.
        let rt = Runtime::new()?;

        let traces_url = format!("{}/v1/traces", endpoint.trim_end_matches('/'));
        let auth_header = format!("Bearer {}", api_key);

        // Build the OTLP HTTP exporter.
        let exporter = opentelemetry_otlp::new_exporter()
            .http()
            .with_endpoint(&traces_url)
            .with_headers({
                let mut h = HashMap::new();
                h.insert("Authorization".to_string(), auth_header);
                h
            })
            .with_timeout(Duration::from_secs(10));

        // Batch processor configuration: buffer up to 50 spans, flush every 1 s.
        let batch_config = BatchConfig::default()
            .with_max_export_batch_size(50)
            .with_scheduled_delay(Duration::from_secs(1));

        // Build the TracerProvider and install it inside the Tokio runtime.
        let otel_tracer = rt.block_on(async {
            opentelemetry_otlp::new_pipeline()
                .tracing()
                .with_exporter(exporter)
                .with_trace_config(
                    Config::default().with_resource(
                        opentelemetry_sdk::Resource::new(vec![KeyValue::new(
                            "service.name",
                            service.to_string(),
                        )]),
                    ),
                )
                .with_batch_config(batch_config)
                .install_batch(runtime::Tokio)
        })?;

        // Retrieve the provider (which is an Option).
        let provider = otel_tracer.provider().ok_or("OTel tracer has no provider")?;

        // Register as the global provider so `global::tracer()` works if
        // callers mix APIs; not strictly required for our SDK but good practice.
        global::set_tracer_provider(provider);

        Ok(Self {
            otel_tracer,
            traces: Arc::new(Mutex::new(HashMap::new())),
            rt,
        })
    }

    // ── start ────────────────────────────────────────────────────────────────

    /// Start a new root trace.
    ///
    /// Returns the trace-id as a lower-case hex string (32 characters).
    pub fn start(&self, name: &str) -> String {
        let span = self
            .otel_tracer
            .span_builder(name.to_string())
            .with_kind(SpanKind::Internal)
            .start(&self.otel_tracer);

        let trace_id = span.span_context().trace_id();
        let tid = format!("{:032x}", u128::from_be_bytes(trace_id.to_bytes()));

        let entry = TraceEntry {
            root_span: span,
            child_spans: HashMap::new(),
        };

        self.traces
            .lock()
            .expect("traces mutex poisoned")
            .insert(tid.clone(), entry);

        tid
    }

    // ── trace ────────────────────────────────────────────────────────────────

    /// Add a span event to the trace identified by `tid`.
    ///
    /// * `cls`      – `code.namespace` attribute value (class / module name).
    /// * `function` – `code.function` attribute value.
    /// * `step`     – Name of the OTel span event.
    /// * `message`  – `message` attribute on the span event.
    /// * `parent`   – Optional parent span key (`"class::function"`).  When
    ///                supplied the newly created span is a child of that span.
    /// * `level`    – Log level string, defaults to `"info"`.
    ///
    /// If `tid` is not recognised the call is silently ignored.
    pub fn trace(
        &self,
        tid: &str,
        cls: &str,
        function: &str,
        step: &str,
        message: &str,
        parent: Option<&str>,
        level: Option<&str>,
    ) {
        let level = level.unwrap_or("info").to_string();
        let span_key = format!("{}::{}", cls, function);
        let step = step.to_string();
        let message = message.to_string();
        let cls = cls.to_string();
        let function = function.to_string();

        let mut guard = self.traces.lock().expect("traces mutex poisoned");

        let entry = match guard.get_mut(tid) {
            Some(e) => e,
            None => return, // unknown tid → silently ignore
        };

        // Resolve the OTel parent context.
        let parent_cx: Context = if let Some(parent_key) = parent {
            if let Some(parent_span) = entry.child_spans.get(parent_key) {
                // Attach the parent span's context so the child is linked.
                Context::current().with_remote_span_context(parent_span.span_context().clone())
            } else {
                // Fall back to root span context.
                Context::current().with_remote_span_context(entry.root_span.span_context().clone())
            }
        } else {
            Context::current().with_remote_span_context(entry.root_span.span_context().clone())
        };

        // Find or create the child span for this class+function pair.
        if !entry.child_spans.contains_key(&span_key) {
            let child_span = self
                .otel_tracer
                .span_builder(span_key.clone())
                .with_kind(SpanKind::Internal)
                .start_with_context(&self.otel_tracer, &parent_cx);

            entry.child_spans.insert(span_key.clone(), child_span);
        }

        // Set attributes and add the event on the child span.
        if let Some(span) = entry.child_spans.get_mut(&span_key) {
            span.set_attribute(KeyValue::new("code.namespace", cls));
            span.set_attribute(KeyValue::new("code.function", function));
            span.add_event(
                step,
                vec![
                    KeyValue::new("message", message),
                    KeyValue::new("level", level),
                ],
            );
        }
    }

    // ── end ──────────────────────────────────────────────────────────────────

    /// Finish the trace identified by `tid`.
    ///
    /// * `status` – `"ok"` sets [`Status::Ok`]; anything else sets
    ///              [`Status::Error`].
    ///
    /// All child spans are ended first, then the root span.  A force-flush
    /// is requested so buffered spans reach the exporter promptly.
    ///
    /// If `tid` is not recognised the call is silently ignored.
    pub fn end(&self, tid: &str, status: &str) {
        let entry = {
            let mut guard = self.traces.lock().expect("traces mutex poisoned");
            guard.remove(tid)
        };

        let mut entry = match entry {
            Some(e) => e,
            None => return,
        };

        let otel_status = if status.eq_ignore_ascii_case("ok") {
            Status::Ok
        } else {
            Status::error(status.to_string())
        };

        // End child spans.
        for (_, mut span) in entry.child_spans.drain() {
            span.set_status(otel_status.clone());
            span.end();
        }

        // End root span.
        entry.root_span.set_status(otel_status);
        entry.root_span.end();

        // Force-flush so the batch processor ships queued spans immediately.
        let provider_opt = self.otel_tracer.provider();
        if let Some(provider) = provider_opt {
            self.rt.spawn(async move {
                // Retry loop: 3 attempts with exponential back-off.
                let mut delay = Duration::from_millis(100);
                for attempt in 0..3u32 {
                    match provider.force_flush() {
                        results if results.iter().all(|r| r.is_ok()) => break,
                        _ => {
                            if attempt < 2 {
                                tokio::time::sleep(delay).await;
                                delay *= 2;
                            }
                            // 3rd failure → drop silently
                        }
                    }
                }
            });
        }
    }

    // ── close ────────────────────────────────────────────────────────────────

    /// Gracefully shut down the tracer.
    ///
    /// Flushes remaining spans and shuts down the OTel provider.  Call once
    /// at application exit.
    pub fn close(&self) {
        if let Some(provider) = self.otel_tracer.provider() {
            // Block until flush completes (within 5 s timeout).
            self.rt.block_on(async move {
                let _ = tokio::time::timeout(Duration::from_secs(5), async {
                    let _ = provider.force_flush();
                })
                .await;
            });
        }
        global::shutdown_tracer_provider();
    }
}

// Safety: `Tracer` can be shared across threads. The `Arc<Mutex<…>>` guards
// mutable state; the OTel provider and tracer are internally `Send + Sync`.
unsafe impl Send for Tracer {}
unsafe impl Sync for Tracer {}
