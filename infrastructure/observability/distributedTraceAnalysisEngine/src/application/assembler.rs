use std::collections::HashMap;
use crate::domain::trace::{Span, Trace, TraceId, TraceStatus};

pub struct TraceAssembler {
    buffers: HashMap<TraceId, SpanBuffer>,
    window_duration_ns: u64,
    orphan_timeout_ns: u64,
}

struct SpanBuffer {
    spans: Vec<Span>,
    first_seen_ns: u64,
    has_root: bool,
}

impl SpanBuffer {
    fn new(first_seen_ns: u64) -> Self {
        Self {
            spans: Vec::new(),
            first_seen_ns,
            has_root: false,
        }
    }

    fn add(&mut self, span: Span) {
        if span.is_root() {
            self.has_root = true;
        }
        self.spans.push(span);
    }
}

pub struct AssemblyOutput {
    pub complete_traces: Vec<Trace>,
    pub partial_traces: Vec<Trace>,
}

impl TraceAssembler {
    pub fn new(window_duration_ns: u64, orphan_timeout_ns: u64) -> Self {
        Self {
            buffers: HashMap::new(),
            window_duration_ns,
            orphan_timeout_ns,
        }
    }

    pub fn default_config() -> Self {
        let window_30s = 30_000_000_000u64;
        let orphan_60s = 60_000_000_000u64;
        Self::new(window_30s, orphan_60s)
    }

    pub fn ingest(&mut self, span: Span) {
        let trace_id = span.trace_id.clone();
        let now = span.start_time_ns;
        self.buffers
            .entry(trace_id)
            .or_insert_with(|| SpanBuffer::new(now))
            .add(span);
    }

    pub fn ingest_batch(&mut self, spans: Vec<Span>) {
        for span in spans {
            self.ingest(span);
        }
    }

    pub fn flush(&mut self, current_time_ns: u64) -> AssemblyOutput {
        let watermark = current_time_ns.saturating_sub(self.window_duration_ns);
        let orphan_watermark = current_time_ns.saturating_sub(self.orphan_timeout_ns);

        let mut complete_traces = Vec::new();
        let mut partial_traces = Vec::new();
        let mut to_remove = Vec::new();

        for (trace_id, buffer) in &self.buffers {
            if buffer.has_root && buffer.first_seen_ns <= watermark {
                let trace = Trace::assemble(trace_id.clone(), buffer.spans.clone(), current_time_ns);
                complete_traces.push(trace);
                to_remove.push(trace_id.clone());
            } else if !buffer.has_root && buffer.first_seen_ns <= orphan_watermark {
                let mut trace = Trace::assemble(trace_id.clone(), buffer.spans.clone(), current_time_ns);
                trace.status = TraceStatus::Partial;
                partial_traces.push(trace);
                to_remove.push(trace_id.clone());
            }
        }

        for id in to_remove {
            self.buffers.remove(&id);
        }

        AssemblyOutput { complete_traces, partial_traces }
    }

    pub fn pending_count(&self) -> usize {
        self.buffers.len()
    }
}
