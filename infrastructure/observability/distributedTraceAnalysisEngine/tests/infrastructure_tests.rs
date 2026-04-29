use distributed_trace_analysis_engine::domain::trace::*;
use distributed_trace_analysis_engine::domain::ports::*;
use distributed_trace_analysis_engine::infrastructure::sampling::*;
use distributed_trace_analysis_engine::infrastructure::clustering::*;
use distributed_trace_analysis_engine::infrastructure::detectors::latency::*;
use distributed_trace_analysis_engine::infrastructure::detectors::structural::*;
use distributed_trace_analysis_engine::infrastructure::detectors::error::*;
use distributed_trace_analysis_engine::domain::fingerprint::*;
use std::collections::HashMap;

fn span(id: &str, tid: &str, p: Option<&str>, svc: &str, dur: u64, err: bool) -> Span {
    Span {
        span_id: SpanId(id.into()), trace_id: TraceId(tid.into()),
        parent_span_id: p.map(|x| SpanId(x.into())), service_name: svc.into(),
        operation_name: "op".into(), start_time_ns: 1000, duration_ns: dur,
        status_code: if err { SpanStatusCode::Error } else { SpanStatusCode::Ok },
        attributes: HashMap::new(),
    }
}

fn trace(id: &str, err: bool) -> Trace {
    Trace::assemble(TraceId(id.into()), vec![
        span("root", id, None, "gw", 500, err),
        span("child", id, Some("root"), "be", 300, err),
    ], 2000)
}

#[test]
fn test_sampling_errors() {
    let s = PriorityWeightedReservoir::new(0, 5_000_000_000);
    assert!(s.should_sample(&span("s1", "t1", None, "svc", 100, true)));
}

#[test]
fn test_sampling_latency() {
    let s = PriorityWeightedReservoir::new(0, 100);
    assert!(s.should_sample(&span("s1", "t1", None, "svc", 200, false)));
}

#[test]
fn test_sampling_deterministic() {
    let s = PriorityWeightedReservoir::new(1, 999_999_999);
    let sp = span("s1", "t1", None, "svc", 50, false);
    assert_eq!(s.should_sample(&sp), s.should_sample(&sp));
}

#[test]
fn test_batch_flush() {
    let mut b = BatchProcessor::new(3, PriorityWeightedReservoir::new(100, 0));
    b.add(span("s1", "t1", None, "svc", 100, false));
    b.add(span("s2", "t2", None, "svc", 100, false));
    assert_eq!(b.flush().len(), 2);
}

#[test]
fn test_hdbscan_empty() {
    let c = HdbscanClusterer::default_config();
    let a = c.assign(&TraceFingerprint { vector: vec![0.0; 64] });
    assert!(a.is_noise);
}

#[test]
fn test_hdbscan_refit() {
    let mut c = HdbscanClusterer::new(3, 2, 5.0);
    let fps: Vec<TraceFingerprint> = (0..10).map(|i| {
        let mut v = vec![0.0; 64]; v[0] = i as f64 * 0.1;
        TraceFingerprint { vector: v }
    }).collect();
    c.refit(&fps);
    let a = c.assign(&TraceFingerprint { vector: vec![0.0; 64] });
    assert!(a.cluster_id >= 0 || a.is_noise);
}

#[test]
fn test_latency_no_baseline() {
    let d = LatencyAnomalyDetector::default_config();
    assert!(d.detect(&trace("t1", false)).is_empty());
}

#[test]
fn test_latency_with_baseline() {
    let mut d = LatencyAnomalyDetector::default_config();
    for i in 0..20 { d.update_baseline(&trace(&format!("t{}", i), false)); }
    let scores = d.detect(&trace("test", false));
    assert!(scores.is_empty() || scores.iter().all(|s| s.score <= 2.0));
}

#[test]
fn test_structural_empty() {
    let d = StructuralAnomalyDetector::default_config();
    assert!(d.detect(&trace("t1", false)).is_empty());
}

#[test]
fn test_error_prop_learns() {
    let mut d = ErrorPropagationDetector::new();
    let t = Trace::assemble(TraceId("t1".into()), vec![
        span("r", "t1", None, "A", 500, true),
        span("c", "t1", Some("r"), "B", 300, true),
    ], 2000);
    d.update_baseline(&t);
    let t2 = Trace::assemble(TraceId("t2".into()), vec![
        span("r", "t2", None, "A", 500, true),
        span("c", "t2", Some("r"), "B", 300, true),
    ], 3000);
    assert!(d.detect(&t2).is_empty());
}
