import { Server, AlertTriangle, CheckCircle, AlertCircle } from 'lucide-react';
import { getServices } from '../utils/dataTransformations';
import { usePolling } from '../hooks';

export function Services() {
  // Fetch real services data from backend using data transformation
  const { data: services, loading: servicesLoading } = usePolling(
    () => getServices(),
    5000
  );

  const getHealthIcon = (health: string) => {
    switch (health) {
      case 'healthy':
        return <CheckCircle size={16} />;
      case 'warning':
        return <AlertCircle size={16} />;
      case 'critical':
        return <AlertTriangle size={16} />;
      default:
        return <Server size={16} />;
    }
  };

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

  const getHealthBg = (health: string) => {
    switch (health) {
      case 'healthy':
        return '#f0fdf4';
      case 'warning':
        return '#fef3c7';
      case 'critical':
        return '#fef2f2';
      default:
        return '#f3f4f6';
    }
  };

  const getLatencyColor = (latency: string) => {
    const value = parseFloat(latency);
    if (latency.includes('s')) {
      return value > 1 ? '#dc2626' : value > 0.5 ? '#f59e0b' : '#10b981';
    }
    return value > 500 ? '#f59e0b' : '#10b981';
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
        <h2
          style={{
            margin: 0,
            fontSize: '20px',
            fontWeight: '600',
            color: '#1f2937',
          }}
        >
          Services
        </h2>
        <p
          style={{
            margin: '8px 0 0 0',
            fontSize: '14px',
            color: '#6b7280',
          }}
        >
          Monitor service health, performance, and error rates across your
          infrastructure
        </p>
      </div>

      {/* Services Table */}
      <div
        style={{
          background: '#ffffff',
          borderRadius: 12,
          border: '1px solid #e2e8f0',
          padding: 20,
          boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1)',
        }}
      >
        {servicesLoading ? (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: 40,
              color: '#6b7280',
            }}
          >
            Loading services data...
          </div>
        ) : (
          <div
            style={{
              width: '100%',
              borderCollapse: 'collapse',
              fontSize: '14px',
              overflow: 'hidden',
            }}
          >
            <thead>
              <tr
                style={{
                  background: '#f8fafc',
                  borderBottom: '2px solid #e2e8f0',
                }}
              >
                <th
                  style={{
                    padding: '8px 12px',
                    textAlign: 'left',
                    fontWeight: '600',
                    color: '#374151',
                    fontSize: '12px',
                    whiteSpace: 'nowrap',
                  }}
                >
                  Service Name
                </th>
                <th
                  style={{
                    padding: '8px 12px',
                    textAlign: 'left',
                    fontWeight: '600',
                    color: '#374151',
                    fontSize: '12px',
                    whiteSpace: 'nowrap',
                  }}
                >
                  Health
                </th>
                <th
                  style={{
                    padding: '8px 12px',
                    textAlign: 'left',
                    fontWeight: '600',
                    color: '#374151',
                    fontSize: '12px',
                    whiteSpace: 'nowrap',
                  }}
                >
                  P95 Latency
                </th>
                <th
                  style={{
                    padding: '8px 12px',
                    textAlign: 'left',
                    fontWeight: '600',
                    color: '#374151',
                    fontSize: '12px',
                    whiteSpace: 'nowrap',
                  }}
                >
                  Error Rate
                </th>
                <th
                  style={{
                    padding: '8px 12px',
                    textAlign: 'left',
                    fontWeight: '600',
                    color: '#374151',
                    fontSize: '12px',
                    whiteSpace: 'nowrap',
                  }}
                >
                  Requests/min
                </th>
              </tr>
            </thead>
            <tbody>
              {(services || []).map((service, _index) => (
                <tr
                  key={service.name}
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
                      padding: '8px 12px',
                      fontWeight: '500',
                      color: '#1f2937',
                      maxWidth: '150px',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {service.name}
                  </td>
                  <td style={{ padding: '8px 12px' }}>
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 4,
                        padding: '2px 6px',
                        borderRadius: 4,
                        background: getHealthBg(service.health),
                        color: getHealthColor(service.health),
                        fontSize: '10px',
                        fontWeight: '500',
                        width: 'fit-content',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {getHealthIcon(service.health)}
                      <span style={{ textTransform: 'capitalize' }}>
                        {service.health}
                      </span>
                    </div>
                  </td>
                  <td
                    style={{
                      padding: '8px 12px',
                      color: getLatencyColor(service.p95Latency),
                      fontWeight: '600',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {service.p95Latency}
                  </td>
                  <td
                    style={{
                      padding: '8px 12px',
                      color:
                        service.errorRate > 10
                          ? '#dc2626'
                          : service.errorRate > 5
                            ? '#f59e0b'
                            : '#10b981',
                      fontWeight: '600',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {service.errorRate}%
                  </td>
                  <td
                    style={{
                      padding: '8px 12px',
                      color: '#64748b',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {service.requestsPerMin}
                  </td>
                </tr>
              ))}
            </tbody>
          </div>
        )}
      </div>

      {/* Summary Stats */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: 16,
        }}
      >
        <div
          style={{
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
            {(services || []).filter(s => s.health === 'critical').length}
          </div>
          <div style={{ fontSize: '12px', color: '#6b7280', marginTop: 4 }}>
            Critical Services
          </div>
        </div>

        <div
          style={{
            background: '#ffffff',
            borderRadius: 12,
            border: '1px solid #e2e8f0',
            padding: 16,
            boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1)',
            textAlign: 'center',
          }}
        >
          <div
            style={{ fontSize: '24px', fontWeight: '600', color: '#f59e0b' }}
          >
            {(services || []).filter(s => s.health === 'warning').length}
          </div>
          <div style={{ fontSize: '12px', color: '#6b7280', marginTop: 4 }}>
            Warning Services
          </div>
        </div>

        <div
          style={{
            background: '#ffffff',
            borderRadius: 12,
            border: '1px solid #e2e8f0',
            padding: 16,
            boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1)',
            textAlign: 'center',
          }}
        >
          <div
            style={{ fontSize: '24px', fontWeight: '600', color: '#10b981' }}
          >
            {(services || []).filter(s => s.health === 'healthy').length}
          </div>
          <div style={{ fontSize: '12px', color: '#6b7280', marginTop: 4 }}>
            Healthy Services
          </div>
        </div>

        <div
          style={{
            background: '#ffffff',
            borderRadius: 12,
            border: '1px solid #e2e8f0',
            padding: 16,
            boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1)',
            textAlign: 'center',
          }}
        >
          <div
            style={{ fontSize: '24px', fontWeight: '600', color: '#3b82f6' }}
          >
            {(services || [])
              .reduce((sum, s) => {
                const value = parseFloat(s.requestsPerMin.replace('k', ''));
                return sum + (isNaN(value) ? 0 : value);
              }, 0)
              .toFixed(1)}
            k
          </div>
          <div style={{ fontSize: '12px', color: '#6b7280', marginTop: 4 }}>
            Total Requests/min
          </div>
        </div>
      </div>
    </div>
  );
}
