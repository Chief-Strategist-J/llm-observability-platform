use std::collections::{HashMap, HashSet};
use crate::domain::trace::{Trace, ServicePairKey};
use crate::domain::ports::{AnomalyDetector, AnomalyScore};

pub struct ErrorPropagationDetector {
    known_propagations: HashSet<String>,
    propagation_counts: HashMap<String, PropagationBaseline>,
}

struct PropagationBaseline {
    total_co_occurrences: u64,
    error_propagations: u64,
}

impl PropagationBaseline {
    fn new() -> Self {
        Self { total_co_occurrences: 0, error_propagations: 0 }
    }

    fn probability(&self) -> f64 {
        if self.total_co_occurrences == 0 { return 0.0; }
        self.error_propagations as f64 / self.total_co_occurrences as f64
    }
}

impl ErrorPropagationDetector {
    pub fn new() -> Self {
        Self {
            known_propagations: HashSet::new(),
            propagation_counts: HashMap::new(),
        }
    }

    fn extract_error_propagations(trace: &Trace) -> Vec<(String, String)> {
        let mut propagations = Vec::new();

        for span in &trace.spans {
            if !span.is_error() { continue; }

            if let Some(ref parent_id) = span.parent_span_id {
                if let Some(parent) = trace.span_by_id(parent_id) {
                    if parent.is_error() && parent.service_name != span.service_name {
                        propagations.push((
                            parent.service_name.clone(),
                            span.service_name.clone(),
                        ));
                    }
                }
            }
        }

        propagations
    }

    fn pair_key(source: &str, target: &str) -> String {
        format!("{}→{}", source, target)
    }
}

impl Default for ErrorPropagationDetector {
    fn default() -> Self {
        Self::new()
    }
}

impl AnomalyDetector for ErrorPropagationDetector {
    fn detect(&self, trace: &Trace) -> Vec<AnomalyScore> {
        let propagations = Self::extract_error_propagations(trace);
        let mut scores = Vec::new();

        for (source, target) in &propagations {
            let key = Self::pair_key(source, target);
            if !self.known_propagations.contains(&key) {
                scores.push(AnomalyScore {
                    signal_name: format!("error_propagation::{}", key),
                    score: 1.0,
                    threshold: 0.8,
                });
            }
        }

        scores
    }

    fn update_baseline(&mut self, trace: &Trace) {
        let error_services: HashSet<&String> = trace.spans.iter()
            .filter(|s| s.is_error())
            .map(|s| &s.service_name)
            .collect();

        let all_services: HashSet<&String> = trace.spans.iter()
            .map(|s| &s.service_name)
            .collect();

        for a in &all_services {
            for b in &all_services {
                if a == b { continue; }
                let key = Self::pair_key(a, b);
                let baseline = self.propagation_counts.entry(key.clone()).or_insert_with(PropagationBaseline::new);
                baseline.total_co_occurrences += 1;
                if error_services.contains(a) && error_services.contains(b) {
                    baseline.error_propagations += 1;
                }
            }
        }

        let propagations = Self::extract_error_propagations(trace);
        for (source, target) in propagations {
            self.known_propagations.insert(Self::pair_key(&source, &target));
        }
    }

    fn signal_name(&self) -> &str {
        "error_propagation"
    }
}
