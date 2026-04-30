import {
  Settings as SettingsIcon,
  Database,
  Bell,
  Shield,
  Palette,
} from 'lucide-react';
import { useState } from 'react';

export function Settings() {
  const [activeTab, setActiveTab] = useState('general');

  const tabs = [
    { id: 'general', name: 'General', icon: SettingsIcon },
    { id: 'data', name: 'Data & Storage', icon: Database },
    { id: 'alerts', name: 'Alerts', icon: Bell },
    { id: 'security', name: 'Security', icon: Shield },
    { id: 'appearance', name: 'Appearance', icon: Palette },
  ];

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
          Settings
        </h2>
        <p
          style={{
            margin: '8px 0 0 0',
            fontSize: '14px',
            color: '#6b7280',
          }}
        >
          Configure system settings, preferences, and operational parameters
        </p>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '250px 1fr',
          gap: 20,
          height: 'calc(100vh - 200px)',
        }}
      >
        {/* Sidebar */}
        <div
          style={{
            background: '#ffffff',
            borderRadius: 12,
            border: '1px solid #e2e8f0',
            padding: 16,
            boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1)',
          }}
        >
          <nav style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {tabs.map(tab => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12,
                    padding: '12px',
                    borderRadius: 8,
                    border: 'none',
                    background:
                      activeTab === tab.id ? '#dbeafe' : 'transparent',
                    color: activeTab === tab.id ? '#1d4ed8' : '#6b7280',
                    cursor: 'pointer',
                    fontSize: '14px',
                    fontWeight: activeTab === tab.id ? '500' : 'normal',
                    transition: 'all 0.2s ease',
                    width: '100%',
                    textAlign: 'left',
                  }}
                  onMouseEnter={e => {
                    if (activeTab !== tab.id) {
                      e.currentTarget.style.background = '#f3f4f6';
                    }
                  }}
                  onMouseLeave={e => {
                    if (activeTab !== tab.id) {
                      e.currentTarget.style.background = 'transparent';
                    }
                  }}
                >
                  <Icon size={18} />
                  <span>{tab.name}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Content */}
        <div
          style={{
            background: '#ffffff',
            borderRadius: 12,
            border: '1px solid #e2e8f0',
            padding: 24,
            boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1)',
            overflow: 'auto',
          }}
        >
          {activeTab === 'general' && <GeneralSettings />}
          {activeTab === 'data' && <DataSettings />}
          {activeTab === 'alerts' && <AlertSettings />}
          {activeTab === 'security' && <SecuritySettings />}
          {activeTab === 'appearance' && <AppearanceSettings />}
        </div>
      </div>
    </div>
  );
}

function GeneralSettings() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <h3
        style={{
          margin: 0,
          fontSize: '18px',
          fontWeight: '600',
          color: '#1f2937',
        }}
      >
        General Settings
      </h3>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
        <div>
          <label
            style={{
              display: 'block',
              fontSize: '14px',
              fontWeight: '500',
              color: '#374151',
              marginBottom: 8,
            }}
          >
            System Name
          </label>
          <input
            type="text"
            defaultValue="DTAE Platform"
            style={{
              width: '100%',
              maxWidth: 400,
              padding: '8px 12px',
              border: '1px solid #d1d5db',
              borderRadius: 6,
              fontSize: '14px',
            }}
          />
        </div>

        <div>
          <label
            style={{
              display: 'block',
              fontSize: '14px',
              fontWeight: '500',
              color: '#374151',
              marginBottom: 8,
            }}
          >
            Default Time Range
          </label>
          <select
            style={{
              width: '100%',
              maxWidth: 400,
              padding: '8px 12px',
              border: '1px solid #d1d5db',
              borderRadius: 6,
              fontSize: '14px',
            }}
          >
            <option>Last 5 minutes</option>
            <option>Last 15 minutes</option>
            <option>Last 1 hour</option>
            <option>Last 6 hours</option>
            <option>Last 24 hours</option>
          </select>
        </div>

        <div>
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
            <input type="checkbox" defaultChecked />
            <span>Auto-refresh dashboard</span>
          </label>
        </div>
      </div>
    </div>
  );
}

