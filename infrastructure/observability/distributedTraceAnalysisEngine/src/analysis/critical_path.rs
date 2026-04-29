use std::collections::HashMap;
use crate::domain::trace::Trace;
use crate::domain::critical_path::CriticalPath;

pub struct ClusterCriticalPathAggregator {
    cluster_bottlenecks: HashMap<i64, Vec<ServiceBottleneck>>,
}

#[derive(Debug, Clone)]
pub struct ServiceBottleneck {
    pub service: String,
    pub avg_contribution: f64,
    pub occurrence_count: usize,
}

pub struct CriticalPathTrend {
    pub cluster_id: i64,
    pub bottleneck_service: String,
    pub contribution_history: Vec<f64>,
    pub is_increasing: bool,
}

impl ClusterCriticalPathAggregator {
    pub fn new() -> Self {
        Self { cluster_bottlenecks: HashMap::new() }
    }

    pub fn record(&mut self, cluster_id: i64, critical_path: &CriticalPath) {
        if let Some(ref service) = critical_path.critical_service {
            let bottlenecks = self.cluster_bottlenecks.entry(cluster_id).or_default();
            let max_contribution = critical_path.nodes.iter()
                .filter(|n| &n.service == service)
                .map(|n| n.contribution)
                .fold(0.0f64, f64::max);

            if let Some(existing) = bottlenecks.iter_mut().find(|b| b.service == *service) {
                let total = existing.avg_contribution * existing.occurrence_count as f64 + max_contribution;
                existing.occurrence_count += 1;
                existing.avg_contribution = total / existing.occurrence_count as f64;
            } else {
                bottlenecks.push(ServiceBottleneck {
                    service: service.clone(),
                    avg_contribution: max_contribution,
                    occurrence_count: 1,
                });
            }
        }
    }

    pub fn top_bottleneck(&self, cluster_id: i64) -> Option<&ServiceBottleneck> {
        self.cluster_bottlenecks.get(&cluster_id)
            .and_then(|b| b.iter().max_by(|a, b|
                a.avg_contribution.partial_cmp(&b.avg_contribution).unwrap_or(std::cmp::Ordering::Equal)
            ))
    }

    pub fn all_bottlenecks(&self, cluster_id: i64) -> Vec<&ServiceBottleneck> {
        self.cluster_bottlenecks.get(&cluster_id)
            .map(|b| {
                let mut sorted: Vec<&ServiceBottleneck> = b.iter().collect();
                sorted.sort_by(|a, b|
                    b.avg_contribution.partial_cmp(&a.avg_contribution).unwrap_or(std::cmp::Ordering::Equal)
                );
                sorted
            })
            .unwrap_or_default()
    }
}

impl Default for ClusterCriticalPathAggregator {
    fn default() -> Self {
        Self::new()
    }
}
