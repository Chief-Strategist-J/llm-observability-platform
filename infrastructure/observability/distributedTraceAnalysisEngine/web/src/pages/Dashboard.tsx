import { useState } from 'react';
import {
  TrendingUp,
  TrendingDown,
  Activity,
  AlertTriangle,
} from 'lucide-react';
import { ClusterStabilityChart } from '../components/dashboard/ClusterStabilityChart';
import { AnomalyTrendChart } from '../components/dashboard/AnomalyTrendChart';
import { ErrorDistributionChart } from '../components/dashboard/ErrorDistributionChart';
import { TopAnomalousClusters } from '../components/dashboard/TopAnomalousClusters';
import { LiveAnomalyFeed } from '../components/dashboard/LiveAnomalyFeed';
import { getDashboardMetrics } from '../utils/dataTransformations';
import { usePolling } from '../hooks';

export function Dashboard() {
  const [timeRange, setTimeRange] = useState('5m');
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Fetch real metrics from backend using data transformation
  const { data: metrics, loading: metricsLoading } = usePolling(
    () => getDashboardMetrics(),
    5000,
    autoRefresh
  );

  const getHealthColor = (value: number) => {
    if (value >= 95) return '#10b981';
    if (value >= 85) return '#f59e0b';
    return '#ef4444';
  };

  const getHealthIcon = (value: number) => {
    if (value >= 95) return <Activity size={16} />;
    return <AlertTriangle size={16} />;
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* Header Controls */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '16px 20px',
          background: '#ffffff',
          borderRadius: 12,
          border: '1px solid #e2e8f0',
          boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1)',
        }}
      >
        <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
          <select
            value={timeRange}
            onChange={(e: any) => setTimeRange(e.target.value)}
            style={{
              padding: '8px 12px',
              border: '1px solid #d1d5db',
              borderRadius: 8,
              fontSize: '14px',
              background: '#ffffff',
              cursor: 'pointer',
            }}
          >
            <option value="5m">Last 5 min</option>
            <option value="15m">Last 15 min</option>
            <option value="1h">Last 1 hour</option>
            <option value="6h">Last 6 hours</option>
            <option value="24h">Last 24 hours</option>
          </select>

          <label
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              fontSize: '14px',
              color: '#374151',
              cursor: 'pointer',
            }}
          >
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e: { target: { checked: boolean } }) => setAutoRefresh(e.target.checked)}
              style={{ cursor: 'pointer' }}
            />
            Auto-refresh
          </label>
        </div>

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            fontSize: '12px',
            color: '#6b7280',
          }}
        >
          {metricsLoading ? 'Loading...' : `Last updated: just now`}
        </div>
      </div>

      {/* Key Metrics */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: 20,
        }}
      >
        {/* System Health */}
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
              alignItems: 'center',
              gap: 12,
              marginBottom: 12,
            }}
          >
            <div
              style={{
                padding: 8,
                borderRadius: 8,
                background: `${getHealthColor(metrics?.systemHealth || 0)}20`,
                color: getHealthColor(metrics?.systemHealth || 0),
              }}
            >
              {getHealthIcon(metrics?.systemHealth || 0)}
            </div>
            <div>
              <div
                style={{ fontSize: '14px', color: '#6b7280', marginBottom: 4 }}
              >
                System Health
              </div>
              <div
                style={{
                  fontSize: '32px',
                  fontWeight: '600',
                  color: '#1f2937',
                }}
              >
                {metrics?.systemHealth || 0}/100
              </div>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            {(metrics?.systemHealth || 0) > 90 ? (
              <TrendingUp size={14} color="#10b981" />
            ) : (
              <TrendingDown size={14} color="#ef4444" />
            )}
            <span
              style={{
                fontSize: '12px',
                color:
                  (metrics?.systemHealth || 0) > 90 ? '#10b981' : '#ef4444',
              }}
            >
              {(metrics?.systemHealth || 0) > 90
                ? 'Healthy'
                : 'Needs Attention'}
            </span>
          </div>
        </div>

        {/* Active Incidents */}
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
              alignItems: 'center',
              gap: 12,
              marginBottom: 12,
            }}
          >
            <div
              style={{
                padding: 8,
                borderRadius: 8,
                background: '#fef2f2',
                color: '#dc2626',
              }}
            >
              <AlertTriangle size={16} />
            </div>
            <div>
              <div
                style={{ fontSize: '14px', color: '#6b7280', marginBottom: 4 }}
              >
                Active Incidents
              </div>
              <div
                style={{
                  fontSize: '32px',
                  fontWeight: '600',
                  color: '#1f2937',
                }}
              >
                {metrics?.activeIncidents || 0}
              </div>
            </div>
          </div>
          <div style={{ fontSize: '12px', color: '#dc2626' }}>
            {(metrics?.activeIncidents || 0) > 0
              ? 'Requires immediate attention'
              : 'No active incidents'}
          </div>
        </div>

        {/* Anomaly Rate */}
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
              alignItems: 'center',
              gap: 12,
              marginBottom: 12,
            }}
          >
            <div
              style={{
                padding: 8,
                borderRadius: 8,
                background:
                  (metrics?.anomalyRate || 0) > 5 ? '#fef2f2' : '#f0fdf4',
                color: (metrics?.anomalyRate || 0) > 5 ? '#dc2626' : '#16a34a',
              }}
            >
              <Activity size={16} />
            </div>
            <div>
              <div
                style={{ fontSize: '14px', color: '#6b7280', marginBottom: 4 }}
              >
                Anomaly Rate
              </div>
              <div
                style={{
                  fontSize: '32px',
                  fontWeight: '600',
                  color: '#1f2937',
                }}
              >
                {(metrics?.anomalyRate || 0).toFixed(1)}%
              </div>
            </div>
          </div>
          <div
            style={{
              fontSize: '12px',
              color: (metrics?.anomalyRate || 0) > 5 ? '#dc2626' : '#16a34a',
            }}
          >
            {(metrics?.anomalyRate || 0) > 5
              ? 'Above threshold'
              : 'Within normal range'}
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
          gap: 20,
        }}
      >
        <ClusterStabilityChart />
        <AnomalyTrendChart />
        <ErrorDistributionChart />
      </div>

      {/* Bottom Sections */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 20,
        }}
      >
        <TopAnomalousClusters />
        <LiveAnomalyFeed />
      </div>
    </div>
  );
}
