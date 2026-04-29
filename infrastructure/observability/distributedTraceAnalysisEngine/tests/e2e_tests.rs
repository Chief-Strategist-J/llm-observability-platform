use distributed_trace_analysis_engine::api::client::TraceAnalysisClient;
use std::time::{SystemTime, UNIX_EPOCH};

fn now_ns() -> u64 {
    SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_nanos() as u64
}

fn create_otlp_span(tid: &str, sid: &str, parent: Option<&str>, _svc: &str, op: &str, start: u64, dur: u64) -> serde_json::Value {
    serde_json::json!({
        "traceId": tid,
        "spanId": sid,
        "parentSpanId": parent,
        "name": op,
        "kind": 1,
        "startTimeUnixNano": start.to_string(),
        "endTimeUnixNano": (start + dur).to_string(),
        "attributes": [],
        "status": { "code": 1 }
    })
}

fn create_otlp_payload(spans: Vec<serde_json::Value>) -> serde_json::Value {
    serde_json::json!({
        "resourceSpans": [{
            "resource": { "attributes": [] },
            "scopeSpans": [{
                "scope": { "name": "test-scope" },
                "spans": spans
            }]
        }]
    })
}

#[tokio::test]
async fn test_e2e_ingestion_and_analysis() {
    let client = TraceAnalysisClient::new("http://localhost:8090");
    
    if client.health().await.is_err() {
        println!("Skipping E2E test: server not running on localhost:8090");
        return;
    }

    let tid = "4bf92f3577b34da6a3ce929d0e0e4736";
    // Set start to 35 seconds ago to ensure it's older than the 30s retention window
    let start = now_ns() - 35_000_000_000;

    let spans = vec![
        create_otlp_span(tid, "0000000000000001", None, "gateway", "GET /user", start, 500_000_000),
        create_otlp_span(tid, "0000000000000002", Some("0000000000000001"), "auth-svc", "validate", start + 10_000, 100_000_000),
        create_otlp_span(tid, "0000000000000003", Some("0000000000000001"), "db-svc", "find_user", start + 110_000_000, 300_000_000),
    ];

    let payload = create_otlp_payload(spans);

    let accepted = client.ingest_otlp(&payload).await.expect("failed to ingest otlp");
    assert_eq!(accepted, 3);

    let flush_res = client.flush().await.expect("failed to flush");
    assert!(flush_res.analysis_results >= 1);

    let results = client.get_results().await.expect("failed to get results");
    let my_result = results.iter().find(|r| r.trace_id.0 == tid).expect("result for trace not found");
    
    assert!(my_result.critical_path.total_duration_ns > 0);
    assert!(!my_result.critical_path.nodes.is_empty());
    
    println!("E2E Test Passed: Trace {} analyzed with {} spans", tid, my_result.critical_path.nodes.len());
}
