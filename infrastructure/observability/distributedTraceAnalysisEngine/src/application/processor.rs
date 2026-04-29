use crate::domain::trace::Trace;
use crate::domain::fingerprint::{TraceFingerprint, FeatureNormalizationState};
use crate::domain::critical_path::CriticalPath;
use crate::domain::events::AnalysisResult;
use crate::domain::ports::{ClusterAssigner, AnomalyDetector, AnomalyScore, ClusterAssignment};

pub struct TraceProcessor {
    normalization_state: FeatureNormalizationState,
    cluster_assigner: Box<dyn ClusterAssigner>,
    detectors: Vec<Box<dyn AnomalyDetector>>,
    traces_since_refit: usize,
    refit_interval: usize,
    fingerprint_buffer: Vec<TraceFingerprint>,
}

impl TraceProcessor {
    pub fn new(
        cluster_assigner: Box<dyn ClusterAssigner>,
        detectors: Vec<Box<dyn AnomalyDetector>>,
        refit_interval: usize,
    ) -> Self {
        Self {
            normalization_state: FeatureNormalizationState::new(),
            cluster_assigner,
            detectors,
            traces_since_refit: 0,
            refit_interval,
            fingerprint_buffer: Vec::new(),
        }
    }

    pub fn process(&mut self, trace: &Trace) -> AnalysisResult {
        let raw_fingerprint = TraceFingerprint::extract(trace);
        self.normalization_state.update(&raw_fingerprint);

        let normalized = raw_fingerprint.normalized(
            &self.normalization_state.means,
            &self.normalization_state.stddevs(),
        );

        let assignment = self.cluster_assigner.assign(&normalized);

        let anomaly_scores = self.run_detectors(trace);

        let critical_path = CriticalPath::compute(trace);

        self.fingerprint_buffer.push(normalized.clone());
        self.traces_since_refit += 1;
        self.maybe_refit();

        for detector in &mut self.detectors {
            detector.update_baseline(trace);
        }

        AnalysisResult::build(
            trace.trace_id.clone(),
            normalized,
            assignment.cluster_id,
            anomaly_scores,
            critical_path,
        )
    }

    pub fn process_batch(&mut self, traces: &[Trace]) -> Vec<AnalysisResult> {
        traces.iter().map(|t| self.process(t)).collect()
    }

    fn run_detectors(&self, trace: &Trace) -> Vec<AnomalyScore> {
        self.detectors.iter().flat_map(|d| d.detect(trace)).collect()
    }

    fn maybe_refit(&mut self) {
        if self.traces_since_refit >= self.refit_interval && !self.fingerprint_buffer.is_empty() {
            self.cluster_assigner.refit(&self.fingerprint_buffer);
            self.fingerprint_buffer.clear();
            self.traces_since_refit = 0;
        }
    }
}
