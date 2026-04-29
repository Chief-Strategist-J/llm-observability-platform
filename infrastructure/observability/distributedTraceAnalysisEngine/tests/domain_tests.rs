use distributed_trace_analysis_engine::domain::trace::*;
use distributed_trace_analysis_engine::domain::fingerprint::*;
use distributed_trace_analysis_engine::domain::critical_path::*;
use distributed_trace_analysis_engine::domain::rules::*;
use distributed_trace_analysis_engine::domain::events::*;
use distributed_trace_analysis_engine::domain::ports::*;
use std::collections::HashMap;

fn make_span(trace_id: &str, span_id: &str, parent: Option<&str>, service: &str, op: &str, start: u64, dur: u64, error: bool) -> Span {
    Span {
        span_id: SpanId(span_id.into()),
        trace_id: TraceId(trace_id.into()),
        parent_span_id: parent.map(|p| SpanId(p.into())),
        service_name: service.into(),
        operation_name: op.into(),
        start_time_ns: start,
        duration_ns: dur,
        status_code: if error { SpanStatusCode::Error } else { SpanStatusCode::Ok },
        attributes: HashMap::new(),
    }
}

fn make_simple_trace() -> Trace {
    let spans = vec![
        make_span("t1", "root", None, "gateway", "GET /api", 1000, 500, false),
        make_span("t1", "child1", Some("root"), "user-svc", "get_user", 1050, 200, false),
        make_span("t1", "child2", Some("root"), "db-svc", "query", 1100, 300, false),
        make_span("t1", "grandchild1", Some("child1"), "cache", "lookup", 1060, 50, false),
    ];
    Trace::assemble(TraceId("t1".into()), spans, 2000)
}

fn make_error_trace() -> Trace {
    let spans = vec![
        make_span("t2", "root", None, "gateway", "POST /pay", 1000, 800, true),
        make_span("t2", "child1", Some("root"), "payment-svc", "charge", 1050, 600, true),
        make_span("t2", "grandchild1", Some("child1"), "stripe-adapter", "api_call", 1100, 400, true),
    ];
    Trace::assemble(TraceId("t2".into()), spans, 2000)
}

#[test]
fn test_span_is_root() {
    let root = make_span("t", "s1", None, "svc", "op", 0, 100, false);
    let child = make_span("t", "s2", Some("s1"), "svc", "op2", 10, 50, false);
    assert!(root.is_root());
    assert!(!child.is_root());
}

#[test]
fn test_span_end_time() {
    let span = make_span("t", "s1", None, "svc", "op", 1000, 500, false);
    assert_eq!(span.end_time_ns(), 1500);
}

#[test]
fn test_trace_assembly_complete() {
    let trace = make_simple_trace();
    assert_eq!(trace.status, TraceStatus::Complete);
    assert_eq!(trace.span_count(), 4);
    assert!(trace.root_span().is_some());
    assert_eq!(trace.root_span().unwrap().span_id, SpanId("root".into()));
}

#[test]
fn test_trace_assembly_orphaned() {
    let spans = vec![
        make_span("t3", "c1", Some("missing_root"), "svc", "op", 1000, 100, false),
        make_span("t3", "c2", Some("missing_root"), "svc", "op2", 1050, 50, false),
    ];
    let trace = Trace::assemble(TraceId("t3".into()), spans, 2000);
    assert_eq!(trace.status, TraceStatus::Orphaned);
    assert!(trace.root_span().is_none());
}

#[test]
fn test_trace_tree_depth() {
    let trace = make_simple_trace();
    assert_eq!(trace.tree.depth, 3);
}

#[test]
fn test_trace_tree_width() {
    let trace = make_simple_trace();
    assert!(trace.tree.width >= 2);
}

#[test]
fn test_trace_service_count() {
    let trace = make_simple_trace();
    assert_eq!(trace.service_count(), 4);
}

#[test]
fn test_trace_error_count() {
    let trace = make_error_trace();
    assert_eq!(trace.error_count(), 3);

    let normal = make_simple_trace();
    assert_eq!(normal.error_count(), 0);
}

#[test]
fn test_self_time_computation() {
    let trace = make_simple_trace();
    let root_self = trace.self_time_ns(&SpanId("root".into()));
    assert!(root_self < trace.total_duration_ns());
}

#[test]
fn test_children_of() {
    let trace = make_simple_trace();
    let children = trace.children_of(&SpanId("root".into()));
    assert_eq!(children.len(), 2);
}

#[test]
fn test_fingerprint_extraction() {
    let trace = make_simple_trace();
    let fp = TraceFingerprint::extract(&trace);
    assert_eq!(fp.vector.len(), FEATURE_DIMENSION);
    assert!(fp.vector[0] > 0.0);
}

#[test]
fn test_fingerprint_normalization() {
    let trace = make_simple_trace();
    let fp = TraceFingerprint::extract(&trace);
    let means = vec![0.0; FEATURE_DIMENSION];
    let stddevs = vec![1.0; FEATURE_DIMENSION];
    let normalized = fp.normalized(&means, &stddevs);
    assert_eq!(normalized.vector.len(), FEATURE_DIMENSION);
}

