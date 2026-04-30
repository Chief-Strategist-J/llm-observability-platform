import { AlertTriangle, TrendingUp, Clock } from 'lucide-react';

export function TopAnomalousClusters() {
  const clusters = [
    {
      id: 'C-3',
      latencyDrift: '+240%',
      errorRate: 12,
      status: 'critical',
      volume: '2.3k/min',
    },
    {
      id: 'C-1',
      latencyDrift: '+40%',
      errorRate: 3,
      status: 'warning',
      volume: '5.2k/min',
    },
    {
      id: 'C-6',
      latencyDrift: '+15%',
      errorRate: 8,
      status: 'warning',
      volume: '3.5k/min',
    },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'critical':
        return '#dc2626';
      case 'warning':
        return '#f59e0b';
      default:
        return '#10b981';
    }
  };

  const getStatusBg = (status: string) => {
    switch (status) {
      case 'critical':
        return '#fef2f2';
      case 'warning':
        return '#fef3c7';
      default:
        return '#f0fdf4';
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
      <h3
        style={{
          margin: '0 0 16px 0',
          fontSize: '16px',
          fontWeight: '600',
          color: '#1f2937',
        }}
      >
        Top Anomalous Clusters
      </h3>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {clusters.map(cluster => (
          <div
            key={cluster.id}
            style={{
              padding: 16,
              border: '1px solid #e5e7eb',
              borderRadius: 8,
              background: '#fafafa',
              display: 'flex',
              alignItems: 'center',
              gap: 16,
              transition: 'all 0.2s ease',
              cursor: 'pointer',
            }}
            onMouseEnter={e => {
              e.currentTarget.style.background = '#f3f4f6';
              e.currentTarget.style.transform = 'translateX(2px)';
            }}
            onMouseLeave={e => {
              e.currentTarget.style.background = '#fafafa';
              e.currentTarget.style.transform = 'translateX(0)';
            }}
          >
            {/* Status Indicator */}
            <div
              style={{
                padding: 8,
                borderRadius: 8,
                background: getStatusBg(cluster.status),
                color: getStatusColor(cluster.status),
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <AlertTriangle size={16} />
            </div>

            {/* Cluster Info */}
            <div style={{ flex: 1 }}>
              <div
                style={{
                  fontSize: '14px',
                  fontWeight: '600',
                  color: '#1f2937',
                  marginBottom: 4,
                }}
              >
                {cluster.id}
              </div>
              <div
                style={{
                  fontSize: '12px',
                  color: '#6b7280',
                }}
              >
                {cluster.volume} traces
              </div>
            </div>

            {/* Metrics */}
            <div style={{ display: 'flex', gap: 20 }}>
              <div style={{ textAlign: 'center' }}>
                <div
                  style={{
                    fontSize: '12px',
                    color: '#6b7280',
                    marginBottom: 2,
                  }}
                >
                  Latency Drift
                </div>
                <div
                  style={{
                    fontSize: '14px',
                    fontWeight: '600',
                    color: cluster.latencyDrift.startsWith('+')
                      ? '#dc2626'
                      : '#10b981',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 4,
                  }}
                >
                  <TrendingUp size={12} />
                  {cluster.latencyDrift}
                </div>
              </div>

              <div style={{ textAlign: 'center' }}>
                <div
                  style={{
                    fontSize: '12px',
                    color: '#6b7280',
                    marginBottom: 2,
                  }}
                >
                  Error Rate
                </div>
                <div
                  style={{
                    fontSize: '14px',
                    fontWeight: '600',
                    color: cluster.errorRate > 10 ? '#dc2626' : '#f59e0b',
                  }}
                >
                  {cluster.errorRate}%
                </div>
              </div>
            </div>

            {/* Status Badge */}
            <div
              style={{
                padding: '4px 8px',
                borderRadius: 12,
                fontSize: '12px',
                fontWeight: '500',
                background: getStatusBg(cluster.status),
                color: getStatusColor(cluster.status),
                textTransform: 'capitalize',
              }}
            >
              {cluster.status}
            </div>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div
        style={{
          marginTop: 16,
          padding: '12px 16px',
          background: '#f8fafc',
          borderRadius: 8,
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          fontSize: '12px',
          color: '#6b7280',
        }}
      >
        <Clock size={14} />
        <span>Last updated: 2 minutes ago</span>
      </div>
    </div>
  );
}
