import { api } from '../api';
import { useState } from 'react';

export function FlushTriggerPanel() {
  const [pending, setPending] = useState(false);
  const [flushed, setFlushed] = useState(false);
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <button
          onClick={async () => {
            setPending(true);
            setFlushed(false);
            try {
              await api.flush();
              setFlushed(true);
              setTimeout(() => setFlushed(false), 3000);
            } finally {
              setPending(false);
            }
          }}
          disabled={pending}
          style={{
            padding: '10px 20px',
            border: 'none',
            borderRadius: 8,
            fontSize: '14px',
            fontWeight: '500',
            cursor: pending ? 'not-allowed' : 'pointer',
            background: pending ? '#d1d5db' : '#3b82f6',
            color: 'white',
            transition: 'all 0.2s',
            minWidth: '100px',
          }}
        >
          {pending ? 'Processing...' : 'Trigger Flush'}
        </button>
        <span style={{ fontSize: '14px', color: '#6b7280' }}>
          Manually trigger trace analysis and clustering
        </span>
      </div>
      {flushed && (
        <div
          style={{
            padding: '12px 16px',
            background: '#dcfce7',
            border: '1px solid #bbf7d0',
            borderRadius: 8,
            color: '#166534',
            fontSize: '14px',
          }}
        >
          Flush triggered successfully - traces are being analyzed
        </div>
      )}
    </div>
  );
}