#[test]
fn test_fingerprint_distance() {
    let t1 = make_simple_trace();
    let t2 = make_error_trace();
    let fp1 = TraceFingerprint::extract(&t1);
    let fp2 = TraceFingerprint::extract(&t2);
    let dist = fp1.euclidean_distance(&fp2);
    assert!(dist > 0.0);
    assert_eq!(fp1.euclidean_distance(&fp1), 0.0);
}

#[test]
fn test_normalization_state_welford() {
    let mut state = FeatureNormalizationState::new();
    let trace = make_simple_trace();
    let fp = TraceFingerprint::extract(&trace);
    state.update(&fp);
    state.update(&fp);
    let stddevs = state.stddevs();
    assert_eq!(stddevs.len(), FEATURE_DIMENSION);
}

#[test]
fn test_critical_path_simple_trace() {
    let trace = make_simple_trace();
    let cp = CriticalPath::compute(&trace);
    assert!(!cp.nodes.is_empty());
    assert!(cp.total_duration_ns > 0);
}

#[test]
fn test_critical_path_contribution() {
    let trace = make_simple_trace();
    let cp = CriticalPath::compute(&trace);
    let total_contribution: f64 = cp.nodes.iter().map(|n| n.contribution).sum();
    assert!(total_contribution > 0.0);
}

#[test]
fn test_critical_path_empty_trace() {
    let trace = Trace::assemble(TraceId("empty".into()), vec![], 0);
    let cp = CriticalPath::compute(&trace);
    assert!(cp.nodes.is_empty());
    assert_eq!(cp.total_duration_ns, 0);
}

#[test]
fn test_completeness_rule() {
    let rule = TraceCompletenessRule;
    let complete = make_simple_trace();
    assert!(rule.evaluate(&complete));
    assert_eq!(rule.name(), "trace_completeness");

    let orphan = Trace::assemble(
        TraceId("orphan".into()),
        vec![make_span("orphan", "c1", Some("missing"), "svc", "op", 0, 100, false)],
        0,
    );
    assert!(!rule.evaluate(&orphan));
}

#[test]
fn test_error_trace_rule() {
    let rule = ErrorTraceRule;
    assert!(rule.evaluate(&make_error_trace()));
    assert!(!rule.evaluate(&make_simple_trace()));
}

#[test]
fn test_high_latency_rule() {
    let rule = HighLatencyRule::p99(400);
    assert!(rule.evaluate(&make_simple_trace()));

    let rule_high = HighLatencyRule::p99(1_000_000);
    assert!(!rule_high.evaluate(&make_simple_trace()));
}

#[test]
fn test_anomaly_threshold_rule() {
    let rule = AnomalyThresholdRule::default_thresholds();
    assert!(rule.evaluate(&(0.9, 0.6)));
    assert!(!rule.evaluate(&(0.7, 0.6)));
    assert!(!rule.evaluate(&(0.9, 0.3)));
}

#[test]
fn test_sampling_decision_rule() {
    let rule = SamplingDecisionRule::new(50);
    let sampled_count = (0u64..100).filter(|h| rule.evaluate(h)).count();
    assert_eq!(sampled_count, 50);
}

#[test]
fn test_composite_rule_any() {
    let rules: Vec<Box<dyn BusinessRule<Trace>>> = vec![
        Box::new(ErrorTraceRule),
        Box::new(HighLatencyRule::p99(1_000_000)),
    ];
    let composite = CompositeRule::any("error_or_high_latency", rules);
    assert!(composite.evaluate(&make_error_trace()));
    assert!(!composite.evaluate(&make_simple_trace()));
}

#[test]
fn test_composite_rule_all() {
    let rules: Vec<Box<dyn BusinessRule<Trace>>> = vec![
        Box::new(TraceCompletenessRule),
        Box::new(ErrorTraceRule),
    ];
    let composite = CompositeRule::all("complete_and_error", rules);
    assert!(composite.evaluate(&make_error_trace()));
    assert!(!composite.evaluate(&make_simple_trace()));
}

#[test]
fn test_analysis_result_build() {
    let scores = vec![
        AnomalyScore { signal_name: "latency".into(), score: 0.9, threshold: 0.8 },
        AnomalyScore { signal_name: "structural".into(), score: 0.85, threshold: 0.8 },
        AnomalyScore { signal_name: "error_prop".into(), score: 0.3, threshold: 0.8 },
    ];
    let trace = make_simple_trace();
    let fp = TraceFingerprint::extract(&trace);
    let cp = CriticalPath::compute(&trace);
    let result = AnalysisResult::build(trace.trace_id.clone(), fp, 0, scores, cp);
    assert_eq!(result.anomaly_scores.len(), 3);
    assert!(result.confidence > 0.0);
}

#[test]
fn test_analysis_result_not_anomalous_low_score() {
    let scores = vec![
        AnomalyScore { signal_name: "latency".into(), score: 0.5, threshold: 0.8 },
    ];
    let trace = make_simple_trace();
    let fp = TraceFingerprint::extract(&trace);
    let cp = CriticalPath::compute(&trace);
    let result = AnalysisResult::build(trace.trace_id.clone(), fp, 0, scores, cp);
    assert!(!result.is_anomalous);
}
