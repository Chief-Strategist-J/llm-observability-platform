import { Clock, Activity, MapPin } from 'lucide-react';
import { getIncidents } from '../utils/dataTransformations';
import { usePolling } from '../hooks';

export function Incidents() {
  // Fetch real incidents data from backend using data transformation
  const { data: incidents, loading: incidentsLoading } = usePolling(
    () => getIncidents(),
    5000
  );

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return '#dc2626';
      case 'high':
        return '#f59e0b';
      case 'medium':
        return '#3b82f6';
      case 'low':
        return '#10b981';
      default:
        return '#6b7280';
    }
  };

  const getSeverityBg = (severity: string) => {
    switch (severity) {
      case 'critical':
        return '#fef2f2';
      case 'high':
        return '#fef3c7';
      case 'medium':
        return '#dbeafe';
      case 'low':
        return '#f0fdf4';
      default:
        return '#f3f4f6';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return '#dc2626';
      case 'investigating':
        return '#f59e0b';
      case 'resolved':
        return '#10b981';
      default:
        return '#6b7280';
    }
  };

  const getStatusBg = (status: string) => {
    switch (status) {
      case 'active':
        return '#fef2f2';
      case 'investigating':
        return '#fef3c7';
      case 'resolved':
        return '#f0fdf4';
      default:
        return '#f3f4f6';
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
        <h2
          style={{
            margin: 0,
            fontSize: '20px',
            fontWeight: '600',
            color: '#1f2937',
          }}
        >
          Incidents
        </h2>
        <p
          style={{
            margin: '8px 0 0 0',
            fontSize: '14px',
            color: '#6b7280',
          }}
        >
          Track, investigate, and resolve system incidents and anomalies
        </p>
      </div>

      {/* Incidents List */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: 16,
        }}
      >
        {incidentsLoading ? (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: 40,
              color: '#6b7280',
            }}
          >
            Loading incidents data...
          </div>
        ) : (
          (incidents || []).map(incident => (
            <div
              key={incident.id}
              style={{
                background: '#ffffff',
                borderRadius: 12,
                border: '1px solid #e2e8f0',
                padding: 20,
                boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1)',
              }}
            >
              {/* Incident Header */}
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'flex-start',
                  marginBottom: 16,
                }}
              >
                <div style={{ flex: 1 }}>
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 12,
                      marginBottom: 8,
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
                      {incident.title}
                    </h3>

                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 8,
                      }}
                    >
                      <span
                        style={{
                          padding: '4px 8px',
                          borderRadius: 6,
                          fontSize: '12px',
                          fontWeight: '500',
                          background: getSeverityBg(incident.severity),
                          color: getSeverityColor(incident.severity),
                          textTransform: 'capitalize',
                        }}
                      >
                        {incident.severity}
                      </span>

                      <span
                        style={{
                          padding: '4px 8px',
                          borderRadius: 6,
                          fontSize: '12px',
                          fontWeight: '500',
                          background: getStatusBg(incident.status),
                          color: getStatusColor(incident.status),
                          textTransform: 'capitalize',
                        }}
                      >
                        {incident.status}
                      </span>
                    </div>
                  </div>

                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 16,
                      fontSize: '14px',
                      color: '#6b7280',
                    }}
                  >
                    <div
                      style={{ display: 'flex', alignItems: 'center', gap: 4 }}
                    >
                      <Clock size={14} />
                      <span>Start: {incident.startTime}</span>
                    </div>

                    <div
                      style={{ display: 'flex', alignItems: 'center', gap: 4 }}
                    >
                      <Activity size={14} />
                      <span>Impact: {incident.impact}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Incident Details */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: 20,
                  marginBottom: 16,
                }}
              >
                <div>
                  <h4
                    style={{
                      margin: '0 0 8px 0',
                      fontSize: '14px',
                      fontWeight: '600',
                      color: '#374151',
                    }}
                  >
                    Root Cause
                  </h4>
                  <p
                    style={{
                      margin: 0,
                      fontSize: '14px',
                      color: '#6b7280',
                      lineHeight: 1.4,
                    }}
                  >
                    {incident.rootCause}
                  </p>
                </div>

                <div>
                  <h4
                    style={{
                      margin: '0 0 8px 0',
                      fontSize: '14px',
                      fontWeight: '600',
                      color: '#374151',
                    }}
                  >
                    Blast Radius
                  </h4>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                    {incident.blastRadius.map((service, index) => (
                      <span
                        key={index}
                        style={{
                          padding: '4px 8px',
                          borderRadius: 6,
                          fontSize: '12px',
                          background: '#f3f4f6',
                          color: '#374151',
                          display: 'flex',
                          alignItems: 'center',
                          gap: 4,
                        }}
                      >
                        <MapPin size={12} />
                        {service}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Recommended Actions */}
              <div>
                <h4
                  style={{
                    margin: '0 0 8px 0',
                    fontSize: '14px',
                    fontWeight: '600',
                    color: '#374151',
                  }}
                >
                  Recommended Actions
                </h4>
                <ul
                  style={{
                    margin: 0,
                    paddingLeft: 20,
                    fontSize: '14px',
                    color: '#6b7280',
                    lineHeight: 1.4,
                  }}
                >
                  {incident.recommendedActions.map((action, index) => (
                    <li key={index}>{action}</li>
                  ))}
                </ul>
              </div>
            </div>
          ))
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
            {(incidents || []).filter(i => i.status === 'active').length}
          </div>
          <div style={{ fontSize: '12px', color: '#6b7280', marginTop: 4 }}>
            Active Incidents
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
            {(incidents || []).filter(i => i.status === 'investigating').length}
          </div>
          <div style={{ fontSize: '12px', color: '#6b7280', marginTop: 4 }}>
            Investigating
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
            style={{ fontSize: '24px', fontWeight: '600', color: '#dc2626' }}
          >
            {(incidents || []).filter(i => i.severity === 'critical').length}
          </div>
          <div style={{ fontSize: '12px', color: '#6b7280', marginTop: 4 }}>
            Critical
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
            {(incidents || []).filter(i => i.status === 'resolved').length}
          </div>
          <div style={{ fontSize: '12px', color: '#6b7280', marginTop: 4 }}>
            Resolved Today
          </div>
        </div>
      </div>
    </div>
  );
}
