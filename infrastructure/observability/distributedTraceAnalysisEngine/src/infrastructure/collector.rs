use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::Mutex;
use async_trait::async_trait;
use crate::domain::trace::{Span, Trace, TraceId, SpanId, SpanStatusCode};
use crate::domain::ports::{SpanReceiver, TraceStore, PortError};

pub struct OtlpSpanReceiver {
    buffer: Arc<Mutex<Vec<Span>>>,
}

impl OtlpSpanReceiver {
    pub fn new() -> Self {
        Self { buffer: Arc::new(Mutex::new(Vec::new())) }
    }

    pub async fn push_spans(&self, spans: Vec<Span>) {
        let mut buf = self.buffer.lock().await;
        buf.extend(spans);
    }

    pub fn from_otlp_json(payload: &serde_json::Value) -> Result<Vec<Span>, PortError> {
        let resource_spans = payload.get("resourceSpans")
            .and_then(|v| v.as_array())
            .ok_or_else(|| PortError::Serialization("missing resourceSpans".into()))?;

        let mut spans = Vec::new();

        for rs in resource_spans {
            let service_name = Self::extract_service_name(rs);
            let scope_spans = rs.get("scopeSpans")
                .and_then(|v| v.as_array())
                .unwrap_or(&Vec::new())
                .clone();

            for ss in &scope_spans {
                let span_list = ss.get("spans")
                    .and_then(|v| v.as_array())
                    .unwrap_or(&Vec::new())
                    .clone();

                for raw_span in &span_list {
                    if let Some(span) = Self::parse_span(raw_span, &service_name) {
                        spans.push(span);
                    }
                }
            }
        }

        Ok(spans)
    }

    fn extract_service_name(resource_span: &serde_json::Value) -> String {
        resource_span.get("resource")
            .and_then(|r| r.get("attributes"))
            .and_then(|a| a.as_array())
            .and_then(|attrs| {
                attrs.iter().find(|attr| {
                    attr.get("key").and_then(|k| k.as_str()) == Some("service.name")
                })
            })
            .and_then(|attr| attr.get("value").and_then(|v| v.get("stringValue")).and_then(|s| s.as_str()))
            .unwrap_or("unknown")
            .to_string()
    }

    fn parse_span(raw: &serde_json::Value, service_name: &str) -> Option<Span> {
        let span_id = raw.get("spanId")?.as_str()?;
        let trace_id = raw.get("traceId")?.as_str()?;
        let parent_span_id = raw.get("parentSpanId").and_then(|v| v.as_str()).filter(|s| !s.is_empty());
        let operation_name = raw.get("name").and_then(|v| v.as_str()).unwrap_or("unknown");
        let start_time = raw.get("startTimeUnixNano")
            .and_then(|v| v.as_str().or_else(|| v.as_u64().map(|_| "")).and_then(|_| v.as_str()))
            .and_then(|s| s.parse::<u64>().ok())
            .or_else(|| raw.get("startTimeUnixNano").and_then(|v| v.as_u64()))
            .unwrap_or(0);
        let end_time = raw.get("endTimeUnixNano")
            .and_then(|v| v.as_str().and_then(|s| s.parse::<u64>().ok()).or_else(|| v.as_u64()))
            .unwrap_or(start_time);

        let status_code = raw.get("status")
            .and_then(|s| s.get("code"))
            .and_then(|c| c.as_u64())
            .map(|code| match code {
                1 => SpanStatusCode::Ok,
                2 => SpanStatusCode::Error,
                _ => SpanStatusCode::Unset,
            })
            .unwrap_or(SpanStatusCode::Unset);

        let mut attributes = HashMap::new();
        if let Some(attrs) = raw.get("attributes").and_then(|a| a.as_array()) {
            for attr in attrs {
                if let (Some(key), Some(value)) = (
                    attr.get("key").and_then(|k| k.as_str()),
                    attr.get("value").and_then(|v| v.get("stringValue")).and_then(|s| s.as_str()),
                ) {
                    attributes.insert(key.to_string(), value.to_string());
                }
            }
        }

        Some(Span {
            span_id: SpanId(span_id.to_string()),
            trace_id: TraceId(trace_id.to_string()),
            parent_span_id: parent_span_id.map(|s| SpanId(s.to_string())),
            service_name: service_name.to_string(),
            operation_name: operation_name.to_string(),
            start_time_ns: start_time,
            duration_ns: end_time.saturating_sub(start_time),
            status_code,
            attributes,
        })
    }
}

impl Default for OtlpSpanReceiver {
    fn default() -> Self {
        Self::new()
    }
}

#[async_trait]
impl SpanReceiver for OtlpSpanReceiver {
    async fn receive(&self) -> Result<Vec<Span>, PortError> {
        let mut buf = self.buffer.lock().await;
        let spans = std::mem::take(&mut *buf);
        Ok(spans)
    }
}

pub struct InMemoryTraceStore {
    traces: Arc<Mutex<HashMap<TraceId, Trace>>>,
}

impl InMemoryTraceStore {
    pub fn new() -> Self {
        Self { traces: Arc::new(Mutex::new(HashMap::new())) }
    }
}

impl Default for InMemoryTraceStore {
    fn default() -> Self {
        Self::new()
    }
}

#[async_trait]
impl TraceStore for InMemoryTraceStore {
    async fn store(&self, trace: &Trace) -> Result<(), PortError> {
        let mut store = self.traces.lock().await;
        store.insert(trace.trace_id.clone(), trace.clone());
        Ok(())
    }

    async fn load(&self, trace_id: &TraceId) -> Result<Option<Trace>, PortError> {
        let store = self.traces.lock().await;
        Ok(store.get(trace_id).cloned())
    }

    async fn list_recent(&self, limit: usize) -> Result<Vec<Trace>, PortError> {
        let store = self.traces.lock().await;
        let mut traces: Vec<Trace> = store.values().cloned().collect();
        traces.sort_by(|a, b| b.assembled_at_ns.cmp(&a.assembled_at_ns));
        traces.truncate(limit);
        Ok(traces)
    }
}
