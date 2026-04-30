import { AlertTriangle, Activity, Clock } from 'lucide-react';
import { api } from '../../api';
import { usePolling } from '../../hooks';

interface AnomalyEvent {
  id: string;
  timestamp: string;
  type: 'latency' | 'structural' | 'error';
  severity: 'high' | 'medium' | 'low';
  message: string;
  cluster?: string;
  service?: string;
}

export function LiveAnomalyFeed() {
  const { data: traces, loading } = usePolling(
    () => api.results(50, 0),
    5000
  );

  const events: AnomalyEvent[] = traces?.results
    .filter(trace => trace.is_anomalous || (trace.confidence && trace.confidence > 0.7))
    .slice(0, 10)
    .map((trace) => {
      const confidence = trace.confidence || 0;
      let severity: 'high' | 'medium' | 'low' = 'medium';
      if (confidence > 0.9) severity = 'high';
      else if (confidence > 0.7) severity = 'medium';
      else severity = 'low';

      const timestamp = new Date().toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
      });

      const criticalService = trace.critical_path?.critical_service || 'Unknown Service';
      
      return {
        id: trace.trace_id,
        timestamp,
        type: confidence > 0.85 ? 'error' : 'latency',
        severity,
        message: `Anomaly detected in ${criticalService} (${(confidence * 100).toFixed(1)}% confidence)`,
        cluster: `C-${trace.cluster_id}`,
        service: criticalService,
      };
    }) || [];

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high': return '#dc2626';
      case 'medium': return '#f59e0b';
      case 'low': return '#3b82f6';
      default: return '#6b7280';
    }
  };

  const getSeverityBg = (severity: string) => {
    switch (severity) {
      case 'high': return '#fef2f2';
      case 'medium': return '#fef3c7';
      case 'low': return '#dbeafe';
      default: return '#f3f4f6';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'latency': return <Clock size={14} />;
      case 'error': return <AlertTriangle size={14} />;
      default: return <Activity size={14} />;
    }
  };

  return (
    <div
      style={{
        background: '#ffffff',
        borderRadius: 12,
        border: '1px solid #e2e8f0',
        padding: 20,
        boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1)',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 16,
        }}
      >
        <h3
          style={{
            margin: 0,
            fontSize: '16px',
            fontWeight: '600',
            color: '#1f2937',
          }}
        >
          Live Anomaly Feed
        </h3>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            fontSize: '12px',
            color: '#6b7280',
          }}
        >
          <div
            style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              background: '#10b981',
              animation: 'pulse 2s infinite',
            }}
          />
          Live
        </div>
      </div>

      {loading ? (
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            height: 200,
            color: '#6b7280',
          }}
        >
          Loading anomaly data...
        </div>
      ) : events.length === 0 ? (
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            height: 200,
            color: '#6b7280',
          }}
        >
          No anomalies detected
        </div>
      ) : (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 12,
            maxHeight: 300,
            overflowY: 'auto',
          }}
        >
          {events.map((event) => (
            <div
              key={event.id}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                padding: '12px 16px',
                borderRadius: 8,
                background: getSeverityBg(event.severity),
                border: `1px solid ${getSeverityColor(event.severity)}20`,
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  flex: 1,
                }}
              >
                <div
                  style={{
                    color: getSeverityColor(event.severity),
                  }}
                >
                  {getTypeIcon(event.type)}
                </div>
                <div style={{ flex: 1 }}>
                  <div
                    style={{
                      fontSize: '14px',
                      fontWeight: '500',
                      color: '#1f2937',
                      marginBottom: 4,
                    }}
                  >
                    {event.message}
                  </div>
                  <div
                    style={{
                      fontSize: '12px',
                      color: '#6b7280',
                    }}
                  >
                    {event.cluster} · {event.service} · {event.timestamp}
                  </div>
                </div>
              </div>
              <div
                style={{
                  padding: '4px 8px',
                  borderRadius: 4,
                  background: getSeverityColor(event.severity),
                  color: '#ffffff',
                  fontSize: '11px',
                  fontWeight: '500',
                  textTransform: 'uppercase',
                }}
              >
                {event.severity}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
