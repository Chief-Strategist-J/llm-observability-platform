use async_trait::async_trait;
use crate::domain::trace::{Span, Trace, TraceId};
use crate::domain::fingerprint::TraceFingerprint;
use crate::domain::events::AnalysisResult;

#[async_trait]
pub trait SpanReceiver: Send + Sync {
    async fn receive(&self) -> Result<Vec<Span>, PortError>;
}

#[async_trait]
pub trait TraceStore: Send + Sync {
    async fn store(&self, trace: &Trace) -> Result<(), PortError>;
    async fn load(&self, trace_id: &TraceId) -> Result<Option<Trace>, PortError>;
    async fn list_recent(&self, limit: usize) -> Result<Vec<Trace>, PortError>;
}

#[async_trait]
pub trait SpanBuffer: Send + Sync {
    async fn add_span(&self, span: Span) -> Result<(), PortError>;
    async fn flush_window(&self, watermark_ns: u64) -> Result<Vec<(TraceId, Vec<Span>)>, PortError>;
}

#[async_trait]
pub trait ClusterAssigner: Send + Sync {
    fn assign(&self, fingerprint: &TraceFingerprint) -> ClusterAssignment;
    fn refit(&mut self, fingerprints: &[TraceFingerprint]);
}

#[derive(Debug, Clone)]
pub struct ClusterAssignment {
    pub cluster_id: i64,
    pub distance: f64,
    pub is_noise: bool,
}

impl ClusterAssignment {
    pub fn noise(distance: f64) -> Self {
        Self { cluster_id: -1, distance, is_noise: true }
    }

    pub fn assigned(cluster_id: i64, distance: f64) -> Self {
        Self { cluster_id, distance, is_noise: false }
    }
}

#[derive(Debug, Clone)]
pub struct AnomalyScore {
    pub signal_name: String,
    pub score: f64,
    pub threshold: f64,
}

impl AnomalyScore {
    pub fn is_anomalous(&self) -> bool {
        self.score > self.threshold
    }
}

pub trait AnomalyDetector: Send + Sync {
    fn detect(&self, trace: &Trace) -> Vec<AnomalyScore>;
    fn update_baseline(&mut self, trace: &Trace);
    fn signal_name(&self) -> &str;
}

#[async_trait]
pub trait AnalysisResultSink: Send + Sync {
    async fn emit(&self, result: &AnalysisResult) -> Result<(), PortError>;
}

pub trait SamplingStrategy: Send + Sync {
    fn should_sample(&self, span: &Span) -> bool;
}

#[derive(Debug, thiserror::Error)]
pub enum PortError {
    #[error("connection failed: {0}")]
    ConnectionFailed(String),
    #[error("timeout: {0}")]
    Timeout(String),
    #[error("serialization error: {0}")]
    Serialization(String),
    #[error("not found: {0}")]
    NotFound(String),
    #[error("internal: {0}")]
    Internal(String),
}
