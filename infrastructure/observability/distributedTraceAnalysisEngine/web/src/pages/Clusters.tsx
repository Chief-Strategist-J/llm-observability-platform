import { useState } from 'react';
import { AlertTriangle, CheckCircle, AlertCircle, Network } from 'lucide-react';
import { ClusterMap2D } from '../components/clusters/ClusterMap2D';
import { getClusters } from '../utils/dataTransformations';
import { usePolling } from '../hooks';


export function Clusters() {
  // Fetch real clusters data from backend using data transformation
  const { data: clusters, loading: clustersLoading } = usePolling(
    () => getClusters(),
    5000
  );

  const [selectedCluster, setSelectedCluster] = useState<string | null>(null);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'stable':
        return <CheckCircle size={16} />;
      case 'degrading':
        return <AlertCircle size={16} />;
      case 'critical':
        return <AlertTriangle size={16} />;
      default:
        return <Network size={16} />;
    }
  };

  const getHealthColor = (status: string) => {
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

  const getHealthBg = (status: string) => {
    switch (status) {
      case 'stable':
        return '#f0fdf4';
      case 'degrading':
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
          Clusters
        </h2>
        <p
          style={{
            margin: '8px 0 0 0',
            fontSize: '14px',
            color: '#6b7280',
          }}
        >
          Monitor trace clusters, detect anomalies, and identify behavioral
          patterns
        </p>
      </div>

      {/* Cluster Map */}
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
          Cluster Map (2D Projection)
        </h3>

        <div
          style={{
            height: 400,
            border: '1px solid #e5e7eb',
            borderRadius: 8,
            background: '#fafafa',
            position: 'relative',
          }}
        >
          {clustersLoading ? (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                height: '100%',
                color: '#6b7280',
              }}
            >
              Loading cluster data...
            </div>
          ) : (
            <ClusterMap2D
              clusters={clusters || []}
              selectedCluster={selectedCluster}
              onClusterSelect={setSelectedCluster}
            />
          )}
        </div>

        <div
          style={{
            marginTop: 12,
            fontSize: '12px',
            color: '#6b7280',
            display: 'flex',
            alignItems: 'center',
            gap: 16,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <div
              style={{
                width: 12,
                height: 12,
                borderRadius: '50%',
                background: '#10b981',
              }}
            />
            <span>Normal cluster</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <div
              style={{
                width: 12,
                height: 12,
                borderRadius: '50%',
                background: '#ef4444',
              }}
            />
            <span>Anomalous cluster</span>
          </div>
          <div>Bubble size = cluster volume</div>
        </div>
      </div>

      {/* Cluster List */}
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
          Cluster List
        </h3>

        {clustersLoading ? (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: 40,
              color: '#6b7280',
            }}
          >
            Loading cluster data...
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
                  Cluster
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
                  Size
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
                  Avg Latency
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
                  Anomaly Rate
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
                  Status
                </th>
              </tr>
            </thead>
            <tbody>
              {(clusters || []).map(cluster => (
                <tr
                  key={cluster.id}
                  style={{
                    borderBottom: '1px solid #f1f5f9',
                    cursor: 'pointer',
                    transition: 'background-color 0.2s',
                    background:
                      selectedCluster === cluster.id
                        ? '#dbeafe'
                        : 'transparent',
                  }}
                  onClick={() => setSelectedCluster(cluster.id)}
                  onMouseEnter={e => {
                    if (selectedCluster !== cluster.id) {
                      e.currentTarget.style.backgroundColor = '#f8fafc';
                    }
                  }}
                  onMouseLeave={e => {
                    if (selectedCluster !== cluster.id) {
                      e.currentTarget.style.backgroundColor = 'transparent';
                    }
                  }}
                >
                  <td
                    style={{
                      padding: '8px 12px',
                      fontWeight: '500',
                      color: '#1f2937',
                      maxWidth: '100px',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {cluster.id}
                  </td>
                  <td
                    style={{
                      padding: '8px 12px',
                      color: '#64748b',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {cluster.size.toLocaleString()}
                  </td>
                  <td
                    style={{
                      padding: '8px 12px',
                      color: getLatencyColor(cluster.avgLatency),
                      fontWeight: '600',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {cluster.avgLatency}
                  </td>
                  <td
                    style={{
                      padding: '8px 12px',
                      color:
                        cluster.anomalyRate > 10
                          ? '#dc2626'
                          : cluster.anomalyRate > 5
                            ? '#f59e0b'
                            : '#10b981',
                      fontWeight: '600',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {cluster.anomalyRate}%
                  </td>
                  <td style={{ padding: '8px 12px' }}>
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 4,
                        padding: '2px 6px',
                        borderRadius: 4,
                        background: getHealthBg(cluster.status),
                        color: getHealthColor(cluster.status),
                        fontSize: '10px',
                        fontWeight: '500',
                        width: 'fit-content',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {getStatusIcon(cluster.status)}
                      <span style={{ textTransform: 'capitalize' }}>
                        {cluster.status}
                      </span>
                    </div>
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
            {(clusters || []).filter(c => c.status === 'critical').length}
          </div>
          <div style={{ fontSize: '12px', color: '#6b7280', marginTop: 4 }}>
            Critical Clusters
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
            {(clusters || []).filter(c => c.status === 'degrading').length}
          </div>
          <div style={{ fontSize: '12px', color: '#6b7280', marginTop: 4 }}>
            Degrading Clusters
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
            {(clusters || []).filter(c => c.status === 'stable').length}
          </div>
          <div style={{ fontSize: '12px', color: '#6b7280', marginTop: 4 }}>
            Stable Clusters
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
            {(
              (clusters || []).reduce((sum, c) => sum + c.size, 0) / 1000
            ).toFixed(1)}
            k
          </div>
          <div style={{ fontSize: '12px', color: '#6b7280', marginTop: 4 }}>
            Total Traces
          </div>
        </div>
      </div>
    </div>
  );
}
