import { api } from '../lib/api';
import { useState } from 'react';

export function FlushTriggerPanel() {
  const [pending, setPending] = useState(false);
  const [data, setData] = useState<unknown>(undefined);
  return (
    <section>
      <button onClick={async () => {
        setPending(true);
        try {
          setData(await api.flush());
        } finally {
          setPending(false);
        }
      }} disabled={pending}>Flush</button>
      {data && (
        <pre>{JSON.stringify(data, null, 2)}</pre>
      )}
    </section>
  );
}
