import { useParams } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { AlertTriangle } from 'lucide-react';

export function ClusterDetail() {
  const { id } = useParams<{ id: string }>();
  const [cluster, setCluster] = useState<{
    id: string;
    status: string;
    volume: string;
    anomalyRate: number;
    avgLatency: string;
    baselineLatency: string;
    currentLatency: string;
    size: number;
    criticalService: string;
    structureDrift: boolean;
    typicalTrace: string;
    deviations: string[];
  } | null>(null);

  useEffect(() => {
    // Mock cluster data
    setCluster({
      id: id || 'C-3',
      status: 'degrading',
      volume: '2.3k/min',
      anomalyRate: 18,
      avgLatency: '1.4s',
      baselineLatency: '320ms',
      currentLatency: '1.4s',
      size: 1250,
      criticalService: 'Payment Service',
      structureDrift: true,
      typicalTrace: 'API -> Auth -> Cart -> Payment -> DB',
      deviations: ['Missing Cache Layer', 'Extra Payment Retry Node'],
    });
  }, [id]);

  if (!cluster) {
    return <div>Loading...</div>;
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'stable':
        return '#10b981';
      case 'degrading':
        return '#f59e0b';
      case 'critical':
        return '#dc2626';
      default:
        return '#6b7280';
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* Header */}
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
          }}
        >
          <div>
            <h2
              style={{
                margin: 0,
                fontSize: '20px',
                fontWeight: '600',
                color: '#1f2937',
              }}
            >
              Cluster: {cluster.id} (Checkout Flow)
            </h2>
            <p
              style={{
                margin: '8px 0 0 0',
                fontSize: '14px',
                color: '#6b7280',
              }}
            >
              Detailed cluster analysis and behavioral patterns
            </p>
          </div>

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '8px 16px',
              borderRadius: 8,
              background: `${getStatusColor(cluster.status)}20`,
              color: getStatusColor(cluster.status),
              fontSize: '14px',
              fontWeight: '500',
            }}
          >
            <AlertTriangle size={16} />
            {cluster.status.toUpperCase()}
          </div>
        </div>
      </div>

      {/* Key Metrics */}
      <div
        style={{
          display: 'flex',
          gap: 20,
        }}
      >
        <div
          style={{
            flex: 1,
            background: '#ffffff',
            borderRadius: 12,
            border: '1px solid #e2e8f0',
            padding: 16,
            boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1)',
            textAlign: 'center',
          }}
        >
          <div
            style={{ fontSize: '24px', fontWeight: '600', color: '#dc2626' }}
          >
            {cluster.volume}
          </div>
          <div style={{ fontSize: '12px', color: '#6b7280', marginTop: 4 }}>
            Volume
          </div>
        </div>

        <div
          style={{
            flex: 1,
            background: '#ffffff',
            borderRadius: 12,
            border: '1px solid #e2e8f0',
            padding: 16,
            boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1)',
            textAlign: 'center',
          }}
        >
          <div
            style={{ fontSize: '24px', fontWeight: '600', color: '#dc2626' }}
          >
            {cluster.anomalyRate}%
          </div>
          <div style={{ fontSize: '12px', color: '#6b7280', marginTop: 4 }}>
            Anomaly Rate
          </div>
        </div>

        <div
          style={{
            flex: 1,
            background: '#ffffff',
            borderRadius: 12,
            border: '1px solid #e2e8f0',
            padding: 16,
            boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1)',
            textAlign: 'center',
          }}
        >
          <div
            style={{ fontSize: '24px', fontWeight: '600', color: '#dc2626' }}
          >
            {cluster.currentLatency}
          </div>
          <div style={{ fontSize: '12px', color: '#6b7280', marginTop: 4 }}>
            Current Latency
          </div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 20,
        }}
      >
        {/* Baseline vs Current */}
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
            Baseline vs Current
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '12px',
                background: '#f8fafc',
                borderRadius: 8,
              }}
            >
              <span style={{ fontSize: '14px', color: '#6b7280' }}>
                Baseline Latency
              </span>
              <span
                style={{
                  fontSize: '16px',
                  fontWeight: '600',
                  color: '#10b981',
                }}
              >
                {cluster.baselineLatency}
              </span>
            </div>

            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '12px',
                background: '#fef2f2',
                borderRadius: 8,
              }}
            >
              <span style={{ fontSize: '14px', color: '#6b7280' }}>
                Current Latency
              </span>
              <span
                style={{
                  fontSize: '16px',
                  fontWeight: '600',
                  color: '#dc2626',
                }}
              >
                {cluster.currentLatency}
              </span>
            </div>

            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '12px',
                background: '#f8fafc',
                borderRadius: 8,
              }}
            >
              <span style={{ fontSize: '14px', color: '#6b7280' }}>
                Structure
              </span>
              <span
                style={{
                  fontSize: '14px',
                  fontWeight: '600',
                  color: cluster.structureDrift ? '#dc2626' : '#10b981',
                }}
              >
                {cluster.structureDrift ? 'Drift detected' : 'Normal'}
              </span>
            </div>
          </div>
        </div>

        {/* Latency Distribution */}
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
            Latency Distribution
          </h3>

          <div
            style={{
              height: 150,
              border: '1px solid #e5e7eb',
              borderRadius: 8,
              background: '#fafafa',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#6b7280',
            }}
          >
            <div style={{ textAlign: 'center' }}>
              <div
                style={{
                  fontSize: '24px',
                  fontWeight: '600',
                  marginBottom: 8,
                  background:
                    'linear-gradient(to right, #10b981, #f59e0b, #dc2626)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  backgroundClip: 'text',
                }}
              >
                | | | | | | | | | | | | | | | | | | | | | | | |
              </div>
              <div style={{ fontSize: '12px' }}>
                Latency distribution skewed towards higher values
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Typical Trace Structure */}
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
          Typical Trace Structure
        </h3>

        <div
          style={{
            padding: 16,
            border: '1px solid #e5e7eb',
            borderRadius: 8,
            background: '#fafafa',
            fontSize: '14px',
            color: '#374151',
            fontFamily: 'monospace',
            textAlign: 'center',
          }}
        >
          {cluster.typicalTrace}
        </div>
      </div>

      {/* Detected Deviations */}
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
          Detected Deviations
        </h3>

        {cluster.deviations.map((deviation: string, index: number) => (
          <div
            key={index}
            style={{
              padding: 12,
              border: '1px solid #e5e7eb',
              borderRadius: 8,
              background: '#fef2f2',
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              marginBottom: 8,
            }}
          >
            <div
              style={{
                padding: 6,
                borderRadius: 6,
                background: '#dc2626',
                color: '#ffffff',
              }}
            >
              <AlertTriangle size={16} />
            </div>
            <div>
              <div
                style={{
                  fontSize: '14px',
                  fontWeight: '500',
                  color: '#1f2937',
                }}
              >
                {deviation}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
