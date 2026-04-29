use distributed_trace_analysis_engine::domain::trace::*;
use distributed_trace_analysis_engine::application::assembler::*;
use std::collections::HashMap;

fn span(trace_id: &str, span_id: &str, parent: Option<&str>, start: u64) -> Span {
    Span {
        span_id: SpanId(span_id.into()),
        trace_id: TraceId(trace_id.into()),
        parent_span_id: parent.map(|p| SpanId(p.into())),
        service_name: "test-svc".into(),
        operation_name: "test-op".into(),
        start_time_ns: start,
        duration_ns: 100,
        status_code: SpanStatusCode::Ok,
        attributes: HashMap::new(),
    }
}

#[test]
fn test_assembler_complete_trace() {
    let mut assembler = TraceAssembler::new(100, 200);
    assembler.ingest(span("t1", "root", None, 1000));
    assembler.ingest(span("t1", "child", Some("root"), 1020));
    let output = assembler.flush(1200);
    assert_eq!(output.complete_traces.len(), 1);
    assert_eq!(output.complete_traces[0].span_count(), 2);
    assert_eq!(output.partial_traces.len(), 0);
}

#[test]
fn test_assembler_within_window_not_flushed() {
    let mut assembler = TraceAssembler::new(100, 200);
    assembler.ingest(span("t1", "root", None, 1000));
    let output = assembler.flush(1050);
    assert_eq!(output.complete_traces.len(), 0);
    assert_eq!(assembler.pending_count(), 1);
}

#[test]
fn test_assembler_orphan_trace() {
    let mut assembler = TraceAssembler::new(100, 200);
    assembler.ingest(span("t1", "child1", Some("missing"), 1000));
    assembler.ingest(span("t1", "child2", Some("missing"), 1020));
    let output = assembler.flush(1300);
    assert_eq!(output.complete_traces.len(), 0);
    assert_eq!(output.partial_traces.len(), 1);
    assert_eq!(output.partial_traces[0].status, TraceStatus::Partial);
}

#[test]
fn test_assembler_multiple_traces() {
    let mut assembler = TraceAssembler::new(100, 200);
    assembler.ingest(span("t1", "root1", None, 1000));
    assembler.ingest(span("t2", "root2", None, 1010));
    assembler.ingest(span("t1", "child1", Some("root1"), 1020));
    let output = assembler.flush(1200);
    assert_eq!(output.complete_traces.len(), 2);
}

#[test]
fn test_assembler_batch_ingest() {
    let mut assembler = TraceAssembler::new(100, 200);
    let spans = vec![
        span("t1", "root", None, 1000),
        span("t1", "c1", Some("root"), 1020),
        span("t1", "c2", Some("root"), 1030),
    ];
    assembler.ingest_batch(spans);
    let output = assembler.flush(1200);
    assert_eq!(output.complete_traces.len(), 1);
    assert_eq!(output.complete_traces[0].span_count(), 3);
}

#[test]
fn test_assembler_pending_count() {
    let mut assembler = TraceAssembler::new(100, 200);
    assert_eq!(assembler.pending_count(), 0);
    assembler.ingest(span("t1", "root", None, 1000));
    assert_eq!(assembler.pending_count(), 1);
    assembler.ingest(span("t2", "root2", None, 1000));
    assert_eq!(assembler.pending_count(), 2);
    assembler.flush(1200);
    assert_eq!(assembler.pending_count(), 0);
}

#[test]
fn test_assembler_default_config() {
    let assembler = TraceAssembler::default_config();
    assert_eq!(assembler.pending_count(), 0);
}
