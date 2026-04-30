import { api } from '../lib/api';
import { usePolling } from '../hooks';

export function HealthStatusBar() {
  const { data, error } = usePolling(api.health, 10_000);
  if (error) return <div style={{ background: '#7f1d1d', color: 'white', padding: 8 }}>Backend: unreachable</div>;
  return <div style={{ background: '#111827', color: 'white', padding: 8 }}>Backend: {data?.status ?? 'loading'} | v{data?.version ?? '...'}</div>;
}
