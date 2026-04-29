use serde::{Deserialize, Serialize};
use crate::domain::trace::TraceId;
use crate::domain::fingerprint::TraceFingerprint;
use crate::domain::critical_path::CriticalPath;
use crate::domain::ports::{AnomalyScore, ClusterAssignment};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum DomainEvent {
    TraceAssembled(TraceAssembledEvent),
    AnomalyDetected(AnomalyDetectedEvent),
    ClusterAssigned(ClusterAssignedEvent),
    AnalysisCompleted(AnalysisCompletedEvent),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TraceAssembledEvent {
    pub trace_id: TraceId,
    pub span_count: usize,
    pub is_complete: bool,
    pub timestamp_ns: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AnomalyDetectedEvent {
    pub trace_id: TraceId,
    pub signal_name: String,
    pub score: f64,
    pub timestamp_ns: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ClusterAssignedEvent {
    pub trace_id: TraceId,
    pub cluster_id: i64,
    pub distance: f64,
    pub timestamp_ns: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AnalysisCompletedEvent {
    pub trace_id: TraceId,
    pub timestamp_ns: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AnalysisResult {
    pub trace_id: TraceId,
    pub fingerprint: TraceFingerprint,
    pub cluster_id: i64,
    pub anomaly_scores: Vec<AnalysisAnomalyScore>,
    pub critical_path: CriticalPath,
    pub is_anomalous: bool,
    pub confidence: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AnalysisAnomalyScore {
    pub signal_name: String,
    pub score: f64,
    pub is_anomalous: bool,
}

impl AnalysisResult {
    pub fn build(
        trace_id: TraceId,
        fingerprint: TraceFingerprint,
        cluster_id: i64,
        anomaly_scores: Vec<AnomalyScore>,
        critical_path: CriticalPath,
    ) -> Self {
        let converted: Vec<AnalysisAnomalyScore> = anomaly_scores.iter().map(|s| {
            AnalysisAnomalyScore {
                signal_name: s.signal_name.clone(),
                score: s.score,
                is_anomalous: s.is_anomalous(),
            }
        }).collect();

        let max_score = converted.iter().map(|s| s.score).fold(0.0f64, f64::max);
        let agreeing = converted.iter().filter(|s| s.is_anomalous).count();
        let confidence = if converted.is_empty() { 0.0 } else { agreeing as f64 / converted.len() as f64 };
        let is_anomalous = max_score > 0.8 && confidence > 0.5;

        Self {
            trace_id,
            fingerprint,
            cluster_id,
            anomaly_scores: converted,
            critical_path,
            is_anomalous,
            confidence,
        }
    }
}
