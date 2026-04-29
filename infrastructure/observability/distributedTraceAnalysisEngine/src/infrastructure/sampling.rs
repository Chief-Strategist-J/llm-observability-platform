use crate::domain::trace::Span;
use crate::domain::ports::SamplingStrategy;
use crate::domain::rules::{BusinessRule, ErrorTraceRule, HighLatencyRule, SamplingDecisionRule};
use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};

pub struct PriorityWeightedReservoir {
    always_sample_rules: Vec<Box<dyn AlwaysSampleCheck>>,
    probabilistic_rate: u32,
}

trait AlwaysSampleCheck: Send + Sync {
    fn should_always_sample(&self, span: &Span) -> bool;
}

struct ErrorSpanCheck;
impl AlwaysSampleCheck for ErrorSpanCheck {
    fn should_always_sample(&self, span: &Span) -> bool {
        span.is_error()
    }
}

struct HighLatencySpanCheck {
    threshold_ns: u64,
}

impl AlwaysSampleCheck for HighLatencySpanCheck {
    fn should_always_sample(&self, span: &Span) -> bool {
        span.duration_ns > self.threshold_ns
    }
}

impl PriorityWeightedReservoir {
    pub fn new(probabilistic_rate: u32, latency_threshold_ns: u64) -> Self {
        let always_sample_rules: Vec<Box<dyn AlwaysSampleCheck>> = vec![
            Box::new(ErrorSpanCheck),
            Box::new(HighLatencySpanCheck { threshold_ns: latency_threshold_ns }),
        ];
        Self { always_sample_rules, probabilistic_rate }
    }

    pub fn default_config() -> Self {
        Self::new(1, 5_000_000_000)
    }

    fn deterministic_hash(trace_id: &str) -> u64 {
        let mut hasher = DefaultHasher::new();
        trace_id.hash(&mut hasher);
        hasher.finish()
    }
}

impl SamplingStrategy for PriorityWeightedReservoir {
    fn should_sample(&self, span: &Span) -> bool {
        for rule in &self.always_sample_rules {
            if rule.should_always_sample(span) {
                return true;
            }
        }
        let hash = Self::deterministic_hash(&span.trace_id.0);
        (hash % 100) < self.probabilistic_rate as u64
    }
}

pub struct BatchProcessor {
    batch: Vec<Span>,
    max_batch_size: usize,
    sampling: PriorityWeightedReservoir,
}

impl BatchProcessor {
    pub fn new(max_batch_size: usize, sampling: PriorityWeightedReservoir) -> Self {
        Self {
            batch: Vec::new(),
            max_batch_size,
            sampling,
        }
    }

    pub fn default_config() -> Self {
        Self::new(1024, PriorityWeightedReservoir::default_config())
    }

    pub fn add(&mut self, span: Span) -> Option<Vec<Span>> {
        if self.sampling.should_sample(&span) {
            self.batch.push(span);
        }
        if self.batch.len() >= self.max_batch_size {
            Some(self.flush())
        } else {
            None
        }
    }

    pub fn flush(&mut self) -> Vec<Span> {
        std::mem::take(&mut self.batch)
    }

    pub fn pending_count(&self) -> usize {
        self.batch.len()
    }
}
