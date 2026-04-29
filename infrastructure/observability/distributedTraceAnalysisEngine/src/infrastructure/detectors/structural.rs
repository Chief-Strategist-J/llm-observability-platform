use std::collections::{HashMap, VecDeque};
use crate::domain::trace::Trace;
use crate::domain::ports::{AnomalyDetector, AnomalyScore};

struct DistributionWindow {
    span_counts: VecDeque<f64>,
    depths: VecDeque<f64>,
    window_size: usize,
}

impl DistributionWindow {
    fn new(window_size: usize) -> Self {
        Self {
            span_counts: VecDeque::with_capacity(window_size),
            depths: VecDeque::with_capacity(window_size),
            window_size,
        }
    }

    fn add(&mut self, span_count: f64, depth: f64) {
        if self.span_counts.len() >= self.window_size {
            self.span_counts.pop_front();
            self.depths.pop_front();
        }
        self.span_counts.push_back(span_count);
        self.depths.push_back(depth);
    }

    fn is_ready(&self) -> bool {
        self.span_counts.len() >= self.window_size / 2
    }
}

pub struct StructuralAnomalyDetector {
    cluster_windows: HashMap<i64, DistributionWindow>,
    window_size: usize,
    alpha: f64,
    current_cluster_map: HashMap<String, i64>,
}

impl StructuralAnomalyDetector {
    pub fn new(window_size: usize, alpha: f64) -> Self {
        Self {
            cluster_windows: HashMap::new(),
            window_size,
            alpha,
            current_cluster_map: HashMap::new(),
        }
    }

    pub fn default_config() -> Self {
        Self::new(1000, 0.05)
    }

    pub fn set_cluster_for_trace(&mut self, trace_id: &str, cluster_id: i64) {
        self.current_cluster_map.insert(trace_id.to_string(), cluster_id);
    }

    fn ks_statistic(sample: &VecDeque<f64>, reference_mean: f64, reference_stddev: f64) -> f64 {
        if sample.is_empty() || reference_stddev <= 0.0 {
            return 0.0;
        }

        let n = sample.len() as f64;
        let mut sorted: Vec<f64> = sample.iter().copied().collect();
        sorted.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));

        let mut max_d = 0.0f64;
        for (i, &val) in sorted.iter().enumerate() {
            let empirical_cdf = (i + 1) as f64 / n;
            let z = (val - reference_mean) / reference_stddev;
            let theoretical_cdf = Self::normal_cdf(z);
            let d = (empirical_cdf - theoretical_cdf).abs();
            max_d = max_d.max(d);

            let empirical_cdf_prev = i as f64 / n;
            let d_prev = (empirical_cdf_prev - theoretical_cdf).abs();
            max_d = max_d.max(d_prev);
        }

        max_d
    }

    fn normal_cdf(z: f64) -> f64 {
        0.5 * (1.0 + Self::erf(z / std::f64::consts::SQRT_2))
    }

    fn erf(x: f64) -> f64 {
        let t = 1.0 / (1.0 + 0.3275911 * x.abs());
        let poly = t * (0.254829592 + t * (-0.284496736 + t * (1.421413741 + t * (-1.453152027 + t * 1.061405429))));
        let result = 1.0 - poly * (-x * x).exp();
        if x >= 0.0 { result } else { -result }
    }

    fn ks_critical_value(n: usize, alpha: f64) -> f64 {
        if n == 0 { return f64::MAX; }
        let c = (-0.5 * (alpha / 2.0).ln()).sqrt();
        c / (n as f64).sqrt()
    }

    fn mean(data: &VecDeque<f64>) -> f64 {
        if data.is_empty() { return 0.0; }
        data.iter().sum::<f64>() / data.len() as f64
    }

    fn stddev(data: &VecDeque<f64>) -> f64 {
        if data.len() < 2 { return 1.0; }
        let m = Self::mean(data);
        let variance = data.iter().map(|&x| (x - m).powi(2)).sum::<f64>() / (data.len() as f64 - 1.0);
        variance.sqrt()
    }
}

impl AnomalyDetector for StructuralAnomalyDetector {
    fn detect(&self, trace: &Trace) -> Vec<AnomalyScore> {
        let cluster_id = self.current_cluster_map
            .get(&trace.trace_id.0)
            .copied()
            .unwrap_or(-1);

        if cluster_id < 0 {
            return Vec::new();
        }

        let window = match self.cluster_windows.get(&cluster_id) {
            Some(w) if w.is_ready() => w,
            _ => return Vec::new(),
        };

        let mut scores = Vec::new();

        let ref_mean = Self::mean(&window.span_counts);
        let ref_std = Self::stddev(&window.span_counts);
        if ref_std > 0.0 {
            let _z = ((trace.span_count() as f64) - ref_mean).abs() / ref_std;
        }

        let ks_stat = Self::ks_statistic(&window.span_counts, ref_mean, ref_std);
        let critical = Self::ks_critical_value(window.span_counts.len(), self.alpha);

        if ks_stat > critical {
            scores.push(AnomalyScore {
                signal_name: format!("structural::cluster_{}", cluster_id),
                score: ks_stat / critical,
                threshold: 1.0,
            });
        }

        scores
    }

    fn update_baseline(&mut self, trace: &Trace) {
        let cluster_id = self.current_cluster_map
            .get(&trace.trace_id.0)
            .copied()
            .unwrap_or(-1);

        if cluster_id < 0 { return; }

        self.cluster_windows
            .entry(cluster_id)
            .or_insert_with(|| DistributionWindow::new(self.window_size))
            .add(trace.span_count() as f64, trace.tree.depth as f64);
    }

    fn signal_name(&self) -> &str {
        "structural"
    }
}
