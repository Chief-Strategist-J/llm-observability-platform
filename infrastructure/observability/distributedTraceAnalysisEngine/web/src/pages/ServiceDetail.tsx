import { useParams } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { Server, AlertTriangle, TrendingUp } from 'lucide-react';

export function ServiceDetail() {
  const { id } = useParams<{ id: string }>();
  const [service, setService] = useState<{
    name: string;
    health: 'healthy' | 'warning' | 'critical';
    errorRate: number;
    p95Latency: string;
    latencyChange: string;
    status: string;
    requestsPerMin: string;
    uptime: string;
    lastIncident: string;
    dependencies: string[];
    structuralChanges: string[];
    affectedClusters: string[];
  } | null>(null);

  useEffect(() => {
    // Mock service data
    setService({
      name: id || 'Payment Gateway',
      health: 'critical',
      errorRate: 14,
      p95Latency: '2.1s',
      latencyChange: '+180%',
      status: 'Degrading',
      requestsPerMin: '1.2k',
      uptime: '99.2%',
      lastIncident: '2 hours ago',
      affectedClusters: ['C-3 (Checkout Flow)'],
      dependencies: ['API Gateway', 'Auth Service', 'External Payment API'],
      structuralChanges: [
        'New retry loop detected',
        'Increased calls to external API',
      ],
    });
  }, [id]);

  if (!service) {
    return <div>Loading...</div>;
  }

  const getHealthColor = (health: string) => {
    switch (health) {
      case 'healthy':
        return '#10b981';
      case 'warning':
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
              Service: {service.name}
            </h2>
            <p
              style={{
                margin: '8px 0 0 0',
                fontSize: '14px',
                color: '#6b7280',
              }}
            >
              Detailed service performance and dependency analysis
            </p>
          </div>

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '8px 16px',
              borderRadius: 8,
              background: `${getHealthColor(service.health)}20`,
              color: getHealthColor(service.health),
              fontSize: '14px',
              fontWeight: '500',
            }}
          >
            <AlertTriangle size={16} />
            {service.health.toUpperCase()}
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
            {service.errorRate}%
          </div>
          <div style={{ fontSize: '12px', color: '#6b7280', marginTop: 4 }}>
            Error Rate
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
            {service.p95Latency}
          </div>
          <div style={{ fontSize: '12px', color: '#6b7280', marginTop: 4 }}>
            P95 Latency
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
            {service.latencyChange}
          </div>
          <div style={{ fontSize: '12px', color: '#6b7280', marginTop: 4 }}>
            Latency Change
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
        {/* Dependency Graph */}
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
            Dependency Graph
          </h3>

          <div
            style={{
              height: 200,
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
              <Server size={32} style={{ margin: '0 auto 8px' }} />
              <div>API Gateway</div>
              <div style={{ fontSize: '12px', margin: '8px 0' }}>v</div>
              <div>Auth Service</div>
              <div style={{ fontSize: '12px', margin: '8px 0' }}>v</div>
              <div>{service.name}</div>
              <div style={{ fontSize: '12px', margin: '8px 0' }}>v</div>
              <div>External API</div>
            </div>
          </div>
        </div>

        {/* Latency Trend */}
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
            Latency Trend
          </h3>

          <div
            style={{
              height: 200,
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
              <TrendingUp
                size={32}
                style={{ margin: '0 auto 8px', color: '#dc2626' }}
              />
              <div>Latency increasing over time</div>
              <div style={{ fontSize: '12px', marginTop: 4 }}>
                +180% in last hour
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Structural Changes */}
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
          Structural Changes
        </h3>

        <ul
          style={{
            margin: 0,
            paddingLeft: 20,
            fontSize: '14px',
            color: '#6b7280',
            lineHeight: 1.6,
          }}
        >
          {service.structuralChanges.map((change: string, index: number) => (
            <li key={index}>{change}</li>
          ))}
        </ul>
      </div>

      {/* Affected Clusters */}
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
          Affected Clusters
        </h3>

        {service.affectedClusters.map((cluster: string, index: number) => (
          <div
            key={index}
            style={{
              padding: 12,
              border: '1px solid #e5e7eb',
              borderRadius: 8,
              background: '#fafafa',
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
                background: '#fef2f2',
                color: '#dc2626',
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
                {cluster}
              </div>
              <div
                style={{
                  fontSize: '12px',
                  color: '#6b7280',
                }}
              >
                Status: Degrading
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
