use std::sync::Arc;
use tokio::sync::Mutex;
use axum::{Router, Json, extract::State, extract::Path, routing::{get, post}, http::StatusCode};
use serde::{Deserialize, Serialize};
use tower_http::cors::CorsLayer;

use crate::domain::trace::{Span, TraceId};
use crate::domain::events::AnalysisResult;
use crate::domain::ports::TraceStore;
use crate::application::assembler::TraceAssembler;
use crate::application::processor::TraceProcessor;
use crate::infrastructure::collector::OtlpSpanReceiver;

pub struct AppState {
    pub assembler: Mutex<TraceAssembler>,
    pub processor: Mutex<TraceProcessor>,
    pub trace_store: Arc<dyn TraceStore>,
    pub results: Mutex<Vec<AnalysisResult>>,
    pub receiver: OtlpSpanReceiver,
}

#[derive(Serialize)]
struct HealthResponse {
    status: String,
    version: String,
}

#[derive(Serialize)]
struct IngestResponse {
    accepted: usize,
    message: String,
}

#[derive(Serialize)]
struct FlushResponse {
    complete_traces: usize,
    partial_traces: usize,
    analysis_results: usize,
}

#[derive(Serialize)]
struct AnalysisResultResponse {
    results: Vec<AnalysisResult>,
}

#[derive(Serialize)]
struct TraceResponse {
    trace_id: String,
    span_count: usize,
    status: String,
    duration_ns: u64,
}

pub fn create_router(state: Arc<AppState>) -> Router {
    Router::new()
        .route("/health", get(health_handler))
        .route("/api/v1/spans", post(ingest_spans_handler))
        .route("/api/v1/spans/otlp", post(ingest_otlp_handler))
        .route("/api/v1/flush", post(flush_handler))
        .route("/api/v1/analysis/results", get(get_results_handler))
        .route("/api/v1/analysis/results/{trace_id}", get(get_result_by_trace_handler))
        .route("/api/v1/traces", get(list_traces_handler))
        .route("/api/v1/traces/{trace_id}", get(get_trace_handler))
        .layer(CorsLayer::permissive())
        .with_state(state)
}

async fn health_handler() -> Json<HealthResponse> {
    Json(HealthResponse {
        status: "healthy".into(),
        version: env!("CARGO_PKG_VERSION").into(),
    })
}

async fn ingest_spans_handler(
    State(state): State<Arc<AppState>>,
    Json(spans): Json<Vec<Span>>,
) -> (StatusCode, Json<IngestResponse>) {
    let count = spans.len();
    let mut assembler = state.assembler.lock().await;
    assembler.ingest_batch(spans);
    (StatusCode::ACCEPTED, Json(IngestResponse {
        accepted: count,
        message: "spans accepted".into(),
    }))
}

async fn ingest_otlp_handler(
    State(state): State<Arc<AppState>>,
    Json(payload): Json<serde_json::Value>,
) -> Result<(StatusCode, Json<IngestResponse>), (StatusCode, String)> {
    let spans = OtlpSpanReceiver::from_otlp_json(&payload)
        .map_err(|e| (StatusCode::BAD_REQUEST, e.to_string()))?;
    let count = spans.len();
    let mut assembler = state.assembler.lock().await;
    assembler.ingest_batch(spans);
    Ok((StatusCode::ACCEPTED, Json(IngestResponse {
        accepted: count,
        message: "otlp spans accepted".into(),
    })))
}

async fn flush_handler(
    State(state): State<Arc<AppState>>,
) -> Json<FlushResponse> {
    let now = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default()
        .as_nanos() as u64;

    let output = {
        let mut assembler = state.assembler.lock().await;
        assembler.flush(now)
    };

    let complete_count = output.complete_traces.len();
    let partial_count = output.partial_traces.len();

    let mut all_traces = output.complete_traces;
    all_traces.extend(output.partial_traces);

    let mut analysis_results = Vec::new();
    {
        let mut processor = state.processor.lock().await;
        for trace in &all_traces {
            let result = processor.process(trace);
            analysis_results.push(result);
        }
    }

    for trace in &all_traces {
        let _ = state.trace_store.store(trace).await;
    }

    let result_count = analysis_results.len();
    {
        let mut results = state.results.lock().await;
        results.extend(analysis_results);
    }

    Json(FlushResponse {
        complete_traces: complete_count,
        partial_traces: partial_count,
        analysis_results: result_count,
    })
}

async fn get_results_handler(
    State(state): State<Arc<AppState>>,
) -> Json<AnalysisResultResponse> {
    let results = state.results.lock().await;
    Json(AnalysisResultResponse { results: results.clone() })
}

async fn get_result_by_trace_handler(
    State(state): State<Arc<AppState>>,
    Path(trace_id): Path<String>,
) -> Result<Json<AnalysisResult>, StatusCode> {
    let results = state.results.lock().await;
    results.iter()
        .find(|r| r.trace_id.0 == trace_id)
        .cloned()
        .map(Json)
        .ok_or(StatusCode::NOT_FOUND)
}

async fn list_traces_handler(
    State(state): State<Arc<AppState>>,
) -> Json<Vec<TraceResponse>> {
    let traces = state.trace_store.list_recent(100).await.unwrap_or_default();
    let response: Vec<TraceResponse> = traces.iter().map(|t| TraceResponse {
        trace_id: t.trace_id.0.clone(),
        span_count: t.span_count(),
        status: format!("{:?}", t.status),
        duration_ns: t.total_duration_ns(),
    }).collect();
    Json(response)
}

async fn get_trace_handler(
    State(state): State<Arc<AppState>>,
    Path(trace_id): Path<String>,
) -> Result<Json<crate::domain::trace::Trace>, StatusCode> {
    let trace = state.trace_store.load(&TraceId(trace_id)).await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
    trace.map(Json).ok_or(StatusCode::NOT_FOUND)
}
