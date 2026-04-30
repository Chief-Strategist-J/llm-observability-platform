import { api } from '../api';
import { AnomalyScoreBadge } from './anomaly/AnomalyScoreBadge';
import { usePolling } from '../hooks';

export function TraceListTable({
  onSelectTrace,
}: {
  onSelectTrace: (traceId: string) => void;
}) {
  const { data, loading } = usePolling(() => api.results(50, 0), 5_000);
  if (loading) return <p>Loading traces...</p>;

  return (
    <table
      style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}
    >
      <thead>
        <tr
          style={{ background: '#f8fafc', borderBottom: '2px solid #e2e8f0' }}
        >
          <th
            style={{
              padding: '12px',
              textAlign: 'left',
              fontWeight: '600',
              color: '#374151',
            }}
          >
            Trace ID
          </th>
          <th
            style={{
              padding: '12px',
              textAlign: 'left',
              fontWeight: '600',
              color: '#374151',
            }}
          >
            Entry Service
          </th>
          <th
            style={{
              padding: '12px',
              textAlign: 'left',
              fontWeight: '600',
              color: '#374151',
            }}
          >
            Duration
          </th>
          <th
            style={{
              padding: '12px',
              textAlign: 'left',
              fontWeight: '600',
              color: '#374151',
            }}
          >
            Spans
          </th>
          <th
            style={{
              padding: '12px',
              textAlign: 'left',
              fontWeight: '600',
              color: '#374151',
            }}
          >
            Cluster
          </th>
          <th
            style={{
              padding: '12px',
              textAlign: 'left',
              fontWeight: '600',
              color: '#374151',
            }}
          >
            Anomaly
          </th>
        </tr>
      </thead>
      <tbody>
        {data?.results.map((row, idx) => {
          const traceId =
            typeof row.trace_id === 'string' ? row.trace_id : row.trace_id['0'];
          const duration = row.total_duration_ns
            ? `${(row.total_duration_ns / 1_000_000).toFixed(1)}ms`
            : '-';
          return (
            <tr
              key={`${traceId}-${idx}`}
              onClick={() => onSelectTrace(traceId)}
              style={{
                borderBottom: '1px solid #f1f5f9',
                cursor: 'pointer',
                transition: 'background-color 0.2s',
              }}
              onMouseEnter={e =>
                (e.currentTarget.style.backgroundColor = '#f8fafc')
              }
              onMouseLeave={e =>
                (e.currentTarget.style.backgroundColor = 'transparent')
              }
            >
              <td
                style={{
                  padding: '12px',
                  fontFamily: 'monospace',
                  fontSize: '12px',
                  color: '#475569',
                }}
              >
                {traceId}
              </td>
              <td style={{ padding: '12px', color: '#64748b' }}>-</td>
              <td style={{ padding: '12px', color: '#64748b' }}>{duration}</td>
              <td style={{ padding: '12px', color: '#64748b' }}>
                {row.span_count ?? '-'}
              </td>
              <td style={{ padding: '12px', color: '#64748b' }}>
                {row.cluster_id}
              </td>
              <td style={{ padding: '12px' }}>
                <AnomalyScoreBadge result={row} />
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
