import {
  AlertTriangle,
  Activity,
  GitBranch,
  Clock,
  TrendingUp,
} from 'lucide-react';


interface CriticalPath {
  optimization_opportunity?: boolean;
  total_duration_ns?: number;
  critical_service?: string;
  nodes?: Array<{
    service?: string;
    self_time_ns?: number;
  }>;
}

interface AnomalyExplanationProps {
  result: {
    confidence: number;
    is_anomalous: boolean;
    cluster_id: number;
    anomaly_scores?: Array<{
      signal_name: string;
      score: number;
      is_anomalous?: boolean;
    }>;
    critical_path?: CriticalPath;
  };
}

export function AnomalyExplanation({ result }: AnomalyExplanationProps) {
  const score = result.confidence || 0;
  const isAnomalous = result.is_anomalous || score > 0.5;

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return '#dc2626';
    if (score >= 0.5) return '#f59e0b';
    return '#10b981';
  };

  const getScoreBg = (score: number) => {
    if (score >= 0.8) return '#fef2f2';
    if (score >= 0.5) return '#fef3c7';
    return '#f0fdf4';
  };

  const getAnomalyReasons = (result: AnomalyExplanationProps['result']): string[] => {
    const reasons: string[] = [];

    if (result.cluster_id === -1) {
      reasons.push('No matching cluster found');
    }

    if (result.anomaly_scores && result.anomaly_scores.length > 0) {
      result.anomaly_scores.forEach((score) => {
        if (score.is_anomalous) {
          reasons.push(
            `${score.signal_name}: ${(score.score * 100).toFixed(1)}%`
          );
        }
      });
    }

    if (result.critical_path && result.critical_path.optimization_opportunity) {
      reasons.push('Critical path optimization opportunity detected');
    }

    return reasons.length > 0 ? reasons : ['Normal trace behavior detected'];
  };

  const anomalyReasons = getAnomalyReasons(result);

  return (
    <div style={{ padding: 16 }}>
      {/* Score Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          marginBottom: 16,
          padding: '12px 16px',
          borderRadius: 8,
          background: getScoreBg(score),
          border: `1px solid ${getScoreColor(score)}20`,
        }}
      >
        <div
          style={{
            padding: 8,
            borderRadius: 6,
            background: getScoreColor(score),
            color: '#ffffff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          {isAnomalous ? <AlertTriangle size={16} /> : <GitBranch size={16} />}
        </div>

        <div style={{ flex: 1 }}>
          <div
            style={{
              fontSize: '16px',
              fontWeight: '600',
              color: getScoreColor(score),
              marginBottom: 4,
            }}
          >
            Score: {score.toFixed(2)}
          </div>
          <div
            style={{
              fontSize: '12px',
              color: isAnomalous ? '#dc2626' : '#16a34a',
            }}
          >
            {isAnomalous
              ? 'Anomalous behavior detected'
              : 'Normal trace behavior'}
          </div>
        </div>
      </div>

      {/* Detailed Analysis */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {anomalyReasons.map((reason, index) => (
          <div
            key={index}
            style={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: 12,
              padding: 12,
              borderRadius: 8,
              background: '#fafafa',
              border: '1px solid #e5e7eb',
            }}
          >
            <div
              style={{
                padding: 6,
                borderRadius: 4,
                background: '#f3f4f6',
                color: '#6b7280',
                marginTop: 2,
              }}
            >
              {reason.includes('latency') && <Clock size={14} />}
              {reason.includes('cluster') && <GitBranch size={14} />}
              {reason.includes('error') && <AlertTriangle size={14} />}
              {reason.includes('critical') && <TrendingUp size={14} />}
              {!reason.includes('latency') &&
                !reason.includes('cluster') &&
                !reason.includes('error') &&
                !reason.includes('critical') && <Activity size={14} />}
            </div>

            <div style={{ flex: 1 }}>
              <div
                style={{
                  fontSize: '14px',
                  color: '#1f2937',
                  marginBottom: 4,
                  fontWeight: '500',
                }}
              >
                {reason}
              </div>

              {/* Add specific explanations based on the reason */}
              {reason.includes('No matching cluster') && (
                <div
                  style={{
                    fontSize: '12px',
                    color: '#6b7280',
                    lineHeight: 1.4,
                  }}
                >
                  This trace doesn&apos;t match any known behavioral patterns,
                  suggesting it represents a new or unusual execution path.
                </div>
              )}

              {reason.includes('latency') && (
                <div
                  style={{
                    fontSize: '12px',
                    color: '#6b7280',
                    lineHeight: 1.4,
                  }}
                >
                  The execution time deviates significantly from expected
                  patterns for this type of operation.
                </div>
              )}

              {reason.includes('error') && (
                <div
                  style={{
                    fontSize: '12px',
                    color: '#6b7280',
                    lineHeight: 1.4,
                  }}
                >
                  Error propagation or failure patterns detected in the trace
                  execution.
                </div>
              )}

              {reason.includes('critical') && (
                <div
                  style={{
                    fontSize: '12px',
                    color: '#6b7280',
                    lineHeight: 1.4,
                  }}
                >
                  The critical path analysis identifies optimization
                  opportunities in this trace.
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Critical Path Info */}
      {result.critical_path && (
        <div
          style={{
            marginTop: 16,
            padding: 12,
            borderRadius: 8,
            background: '#f8fafc',
            border: '1px solid #e2e8f0',
          }}
        >
          <div
            style={{
              fontSize: '12px',
              fontWeight: '600',
              color: '#374151',
              marginBottom: 8,
            }}
          >
            Critical Path Analysis
          </div>

          <div style={{ fontSize: '12px', color: '#6b7280', lineHeight: 1.4 }}>
            <div style={{ marginBottom: 4 }}>
              <strong>Total Duration:</strong>{' '}
              {(
                (result.critical_path.total_duration_ns || 0) / 1_000_000
              ).toFixed(1)}
              ms
            </div>
            <div style={{ marginBottom: 4 }}>
              <strong>Critical Service:</strong>{' '}
              {result.critical_path.critical_service || 'N/A'}
            </div>
            <div>
              <strong>Optimization Opportunity:</strong>{' '}
              {result.critical_path.optimization_opportunity ? 'Yes' : 'No'}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
