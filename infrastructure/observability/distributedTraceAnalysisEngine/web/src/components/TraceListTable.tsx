import { api } from '../lib/api';
import { AnomalyScoreBadge } from './anomaly/AnomalyScoreBadge';
import { usePolling } from '../hooks';

export function TraceListTable({ onSelectTrace }: { onSelectTrace: (traceId: string) => void }) {
  const { data, loading } = usePolling(() => api.results(50, 0), 5_000);
  if (loading) return <p>Loading traces...</p>;

  return (
    <table>
      <thead>
        <tr><th>Trace ID</th><th>Entry Service</th><th>Duration</th><th>Spans</th><th>Cluster</th><th>Anomaly</th></tr>
      </thead>
      <tbody>
        {data?.results.map((row, idx) => {
          const traceId = typeof row.trace_id === 'string' ? row.trace_id : row.trace_id['0'];
          return <tr key={`${traceId}-${idx}`} onClick={() => onSelectTrace(traceId)}><td>{traceId}</td><td>-</td><td>{row.total_duration_ns ?? '-'}</td><td>{row.span_count ?? '-'}</td><td>{row.cluster_id}</td><td><AnomalyScoreBadge result={row} /></td></tr>;
        })}
      </tbody>
    </table>
  );
}
