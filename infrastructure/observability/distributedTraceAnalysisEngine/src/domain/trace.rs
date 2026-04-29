use std::collections::HashMap;
use serde::{Deserialize, Serialize};
use uuid::Uuid;
use ordered_float::OrderedFloat;

#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct SpanId(pub String);

#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct TraceId(pub String);

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum SpanStatusCode {
    Ok,
    Error,
    Unset,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Span {
    pub span_id: SpanId,
    pub trace_id: TraceId,
    pub parent_span_id: Option<SpanId>,
    pub service_name: String,
    pub operation_name: String,
    pub start_time_ns: u64,
    pub duration_ns: u64,
    pub status_code: SpanStatusCode,
    pub attributes: HashMap<String, String>,
}

impl Span {
    pub fn new(
        trace_id: TraceId,
        service_name: String,
        operation_name: String,
        start_time_ns: u64,
        duration_ns: u64,
    ) -> Self {
        Self {
            span_id: SpanId(Uuid::new_v4().to_string()),
            trace_id,
            parent_span_id: None,
            service_name,
            operation_name,
            start_time_ns,
            duration_ns,
            status_code: SpanStatusCode::Unset,
            attributes: HashMap::new(),
        }
    }

    pub fn end_time_ns(&self) -> u64 {
        self.start_time_ns + self.duration_ns
    }

    pub fn is_root(&self) -> bool {
        self.parent_span_id.is_none()
    }

    pub fn is_error(&self) -> bool {
        self.status_code == SpanStatusCode::Error
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum TraceStatus {
    Complete,
    Partial,
    Orphaned,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TraceTree {
    pub adjacency: HashMap<SpanId, Vec<SpanId>>,
    pub root_id: Option<SpanId>,
    pub depth: usize,
    pub width: usize,
}

impl TraceTree {
    pub fn build(spans: &[Span]) -> Self {
        let mut adjacency: HashMap<SpanId, Vec<SpanId>> = HashMap::new();
        let mut root_id: Option<SpanId> = None;

        for span in spans {
            adjacency.entry(span.span_id.clone()).or_default();
        }

        for span in spans {
            if let Some(ref parent) = span.parent_span_id {
                adjacency.entry(parent.clone()).or_default().push(span.span_id.clone());
            } else {
                root_id = Some(span.span_id.clone());
            }
        }

        let depth = Self::compute_depth(&adjacency, &root_id);
        let width = Self::compute_width(&adjacency, &root_id);

        Self { adjacency, root_id, depth, width }
    }

    fn compute_depth(adjacency: &HashMap<SpanId, Vec<SpanId>>, root: &Option<SpanId>) -> usize {
        match root {
            Some(r) => Self::depth_recursive(adjacency, r),
            None => 0,
        }
    }

    fn depth_recursive(adjacency: &HashMap<SpanId, Vec<SpanId>>, node: &SpanId) -> usize {
        let children = match adjacency.get(node) {
            Some(c) => c,
            None => return 1,
        };
        if children.is_empty() {
            return 1;
        }
        1 + children.iter().map(|c| Self::depth_recursive(adjacency, c)).max().unwrap_or(0)
    }

    fn compute_width(adjacency: &HashMap<SpanId, Vec<SpanId>>, root: &Option<SpanId>) -> usize {
        let root_node = match root {
            Some(r) => r,
            None => return 0,
        };
        let mut max_width = 0usize;
        let mut queue = std::collections::VecDeque::new();
        queue.push_back(root_node.clone());
        while !queue.is_empty() {
            let level_size = queue.len();
            max_width = max_width.max(level_size);
            for _ in 0..level_size {
                if let Some(node) = queue.pop_front() {
                    if let Some(children) = adjacency.get(&node) {
                        for child in children {
                            queue.push_back(child.clone());
                        }
                    }
                }
            }
        }
        max_width
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Trace {
    pub trace_id: TraceId,
    pub spans: Vec<Span>,
    pub tree: TraceTree,
    pub status: TraceStatus,
    pub assembled_at_ns: u64,
}

impl Trace {
    pub fn assemble(trace_id: TraceId, spans: Vec<Span>, assembled_at_ns: u64) -> Self {
        let tree = TraceTree::build(&spans);
        let status = if tree.root_id.is_some() {
            TraceStatus::Complete
        } else {
            TraceStatus::Orphaned
        };
        Self { trace_id, spans, tree, status, assembled_at_ns }
    }

    pub fn root_span(&self) -> Option<&Span> {
        self.tree.root_id.as_ref().and_then(|root_id| {
            self.spans.iter().find(|s| s.span_id == *root_id)
        })
    }

    pub fn total_duration_ns(&self) -> u64 {
        self.root_span().map_or(0, |s| s.duration_ns)
    }

    pub fn span_count(&self) -> usize {
        self.spans.len()
    }

    pub fn service_count(&self) -> usize {
        self.spans.iter().map(|s| &s.service_name).collect::<std::collections::HashSet<_>>().len()
    }

    pub fn error_count(&self) -> usize {
        self.spans.iter().filter(|s| s.is_error()).count()
    }

    pub fn span_by_id(&self, id: &SpanId) -> Option<&Span> {
        self.spans.iter().find(|s| s.span_id == *id)
    }

    pub fn children_of(&self, span_id: &SpanId) -> Vec<&Span> {
        self.tree.adjacency.get(span_id)
            .map(|ids| ids.iter().filter_map(|id| self.span_by_id(id)).collect())
            .unwrap_or_default()
    }

    pub fn self_time_ns(&self, span_id: &SpanId) -> u64 {
        let span = match self.span_by_id(span_id) {
            Some(s) => s,
            None => return 0,
        };
        let children_sum: u64 = self.children_of(span_id).iter().map(|c| c.duration_ns).sum();
        span.duration_ns.saturating_sub(children_sum)
    }

    pub fn operation_sequence_hash(&self) -> u64 {
        use std::hash::{Hash, Hasher};
        use std::collections::hash_map::DefaultHasher;
        let mut ops: Vec<String> = self.spans.iter()
            .map(|s| format!("{}:{}", s.service_name, s.operation_name))
            .collect();
        ops.sort();
        let mut hasher = DefaultHasher::new();
        ops.hash(&mut hasher);
        hasher.finish()
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ServiceOperationKey {
    pub service: String,
    pub operation: String,
}

impl ServiceOperationKey {
    pub fn new(service: String, operation: String) -> Self {
        Self { service, operation }
    }

    pub fn canonical(&self) -> String {
        format!("{}::{}", self.service, self.operation)
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ServicePairKey {
    pub source: String,
    pub target: String,
}

impl ServicePairKey {
    pub fn new(source: String, target: String) -> Self {
        Self { source, target }
    }

    pub fn canonical(&self) -> String {
        format!("{}→{}", self.source, self.target)
    }
}
