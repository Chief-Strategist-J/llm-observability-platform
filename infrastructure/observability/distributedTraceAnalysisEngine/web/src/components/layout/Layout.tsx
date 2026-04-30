import { Outlet, Link, useLocation } from 'react-router-dom';
import {
  Search,
  Menu,
  X,
  Activity,
  Server,
  Network,
  GitBranch,
  AlertTriangle,
  Settings,
  User,
} from 'lucide-react';
import { useState } from 'react';

const navigation = [
  { name: 'Dashboard', href: '/', icon: Activity },
  { name: 'Services', href: '/services', icon: Server },
  { name: 'Clusters', href: '/clusters', icon: Network },
  { name: 'Traces', href: '/traces', icon: GitBranch },
  { name: 'Incidents', href: '/incidents', icon: AlertTriangle },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  return (
    <div
      className="app"
      style={{
        fontFamily: 'Inter, system-ui, sans-serif',
        height: '100vh',
        overflow: 'hidden',
        background: '#f8fafc',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Header */}
      <header
        style={{
          height: 64,
          borderBottom: '1px solid #e2e8f0',
          background: '#ffffff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 24px',
          boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.05)',
          zIndex: 50,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              padding: 8,
              borderRadius: 6,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div
              style={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                background: '#10b981',
              }}
            />
            <strong style={{ fontSize: '20px', color: '#1f2937' }}>
              DTAE Platform
            </strong>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          {/* Global Search */}
          <div style={{ position: 'relative' }}>
            <Search
              size={16}
              style={{
                position: 'absolute',
                left: 12,
                top: '50%',
                transform: 'translateY(-50%)',
                color: '#6b7280',
              }}
            />
            <input
              placeholder="Search traces / services..."
              style={{
                width: 320,
                border: '1px solid #d1d5db',
                borderRadius: 8,
                padding: '8px 12px 8px 36px',
                fontSize: '14px',
                background: '#f9fafb',
                outline: 'none',
              }}
            />
          </div>

          {/* User Menu */}
          <button
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '8px 12px',
              border: '1px solid #e5e7eb',
              borderRadius: 8,
              background: '#ffffff',
              cursor: 'pointer',
              fontSize: '14px',
              color: '#374151',
            }}
          >
            <User size={16} />
            <span>Admin</span>
          </button>
        </div>
      </header>

      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Sidebar */}
        <aside
          style={{
            width: sidebarOpen ? 256 : 0,
            borderRight: '1px solid #e2e8f0',
            background: '#ffffff',
            transition: 'width 0.3s ease',
            overflow: 'hidden',
            display: sidebarOpen ? 'block' : 'none',
          }}
        >
          <div style={{ padding: 20 }}>
            <div
              style={{
                fontSize: '12px',
                color: '#6b7280',
                marginBottom: 16,
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                fontWeight: 500,
              }}
            >
              Enterprise Observability
            </div>
            <nav style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              {navigation.map(item => {
                const Icon = item.icon;
                const isActive =
                  location.pathname === item.href ||
                  (item.href !== '/' &&
                    location.pathname.startsWith(item.href));

                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 12,
                      padding: '12px',
                      borderRadius: 8,
                      textDecoration: 'none',
                      color: isActive ? '#1d4ed8' : '#6b7280',
                      background: isActive ? '#dbeafe' : 'transparent',
                      fontWeight: isActive ? 500 : 'normal',
                      transition: 'all 0.2s ease',
                      cursor: 'pointer',
                    }}
                    onMouseEnter={(e: React.MouseEvent<HTMLDivElement>) => {
                      if (!isActive) {
                        e.currentTarget.style.background = '#f3f4f6';
                      }
                    }}
                    onMouseLeave={(e: React.MouseEvent<HTMLDivElement>) => {
                      if (!isActive) {
                        e.currentTarget.style.background = 'transparent';
                      }
                    }}
                  >
                    <Icon size={18} />
                    <span>{item.name}</span>
                  </Link>
                );
              })}
            </nav>
          </div>
        </aside>

        {/* Main Content */}
        <main
          style={{
            flex: 1,
            overflow: 'auto',
            padding: 24,
            background: '#f8fafc',
          }}
        >
          <Outlet />
        </main>
      </div>
    </div>
  );
}
