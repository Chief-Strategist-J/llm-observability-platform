import { useEffect, useState, useCallback, useRef } from 'react';

export function usePolling<T>(
  fetcher: () => Promise<T>,
  intervalMs: number,
  enabled = true
) {
  const [data, setData] = useState<T | undefined>(undefined);
  const [error, setError] = useState<string | undefined>(undefined);
  const [loading, setLoading] = useState(true);
  const fetcherRef = useRef(fetcher);
  const intervalRef = useRef(intervalMs);
  const enabledRef = useRef(enabled);

  // Update refs when values change
  useEffect(() => {
    fetcherRef.current = fetcher;
  }, [fetcher]);

  useEffect(() => {
    intervalRef.current = intervalMs;
  }, [intervalMs]);

  useEffect(() => {
    enabledRef.current = enabled;
  }, [enabled]);

  const run = useCallback(async () => {
    if (!enabledRef.current) return;

    try {
      setLoading(true);
      const res = await fetcherRef.current();
      setData(res);
      setError(undefined);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!enabled) return;

    const timer = setInterval(run, intervalMs);
    run(); // Initial run

    return () => {
      clearInterval(timer);
    };
  }, [run, intervalMs, enabled]);

  return { data, error, loading };
}
