use serde::{Deserialize, Serialize};
use crate::domain::trace::{Trace, SpanId};
use petgraph::graph::{DiGraph, NodeIndex};
use petgraph::algo::toposort;
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CriticalPathNode {
    pub span_id: SpanId,
    pub service: String,
    pub operation: String,
    pub self_time_ns: u64,
    pub contribution: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CriticalPath {
    pub nodes: Vec<CriticalPathNode>,
    pub total_duration_ns: u64,
    pub critical_service: Option<String>,
    pub optimization_opportunity: bool,
}

impl CriticalPath {
    pub fn compute(trace: &Trace) -> Self {
        let (dag, _node_map, span_map) = Self::build_dag(trace);

        let sorted = match toposort(&dag, None) {
            Ok(s) => s,
            Err(_) => return Self::empty(),
        };

        let dist = Self::longest_path_dp(&dag, &sorted);

        let terminal = sorted.iter()
            .max_by(|&&a, &&b| {
                dist[a.index()].partial_cmp(&dist[b.index()]).unwrap_or(std::cmp::Ordering::Equal)
            })
            .copied();

        let path_nodes = match terminal {
            Some(t) => Self::reconstruct_path(trace, &dag, &dist, t, &span_map),
            None => Vec::new(),
        };

        let total_duration: u64 = path_nodes.iter().map(|n| n.self_time_ns).sum();

        let critical_service = path_nodes.iter()
            .max_by(|a, b| a.contribution.partial_cmp(&b.contribution).unwrap_or(std::cmp::Ordering::Equal))
            .map(|n| n.service.clone());

        let top_contribution = path_nodes.iter()
            .map(|n| n.contribution)
            .fold(0.0f64, f64::max);

        Self {
            nodes: path_nodes,
            total_duration_ns: total_duration,
            critical_service,
            optimization_opportunity: top_contribution > 0.5,
        }
    }

    fn build_dag(trace: &Trace) -> (DiGraph<SpanId, ()>, HashMap<SpanId, NodeIndex>, HashMap<NodeIndex, SpanId>) {
        let mut dag = DiGraph::new();
        let mut node_map: HashMap<SpanId, NodeIndex> = HashMap::new();
        let mut span_map: HashMap<NodeIndex, SpanId> = HashMap::new();

        for span in &trace.spans {
            let idx = dag.add_node(span.span_id.clone());
            node_map.insert(span.span_id.clone(), idx);
            span_map.insert(idx, span.span_id.clone());
        }

        for span in &trace.spans {
            if let Some(ref parent_id) = span.parent_span_id {
                if let (Some(&parent_idx), Some(&child_idx)) = (node_map.get(parent_id), node_map.get(&span.span_id)) {
                    dag.add_edge(parent_idx, child_idx, ());
                }
            }
        }

        (dag, node_map, span_map)
    }

    fn longest_path_dp(dag: &DiGraph<SpanId, ()>, sorted: &[NodeIndex]) -> Vec<f64> {
        let mut dist = vec![0.0f64; dag.node_count()];

        for &node in sorted {
            let _span_id = &dag[node];
            let node_weight = dist[node.index()];
            for neighbor in dag.neighbors(node) {
                let edge_weight = 1.0;
                let new_dist = node_weight + edge_weight;
                if new_dist > dist[neighbor.index()] {
                    dist[neighbor.index()] = new_dist;
                }
            }
        }

        dist
    }

    fn reconstruct_path(
        trace: &Trace,
        dag: &DiGraph<SpanId, ()>,
        dist: &[f64],
        terminal: NodeIndex,
        span_map: &HashMap<NodeIndex, SpanId>,
    ) -> Vec<CriticalPathNode> {
        let mut path = Vec::new();
        let mut current = Some(terminal);
        let total: u64 = trace.total_duration_ns();

        while let Some(node_idx) = current {
            if let Some(span_id) = span_map.get(&node_idx) {
                if let Some(span) = trace.span_by_id(span_id) {
                    let self_time = trace.self_time_ns(span_id);
                    let contribution = if total > 0 { self_time as f64 / total as f64 } else { 0.0 };
                    path.push(CriticalPathNode {
                        span_id: span_id.clone(),
                        service: span.service_name.clone(),
                        operation: span.operation_name.clone(),
                        self_time_ns: self_time,
                        contribution,
                    });
                }
            }

            let predecessors: Vec<NodeIndex> = dag.neighbors_directed(node_idx, petgraph::Direction::Incoming).collect();
            current = predecessors.into_iter()
                .max_by(|&a, &b| dist[a.index()].partial_cmp(&dist[b.index()]).unwrap_or(std::cmp::Ordering::Equal));
        }

        path.reverse();
        path
    }

    fn empty() -> Self {
        Self {
            nodes: Vec::new(),
            total_duration_ns: 0,
            critical_service: None,
            optimization_opportunity: false,
        }
    }
}
