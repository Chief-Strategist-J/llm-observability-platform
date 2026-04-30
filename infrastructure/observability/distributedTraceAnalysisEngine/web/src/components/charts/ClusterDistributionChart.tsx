import type { AnalysisResult } from '../../types/trace';

export function ClusterDistributionChart({ results }: { results: AnalysisResult[] }) {
  const buckets = results.reduce<Record<string, number>>((acc, r) => {
    const key = String(r.cluster_id);
    acc[key] = (acc[key] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <section>
      <h3>Cluster Distribution</h3>
      <ul>{Object.entries(buckets).map(([cluster, count]) => <li key={cluster}>Cluster {cluster}: {count}</li>)}</ul>
    </section>
  );
}
