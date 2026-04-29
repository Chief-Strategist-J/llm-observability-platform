use std::sync::Arc;
use tokio::sync::Mutex;
use tracing_subscriber::EnvFilter;

use distributed_trace_analysis_engine::application::assembler::TraceAssembler;
use distributed_trace_analysis_engine::application::processor::TraceProcessor;
use distributed_trace_analysis_engine::infrastructure::collector::InMemoryTraceStore;
use distributed_trace_analysis_engine::infrastructure::collector::OtlpSpanReceiver;
use distributed_trace_analysis_engine::infrastructure::clustering::HdbscanClusterer;
use distributed_trace_analysis_engine::infrastructure::detectors::latency::LatencyAnomalyDetector;
use distributed_trace_analysis_engine::infrastructure::detectors::structural::StructuralAnomalyDetector;
use distributed_trace_analysis_engine::infrastructure::detectors::error::ErrorPropagationDetector;
use distributed_trace_analysis_engine::api::server::{AppState, create_router};

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt()
        .with_env_filter(EnvFilter::from_default_env().add_directive("info".parse().unwrap()))
        .init();

    let assembler = TraceAssembler::default_config();
    let cluster_assigner = Box::new(HdbscanClusterer::default_config());
    let detectors: Vec<Box<dyn distributed_trace_analysis_engine::domain::ports::AnomalyDetector>> = vec![
        Box::new(LatencyAnomalyDetector::default_config()),
        Box::new(StructuralAnomalyDetector::default_config()),
        Box::new(ErrorPropagationDetector::new()),
    ];
    let processor = TraceProcessor::new(cluster_assigner, detectors, 1000);
    let trace_store = Arc::new(InMemoryTraceStore::new());

    let state = Arc::new(AppState {
        assembler: Mutex::new(assembler),
        processor: Mutex::new(processor),
        trace_store,
        results: Mutex::new(Vec::new()),
        receiver: OtlpSpanReceiver::new(),
    });

    let app = create_router(state);

    let bind_addr = std::env::var("DTAE_BIND_ADDR").unwrap_or_else(|_| "0.0.0.0:8090".to_string());
    tracing::info!("starting distributed trace analysis engine on {}", bind_addr);

    let listener = tokio::net::TcpListener::bind(&bind_addr).await.expect("failed to bind");
    axum::serve(listener, app).await.expect("server failed");
}
