use crate::domain::fingerprint::TraceFingerprint;
use crate::domain::ports::{ClusterAssigner, ClusterAssignment};
use ordered_float::OrderedFloat;

pub struct HdbscanClusterer {
    centroids: Vec<ClusterCentroid>,
    min_cluster_size: usize,
    min_samples: usize,
    distance_threshold: f64,
}

struct ClusterCentroid {
    id: i64,
    center: Vec<f64>,
    member_count: usize,
}

impl HdbscanClusterer {
    pub fn new(min_cluster_size: usize, min_samples: usize, distance_threshold: f64) -> Self {
        Self {
            centroids: Vec::new(),
            min_cluster_size,
            min_samples,
            distance_threshold,
        }
    }

    pub fn default_config() -> Self {
        Self::new(50, 10, 2.0)
    }

    fn euclidean_distance(a: &[f64], b: &[f64]) -> f64 {
        a.iter().zip(b.iter())
            .map(|(x, y)| (x - y).powi(2))
            .sum::<f64>()
            .sqrt()
    }

    fn find_nearest_centroid(&self, point: &[f64]) -> Option<(i64, f64)> {
        self.centroids.iter()
            .map(|c| (c.id, Self::euclidean_distance(point, &c.center)))
            .min_by_key(|&(_, d)| OrderedFloat(d))
    }

    fn compute_core_distances(points: &[Vec<f64>], min_samples: usize) -> Vec<f64> {
        points.iter().map(|p| {
            let mut distances: Vec<OrderedFloat<f64>> = points.iter()
                .map(|q| OrderedFloat(Self::euclidean_distance(p, q)))
                .collect();
            distances.sort();
            let k = min_samples.min(distances.len().saturating_sub(1));
            distances.get(k).map(|d| d.into_inner()).unwrap_or(f64::MAX)
        }).collect()
    }

    fn mutual_reachability_distance(core_a: f64, core_b: f64, dist: f64) -> f64 {
        core_a.max(core_b).max(dist)
    }

    fn build_mst(points: &[Vec<f64>], core_distances: &[f64]) -> Vec<(usize, usize, f64)> {
        let n = points.len();
        if n == 0 { return Vec::new(); }

        let mut in_tree = vec![false; n];
        let mut min_dist = vec![f64::MAX; n];
        let mut min_partner = vec![0usize; n];
        let mut edges = Vec::with_capacity(n.saturating_sub(1));

        in_tree[0] = true;
        for j in 1..n {
            let mrd = Self::mutual_reachability_distance(
                core_distances[0], core_distances[j],
                Self::euclidean_distance(&points[0], &points[j]),
            );
            min_dist[j] = mrd;
            min_partner[j] = 0;
        }

        for _ in 1..n {
            let next = (0..n)
                .filter(|&i| !in_tree[i])
                .min_by_key(|&i| OrderedFloat(min_dist[i]));

            let next = match next {
                Some(n) => n,
                None => break,
            };

            edges.push((min_partner[next], next, min_dist[next]));
            in_tree[next] = true;

            for j in 0..n {
                if in_tree[j] { continue; }
                let mrd = Self::mutual_reachability_distance(
                    core_distances[next], core_distances[j],
                    Self::euclidean_distance(&points[next], &points[j]),
                );
                if mrd < min_dist[j] {
                    min_dist[j] = mrd;
                    min_partner[j] = next;
                }
            }
        }

        edges.sort_by_key(|e| OrderedFloat(e.2));
        edges
    }

    fn extract_clusters(
        n: usize,
        mst: &[(usize, usize, f64)],
        min_cluster_size: usize,
    ) -> Vec<i64> {
        let mut labels = vec![-1i64; n];
        let mut parent = (0..n).collect::<Vec<_>>();

        fn find(parent: &mut [usize], x: usize) -> usize {
            if parent[x] != x {
                parent[x] = find(parent, parent[x]);
            }
            parent[x]
        }

        fn union(parent: &mut [usize], a: usize, b: usize) {
            let ra = find(parent, a);
            let rb = find(parent, b);
            if ra != rb {
                parent[ra] = rb;
            }
        }

        for &(a, b, _) in mst {
            union(&mut parent, a, b);
        }

        let mut cluster_members: std::collections::HashMap<usize, Vec<usize>> = std::collections::HashMap::new();
        for i in 0..n {
            let root = find(&mut parent, i);
            cluster_members.entry(root).or_default().push(i);
        }

        let mut cluster_id = 0i64;
        for (_, members) in &cluster_members {
            if members.len() >= min_cluster_size {
                for &idx in members {
                    labels[idx] = cluster_id;
                }
                cluster_id += 1;
            }
        }

        labels
    }

    fn compute_centroids_from_labels(points: &[Vec<f64>], labels: &[i64]) -> Vec<ClusterCentroid> {
        let mut cluster_points: std::collections::HashMap<i64, Vec<&Vec<f64>>> = std::collections::HashMap::new();
        for (i, &label) in labels.iter().enumerate() {
            if label >= 0 {
                cluster_points.entry(label).or_default().push(&points[i]);
            }
        }

        cluster_points.into_iter().map(|(id, pts)| {
            let dim = pts.first().map(|p| p.len()).unwrap_or(0);
            let mut center = vec![0.0; dim];
            for p in &pts {
                for (j, &val) in p.iter().enumerate() {
                    if j < dim { center[j] += val; }
                }
            }
            let count = pts.len();
            for v in &mut center {
                *v /= count as f64;
            }
            ClusterCentroid { id, center, member_count: count }
        }).collect()
    }
}

impl ClusterAssigner for HdbscanClusterer {
    fn assign(&self, fingerprint: &TraceFingerprint) -> ClusterAssignment {
        match self.find_nearest_centroid(&fingerprint.vector) {
            Some((id, dist)) if dist <= self.distance_threshold => {
                ClusterAssignment::assigned(id, dist)
            }
            Some((_, dist)) => ClusterAssignment::noise(dist),
            None => ClusterAssignment::noise(f64::MAX),
        }
    }

    fn refit(&mut self, fingerprints: &[TraceFingerprint]) {
        if fingerprints.len() < self.min_cluster_size {
            return;
        }

        let points: Vec<Vec<f64>> = fingerprints.iter().map(|f| f.vector.clone()).collect();
        let core_distances = Self::compute_core_distances(&points, self.min_samples);
        let mst = Self::build_mst(&points, &core_distances);
        let labels = Self::extract_clusters(points.len(), &mst, self.min_cluster_size);
        self.centroids = Self::compute_centroids_from_labels(&points, &labels);
    }
}