function DataSettings() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <h3
        style={{
          margin: 0,
          fontSize: '18px',
          fontWeight: '600',
          color: '#1f2937',
        }}
      >
        Data & Storage
      </h3>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
        <div>
          <label
            style={{
              display: 'block',
              fontSize: '14px',
              fontWeight: '500',
              color: '#374151',
              marginBottom: 8,
            }}
          >
            Data Retention Period
          </label>
          <select
            style={{
              width: '100%',
              maxWidth: 400,
              padding: '8px 12px',
              border: '1px solid #d1d5db',
              borderRadius: 6,
              fontSize: '14px',
            }}
          >
            <option>7 days</option>
            <option>30 days</option>
            <option>90 days</option>
            <option>1 year</option>
          </select>
        </div>

        <div>
          <label
            style={{
              display: 'block',
              fontSize: '14px',
              fontWeight: '500',
              color: '#374151',
              marginBottom: 8,
            }}
          >
            Maximum Traces per Cluster
          </label>
          <input
            type="number"
            defaultValue="10000"
            style={{
              width: '100%',
              maxWidth: 400,
              padding: '8px 12px',
              border: '1px solid #d1d5db',
              borderRadius: 6,
              fontSize: '14px',
            }}
          />
        </div>
      </div>
    </div>
  );
}

function AlertSettings() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <h3
        style={{
          margin: 0,
          fontSize: '18px',
          fontWeight: '600',
          color: '#1f2937',
        }}
      >
        Alert Configuration
      </h3>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
        <div>
          <label
            style={{
              display: 'block',
              fontSize: '14px',
              fontWeight: '500',
              color: '#374151',
              marginBottom: 8,
            }}
          >
            Anomaly Threshold
          </label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.1"
            defaultValue="0.7"
            style={{ width: '100%', maxWidth: 400 }}
          />
          <div style={{ fontSize: '12px', color: '#6b7280', marginTop: 4 }}>
            Current: 70%
          </div>
        </div>

        <div>
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
            <input type="checkbox" defaultChecked />
            <span>Email notifications</span>
          </label>
        </div>

        <div>
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
            <input type="checkbox" defaultChecked />
            <span>Slack integration</span>
          </label>
        </div>
      </div>
    </div>
  );
}

function SecuritySettings() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <h3
        style={{
          margin: 0,
          fontSize: '18px',
          fontWeight: '600',
          color: '#1f2937',
        }}
      >
        Security Settings
      </h3>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
        <div>
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
            <input type="checkbox" defaultChecked />
            <span>Enable authentication</span>
          </label>
        </div>

        <div>
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
            <input type="checkbox" defaultChecked />
            <span>Session timeout (30 min)</span>
          </label>
        </div>
      </div>
    </div>
  );
}

function AppearanceSettings() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <h3
        style={{
          margin: 0,
          fontSize: '18px',
          fontWeight: '600',
          color: '#1f2937',
        }}
      >
        Appearance
      </h3>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
        <div>
          <label
            style={{
              display: 'block',
              fontSize: '14px',
              fontWeight: '500',
              color: '#374151',
              marginBottom: 8,
            }}
          >
            Theme
          </label>
          <select
            style={{
              width: '100%',
              maxWidth: 400,
              padding: '8px 12px',
              border: '1px solid #d1d5db',
              borderRadius: 6,
              fontSize: '14px',
            }}
          >
            <option>Light</option>
            <option>Dark</option>
            <option>System</option>
          </select>
        </div>

        <div>
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
            <input type="checkbox" defaultChecked />
            <span>Compact mode</span>
          </label>
        </div>
      </div>
    </div>
  );
}
