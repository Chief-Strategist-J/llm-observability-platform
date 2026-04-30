import { useEffect, useState } from 'react';

export function usePolling<T>(fetcher: () => Promise<T>, intervalMs: number, enabled = true) {
  const [data, setData] = useState<T | undefined>(undefined);
  const [error, setError] = useState<string | undefined>(undefined);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!enabled) return;
    let active = true;

    const run = async () => {
      try {
        setLoading(true);
        const res = await fetcher();
        if (!active) return;
        setData(res);
        setError(undefined);
      } catch (e) {
        if (!active) return;
        setError(e instanceof Error ? e.message : 'Unknown error');
      } finally {
        if (active) setLoading(false);
      }
    };

    run();
    const timer = setInterval(run, intervalMs);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [fetcher, intervalMs, enabled]);

  return { data, error, loading };
}
