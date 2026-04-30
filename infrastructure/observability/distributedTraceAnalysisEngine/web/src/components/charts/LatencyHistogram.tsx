import type { AnalysisResult } from '../../types/trace';

export function LatencyHistogram({ results, bins }: { results: AnalysisResult[]; bins: number }) {
  const durations = results.map((r) => r.total_duration_ns ?? 0).filter((d) => d > 0);
  if (!durations.length) return <section><h3>Latency Histogram</h3><p>No duration data.</p></section>;

  const min = Math.min(...durations);
  const max = Math.max(...durations);
  const width = Math.max(1, Math.floor((max - min) / bins));
  const histogram = new Array(bins).fill(0);
  durations.forEach((d) => {
    const index = Math.min(bins - 1, Math.floor((d - min) / width));
    histogram[index] += 1;
  });

  return (
    <section>
      <h3>Latency Histogram ({bins} bins)</h3>
      <ol>{histogram.map((count, i) => <li key={i}>Bin {i + 1}: {count}</li>)}</ol>
    </section>
  );
}
