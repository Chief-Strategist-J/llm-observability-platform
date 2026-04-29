use serde::{Deserialize, Serialize};
use crate::domain::trace::{Trace, SpanId};
use std::collections::HashSet;

pub const FEATURE_DIMENSION: usize = 64;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TraceFingerprint {
    pub vector: Vec<f64>,
}

impl TraceFingerprint {
    pub fn extract(trace: &Trace) -> Self {
        let mut raw = Vec::with_capacity(FEATURE_DIMENSION);
        Self::append_structural_features(trace, &mut raw);
        Self::append_timing_features(trace, &mut raw);
        Self::append_error_features(trace, &mut raw);
        raw.resize(FEATURE_DIMENSION, 0.0);
        Self { vector: raw }
    }

    pub fn normalized(&self, means: &[f64], stddevs: &[f64]) -> Self {
        let vector = self.vector.iter().enumerate().map(|(i, &v)| {
            let mean = means.get(i).copied().unwrap_or(0.0);
            let std = stddevs.get(i).copied().unwrap_or(1.0);
            if std.abs() < f64::EPSILON { 0.0 } else { (v - mean) / std }
        }).collect();
        Self { vector }
    }

    pub fn euclidean_distance(&self, other: &Self) -> f64 {
        self.vector.iter().zip(other.vector.iter())
            .map(|(a, b)| (a - b).powi(2))
            .sum::<f64>()
            .sqrt()
    }

    fn append_structural_features(trace: &Trace, out: &mut Vec<f64>) {
        out.push(trace.span_count() as f64);
        out.push(trace.tree.depth as f64);
        out.push(trace.tree.width as f64);
        out.push(trace.service_count() as f64);
        out.push(trace.operation_sequence_hash() as f64);
    }

    fn append_timing_features(trace: &Trace, out: &mut Vec<f64>) {
        let total_duration = trace.total_duration_ns() as f64;
        out.push(total_duration);

        let services: HashSet<&String> = trace.spans.iter().map(|s| &s.service_name).collect();
        for service in &services {
            let self_time: u64 = trace.spans.iter()
                .filter(|s| &s.service_name == *service)
                .map(|s| trace.self_time_ns(&s.span_id))
                .sum();
            out.push(self_time as f64);
        }

        let critical_path_duration = Self::estimate_critical_path_duration(trace);
        let critical_path_ratio = if total_duration > 0.0 {
            critical_path_duration / total_duration
        } else {
            0.0
        };
        out.push(critical_path_ratio);

        let service_count = trace.service_count() as f64;
        let total_work: f64 = trace.spans.iter().map(|s| s.duration_ns as f64).sum();
        let parallel_efficiency = if critical_path_duration > 0.0 && service_count > 0.0 {
            total_work / (critical_path_duration * service_count)
        } else {
            0.0
        };
        out.push(parallel_efficiency);
    }

    fn append_error_features(trace: &Trace, out: &mut Vec<f64>) {
        out.push(trace.error_count() as f64);

        let error_depth = trace.spans.iter()
            .filter(|s| s.is_error())
            .map(|s| Self::span_depth(trace, &s.span_id))
            .max()
            .unwrap_or(0);
        out.push(error_depth as f64);

        let first_error_service = trace.spans.iter()
            .filter(|s| s.is_error())
            .min_by_key(|s| s.start_time_ns)
            .map(|s| {
                let mut hasher = std::collections::hash_map::DefaultHasher::new();
                std::hash::Hash::hash(&s.service_name, &mut hasher);
                std::hash::Hasher::finish(&hasher) as f64
            })
            .unwrap_or(0.0);
        out.push(first_error_service);

        let error_propagated = Self::detect_error_propagation(trace);
        out.push(if error_propagated { 1.0 } else { 0.0 });
    }

    fn span_depth(trace: &Trace, span_id: &SpanId) -> usize {
        let mut depth = 0usize;
        let mut current = span_id.clone();
        loop {
            match trace.span_by_id(&current).and_then(|s| s.parent_span_id.clone()) {
                Some(parent) => {
                    depth += 1;
                    current = parent;
                }
                None => break,
            }
        }
        depth
    }

    fn detect_error_propagation(trace: &Trace) -> bool {
        for span in &trace.spans {
            if !span.is_error() {
                continue;
            }
            if let Some(ref parent_id) = span.parent_span_id {
                if let Some(parent) = trace.span_by_id(parent_id) {
                    if parent.is_error() && parent.service_name != span.service_name {
                        return true;
                    }
                }
            }
        }
        false
    }

    fn estimate_critical_path_duration(trace: &Trace) -> f64 {
        match trace.tree.root_id {
            Some(ref root) => Self::critical_path_recursive(trace, root),
            None => 0.0,
        }
    }

    fn critical_path_recursive(trace: &Trace, span_id: &SpanId) -> f64 {
        let self_time = trace.self_time_ns(span_id) as f64;
        let max_child = trace.children_of(span_id).iter()
            .map(|c| Self::critical_path_recursive(trace, &c.span_id))
            .fold(0.0f64, f64::max);
        self_time + max_child
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FeatureNormalizationState {
    pub count: u64,
    pub means: Vec<f64>,
    pub m2: Vec<f64>,
}

impl FeatureNormalizationState {
    pub fn new() -> Self {
        Self {
            count: 0,
            means: vec![0.0; FEATURE_DIMENSION],
            m2: vec![0.0; FEATURE_DIMENSION],
        }
    }

    pub fn update(&mut self, fingerprint: &TraceFingerprint) {
        self.count += 1;
        let n = self.count as f64;
        for (i, &val) in fingerprint.vector.iter().enumerate() {
            if i >= FEATURE_DIMENSION { break; }
            let delta = val - self.means[i];
            self.means[i] += delta / n;
            let delta2 = val - self.means[i];
            self.m2[i] += delta * delta2;
        }
    }

    pub fn stddevs(&self) -> Vec<f64> {
        if self.count < 2 {
            return vec![1.0; FEATURE_DIMENSION];
        }
        self.m2.iter().map(|&m| (m / (self.count as f64 - 1.0)).sqrt()).collect()
    }
}

impl Default for FeatureNormalizationState {
    fn default() -> Self {
        Self::new()
    }
}
