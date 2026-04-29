use std::collections::HashMap;
use crate::domain::trace::{Trace, ServiceOperationKey};
use crate::domain::ports::{AnomalyDetector, AnomalyScore};

struct WelfordState {
    count: u64,
    mean: f64,
    m2: f64,
    ewma_mean: f64,
    ewma_var: f64,
    lambda: f64,
}

impl WelfordState {
    fn new(lambda: f64) -> Self {
        Self { count: 0, mean: 0.0, m2: 0.0, ewma_mean: 0.0, ewma_var: 0.0, lambda }
    }

    fn update(&mut self, value: f64) {
        self.count += 1;
        let delta = value - self.mean;
        self.mean += delta / self.count as f64;
        let delta2 = value - self.mean;
        self.m2 += delta * delta2;

        if self.count == 1 {
            self.ewma_mean = value;
            self.ewma_var = 0.0;
        } else {
            self.ewma_mean = self.lambda * self.ewma_mean + (1.0 - self.lambda) * value;
            let diff = value - self.ewma_mean;
            self.ewma_var = self.lambda * self.ewma_var + (1.0 - self.lambda) * diff * diff;
        }
    }

    fn stddev(&self) -> f64 {
        if self.count < 2 { return f64::MAX; }
        (self.m2 / (self.count as f64 - 1.0)).sqrt()
    }

    fn log_normal_threshold(&self, sigma_multiplier: f64) -> f64 {
        (self.ewma_mean + sigma_multiplier * self.ewma_var.sqrt()).exp()
    }
}

pub struct LatencyAnomalyDetector {
    baselines: HashMap<String, WelfordState>,
    sigma_multiplier: f64,
    lambda: f64,
}

impl LatencyAnomalyDetector {
    pub fn new(sigma_multiplier: f64, lambda: f64) -> Self {
        Self {
            baselines: HashMap::new(),
            sigma_multiplier,
            lambda,
        }
    }

    pub fn default_config() -> Self {
        Self::new(3.0, 0.99)
    }

    fn key_for(service: &str, operation: &str) -> String {
        format!("{}::{}", service, operation)
    }
}

impl AnomalyDetector for LatencyAnomalyDetector {
    fn detect(&self, trace: &Trace) -> Vec<AnomalyScore> {
        let mut scores = Vec::new();

        for span in &trace.spans {
            let key = Self::key_for(&span.service_name, &span.operation_name);
            if let Some(state) = self.baselines.get(&key) {
                if state.count < 10 { continue; }
                let log_latency = (span.duration_ns as f64).ln();
                let threshold = state.ewma_mean + self.sigma_multiplier * state.ewma_var.sqrt();
                let score = if threshold > 0.0 { log_latency / threshold } else { 0.0 };
                if score > 1.0 {
                    scores.push(AnomalyScore {
                        signal_name: format!("latency::{}", key),
                        score: score.min(2.0),
                        threshold: 1.0,
                    });
                }
            }
        }

        scores
    }

    fn update_baseline(&mut self, trace: &Trace) {
        for span in &trace.spans {
            let key = Self::key_for(&span.service_name, &span.operation_name);
            let log_latency = (span.duration_ns as f64).ln();
            self.baselines
                .entry(key)
                .or_insert_with(|| WelfordState::new(self.lambda))
                .update(log_latency);
        }
    }

    fn signal_name(&self) -> &str {
        "latency"
    }
}
