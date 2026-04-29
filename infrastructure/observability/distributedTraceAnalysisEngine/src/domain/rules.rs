use crate::domain::trace::{Span, Trace, TraceStatus};

pub trait BusinessRule<T> {
    fn evaluate(&self, input: &T) -> bool;
    fn name(&self) -> &str;
}

pub struct TraceCompletenessRule;

impl BusinessRule<Trace> for TraceCompletenessRule {
    fn evaluate(&self, trace: &Trace) -> bool {
        trace.status == TraceStatus::Complete && trace.span_count() > 0
    }

    fn name(&self) -> &str {
        "trace_completeness"
    }
}

pub struct ErrorTraceRule;

impl BusinessRule<Trace> for ErrorTraceRule {
    fn evaluate(&self, trace: &Trace) -> bool {
        trace.error_count() > 0
    }

    fn name(&self) -> &str {
        "error_trace"
    }
}

pub struct HighLatencyRule {
    pub threshold_ns: u64,
}

impl HighLatencyRule {
    pub fn p99(threshold_ns: u64) -> Self {
        Self { threshold_ns }
    }
}

impl BusinessRule<Trace> for HighLatencyRule {
    fn evaluate(&self, trace: &Trace) -> bool {
        trace.total_duration_ns() > self.threshold_ns
    }

    fn name(&self) -> &str {
        "high_latency"
    }
}

pub struct AnomalyThresholdRule {
    pub score_threshold: f64,
    pub confidence_threshold: f64,
}

impl AnomalyThresholdRule {
    pub fn default_thresholds() -> Self {
        Self {
            score_threshold: 0.8,
            confidence_threshold: 0.5,
        }
    }
}

impl BusinessRule<(f64, f64)> for AnomalyThresholdRule {
    fn evaluate(&self, input: &(f64, f64)) -> bool {
        let (score, confidence) = input;
        *score > self.score_threshold && *confidence > self.confidence_threshold
    }

    fn name(&self) -> &str {
        "anomaly_threshold"
    }
}

pub struct SamplingDecisionRule {
    pub rate_percent: u32,
}

impl SamplingDecisionRule {
    pub fn new(rate_percent: u32) -> Self {
        Self { rate_percent }
    }
}

impl BusinessRule<u64> for SamplingDecisionRule {
    fn evaluate(&self, trace_id_hash: &u64) -> bool {
        (*trace_id_hash % 100) < self.rate_percent as u64
    }

    fn name(&self) -> &str {
        "sampling_decision"
    }
}

pub struct CompositeRule<T> {
    rules: Vec<Box<dyn BusinessRule<T>>>,
    mode: CompositionMode,
    rule_name: String,
}

#[derive(Debug, Clone)]
pub enum CompositionMode {
    Any,
    All,
}

impl<T> CompositeRule<T> {
    pub fn any(name: &str, rules: Vec<Box<dyn BusinessRule<T>>>) -> Self {
        Self { rules, mode: CompositionMode::Any, rule_name: name.to_string() }
    }

    pub fn all(name: &str, rules: Vec<Box<dyn BusinessRule<T>>>) -> Self {
        Self { rules, mode: CompositionMode::All, rule_name: name.to_string() }
    }
}

impl<T> BusinessRule<T> for CompositeRule<T> {
    fn evaluate(&self, input: &T) -> bool {
        match self.mode {
            CompositionMode::Any => self.rules.iter().any(|r| r.evaluate(input)),
            CompositionMode::All => self.rules.iter().all(|r| r.evaluate(input)),
        }
    }

    fn name(&self) -> &str {
        &self.rule_name
    }
}
