use distributed_trace_analysis_engine::domain::trace::*;
use distributed_trace_analysis_engine::domain::ports::*;
use distributed_trace_analysis_engine::application::assembler::*;
use distributed_trace_analysis_engine::application::processor::*;
use distributed_trace_analysis_engine::infrastructure::clustering::*;
use distributed_trace_analysis_engine::infrastructure::detectors::latency::*;
use distributed_trace_analysis_engine::infrastructure::detectors::error::*;
use distributed_trace_analysis_engine::domain::fingerprint::*;
use std::collections::HashMap;

fn span(id: &str, tid: &str, p: Option<&str>, svc: &str, dur: u64) -> Span {
    Span {
        span_id: SpanId(id.into()), trace_id: TraceId(tid.into()),
        parent_span_id: p.map(|x| SpanId(x.into())), service_name: svc.into(),
        operation_name: "op".into(), start_time_ns: 1000, duration_ns: dur,
        status_code: SpanStatusCode::Ok, attributes: HashMap::new(),
    }
}

#[test]
fn test_full_pipeline() {
    let mut assembler = TraceAssembler::new(100, 200);
    assembler.ingest(span("root", "t1", None, "gateway", 500));
    assembler.ingest(span("c1", "t1", Some("root"), "user-svc", 200));
    assembler.ingest(span("c2", "t1", Some("root"), "db-svc", 300));

    let output = assembler.flush(1200);
    assert_eq!(output.complete_traces.len(), 1);

    let clusterer = Box::new(HdbscanClusterer::default_config());
    let detectors: Vec<Box<dyn AnomalyDetector>> = vec![
        Box::new(LatencyAnomalyDetector::default_config()),
        Box::new(ErrorPropagationDetector::new()),
    ];
    let mut processor = TraceProcessor::new(clusterer, detectors, 1000);

    let result = processor.process(&output.complete_traces[0]);
    assert_eq!(result.trace_id, TraceId("t1".into()));
    assert_eq!(result.fingerprint.vector.len(), FEATURE_DIMENSION);
    assert!(!result.critical_path.nodes.is_empty());
}

#[test]
fn test_pipeline_batch_processing() {
    let mut assembler = TraceAssembler::new(100, 200);
    for i in 0..5 {
        let tid = format!("t{}", i);
        assembler.ingest(span("root", &tid, None, "gw", 500));
        assembler.ingest(span("c1", &tid, Some("root"), "be", 200));
    }

    let output = assembler.flush(1200);
    assert_eq!(output.complete_traces.len(), 5);

    let clusterer = Box::new(HdbscanClusterer::default_config());
    let detectors: Vec<Box<dyn AnomalyDetector>> = vec![
        Box::new(LatencyAnomalyDetector::default_config()),
    ];
    let mut processor = TraceProcessor::new(clusterer, detectors, 1000);
    let results = processor.process_batch(&output.complete_traces);
    assert_eq!(results.len(), 5);
}
