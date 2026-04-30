import React, { MouseEvent } from 'react';
import { api } from '../../api';
import { AnomalyScoreBadge } from '../anomaly/AnomalyScoreBadge';
import { usePolling } from '../../hooks';

interface CriticalPathNode {
  self_time_ns?: number;
}

interface CriticalPath {
  nodes?: CriticalPathNode[];
}

interface TraceRow {
  trace_id: string;
  fingerprint?: string;
  is_anomalous?: boolean;
  confidence?: number;
  cluster_id?: number;
  critical_path?: CriticalPath;
  total_duration_ns?: number;
  span_count?: number;
}

interface TraceListTableProps {
  onSelectTrace: (traceId: string) => void;
  selectedTraceId?: string;
  compact?: boolean;
}

export function TraceListTable({
  onSelectTrace,
  selectedTraceId,
  compact = false,
}: TraceListTableProps) {
  const { data: tracesData, loading: tracesLoading } = usePolling(
    () => api.traces(),
    5_000
  );
  
  const { data: resultsData, loading: resultsLoading } = usePolling(
    () => api.results(compact ? 50 : 200, 0),
    5_000
  );
  
  const loading = tracesLoading || resultsLoading;

  if (loading) {
    return (
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: 40,
          color: '#6b7280',
        }}
      >
        Loading traces...
      </div>
    );
  }

  const traces = tracesData || [];
  const results = resultsData?.results || [];
  
  // Merge trace data with analysis results
  const mergedTraces: TraceRow[] = traces.map((trace: any) => {
    const result = results.find((r: any) => r.trace_id === trace.trace_id);
    return {
      trace_id: trace.trace_id,
      span_count: trace.span_count,
      total_duration_ns: trace.duration_ns,
      is_anomalous: result?.is_anomalous,
      confidence: result?.confidence,
      cluster_id: result?.cluster_id,
      critical_path: result?.critical_path,
    };
  });

  return (
    <div style={{ height: '100%', overflow: 'auto' }}>
      <table
        style={{
          width: '100%',
          borderCollapse: 'collapse',
          fontSize: compact ? '12px' : '14px',
        }}
      >
        <thead
          style={{
            position: 'sticky',
            top: 0,
            background: '#f8fafc',
            borderBottom: '2px solid #e2e8f0',
            zIndex: 10,
          }}
        >
          <tr>
            <th
              style={{
                padding: compact ? '8px' : '12px',
                textAlign: 'left',
                fontWeight: '600',
                color: '#374151',
                fontSize: compact ? '11px' : '14px',
              }}
            >
              Trace ID
            </th>
            {!compact && (
              <th
                style={{
                  padding: '12px',
                  textAlign: 'left',
                  fontWeight: '600',
                  color: '#374151',
                  fontSize: '14px',
                }}
              >
                Entry Service
              </th>
            )}
            <th
              style={{
                padding: compact ? '8px' : '12px',
                textAlign: 'left',
                fontWeight: '600',
                color: '#374151',
                fontSize: compact ? '11px' : '14px',
              }}
            >
              Duration
            </th>
            {!compact && (
              <th
                style={{
                  padding: '12px',
                  textAlign: 'left',
                  fontWeight: '600',
                  color: '#374151',
                  fontSize: '14px',
                }}
              >
                Spans
              </th>
            )}
            <th
              style={{
                padding: compact ? '8px' : '12px',
                textAlign: 'left',
                fontWeight: '600',
                color: '#374151',
                fontSize: compact ? '11px' : '14px',
              }}
            >
              Anomaly
            </th>
          </tr>
        </thead>
        <tbody>
          {mergedTraces.map((row: TraceRow, idx: number) => {
            // Backend returns simple string for trace_id
            const traceId = row.trace_id;
            // Use total_duration_ns if available, otherwise calculate from critical_path nodes
            const duration = row.total_duration_ns
              ? `${(row.total_duration_ns / 1_000_000).toFixed(1)}ms`
              : row.critical_path?.nodes?.length
              ? `${(row.critical_path.nodes.reduce((sum: number, node: CriticalPathNode) => sum + (node.self_time_ns || 0), 0) / 1_000_000).toFixed(1)}ms`
              : '-';
            const isSelected = selectedTraceId === traceId;

            return (
              <tr
                key={`${traceId}-${idx}`}
                onClick={() => onSelectTrace(traceId)}
                style={{
                  borderBottom: '1px solid #f1f5f9',
                  cursor: 'pointer',
                  transition: 'background-color 0.2s',
                  background: isSelected ? '#dbeafe' : 'transparent',
                }}
                onMouseEnter={(e: React.MouseEvent<HTMLTableRowElement>) => {
                  if (!isSelected) {
                    e.currentTarget.style.backgroundColor = '#f8fafc';
                  }
                }}
                onMouseLeave={(e: React.MouseEvent<HTMLTableRowElement>) => {
                  if (!isSelected) {
                    e.currentTarget.style.backgroundColor = 'transparent';
                  }
                }}
              >
                <td
                  style={{
                    padding: compact ? '8px' : '12px',
                    fontFamily: 'monospace',
                    fontSize: compact ? '10px' : '12px',
                    color: '#475569',
                    maxWidth: compact ? '120px' : '200px',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {traceId}
                </td>
                {!compact && (
                  <td style={{ padding: '12px', color: '#64748b' }}>-</td>
                )}
                <td
                  style={{
                    padding: compact ? '8px' : '12px',
                    color: '#64748b',
                    fontWeight: '500',
                  }}
                >
                  {duration}
                </td>
                {!compact && (
                  <td style={{ padding: '12px', color: '#64748b' }}>
                    {row.critical_path?.nodes?.length ?? '-'}
                  </td>
                )}
                <td style={{ padding: compact ? '8px' : '12px' }}>
                  <AnomalyScoreBadge result={row} compact={compact} />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

      {traces.length === 0 && (
        <div
          style={{
            textAlign: 'center',
            padding: 40,
            color: '#6b7280',
            fontSize: '14px',
          }}
        >
          No traces found. Send some traces to the system to see them here.
        </div>
      )}
    </div>
  );
}
