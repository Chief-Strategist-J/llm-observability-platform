import { api } from '../api';
import { usePolling } from '../hooks';

export function HealthStatusBar() {
  const { data, error } = usePolling(api.health, 10_000);
  if (error)
    return (
      <div
        style={{
          background: '#fef2f2',
          border: '1px solid #fecaca',
          borderRadius: 8,
          padding: '12px 16px',
          display: 'flex',
          alignItems: 'center',
          gap: 8,
        }}
      >
        <div
          style={{
            width: 8,
            height: 8,
            borderRadius: '50%',
            background: '#dc2626',
          }}
        />
        <span style={{ color: '#991b1b', fontSize: '14px', fontWeight: '500' }}>
          Backend: Unreachable
        </span>
      </div>
    );

  return (
    <div
      style={{
        background: '#f0fdf4',
        border: '1px solid #bbf7d0',
        borderRadius: 8,
        padding: '12px 16px',
        display: 'flex',
        alignItems: 'center',
        gap: 8,
      }}
    >
      <div
        style={{
          width: 8,
          height: 8,
          borderRadius: '50%',
          background: '#16a34a',
          animation: 'pulse 2s infinite',
        }}
      />
      <span style={{ color: '#166534', fontSize: '14px', fontWeight: '500' }}>
        Backend: {data?.status ?? 'loading'} | Version {data?.version ?? '...'}
      </span>
    </div>
  );
}
