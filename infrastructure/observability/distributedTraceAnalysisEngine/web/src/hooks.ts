import { useEffect, useState, useCallback, useRef } from 'react';

// Simple cache for API responses
interface CacheEntry<T> {
  data: T;
  timestamp: number;
  hash: string;
}

const globalCache = new Map<string, CacheEntry<unknown>>();

// Type-safe cache getter
function getCachedData<T>(cacheKey: string): T | null {
  const cached = globalCache.get(cacheKey);
  if (cached && (Date.now() - cached.timestamp) < 60000) {
    return cached.data as T;
  }
  return null;
}

// Type-safe cache setter
function setCachedData<T>(cacheKey: string, data: T, hash: string): void {
  globalCache.set(cacheKey, {
    data,
    timestamp: Date.now(),
    hash
  });
}

// Generate a simple hash for caching
function generateHash(data: unknown): string {
  if (Array.isArray(data)) {
    return JSON.stringify(data.map(item => 
      typeof item === 'object' && item !== null ? (item as Record<string, unknown>).id || (item as Record<string, unknown>).span_id || JSON.stringify(item) : item
    ).sort());
  }
  return JSON.stringify(data);
}

export function usePolling<T>(
  fetcher: () => Promise<T>,
  intervalMs: number,
  enabled = true,
  cacheKey?: string
) {
  const [data, setData] = useState<T | undefined>(undefined);
  const [error, setError] = useState<string | undefined>(undefined);
  const [loading, setLoading] = useState(true);
  const fetcherRef = useRef(fetcher);
  const intervalRef = useRef(intervalMs);
  const enabledRef = useRef(enabled);
  const lastFetchRef = useRef<number>(0);
  const lastDataHashRef = useRef<string>('');

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

    // Prevent excessive polling - only run if enough time has passed
    const now = Date.now();
    if (now - lastFetchRef.current < intervalRef.current * 0.8) {
      return; // Don't poll if we recently fetched
    }

    try {
      setLoading(true);
      lastFetchRef.current = now;
      
      const res = await fetcherRef.current();
      
      // Generate hash for comparison
      const dataHash = generateHash(res);
      
      // Check if data has actually changed
      if (dataHash === lastDataHashRef.current) {
        // Data is the same, don't update state
        setLoading(false);
        return;
      }
      
      // Cache the response if cache key provided
      if (cacheKey) {
        setCachedData(cacheKey, res, dataHash);
      }
      
      setData(res);
      setError(undefined);
      lastDataHashRef.current = dataHash;
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, [intervalMs, cacheKey]);

  useEffect(() => {
    if (!enabled) return;

    // Check cache first
    if (cacheKey) {
      const cached = getCachedData<T>(cacheKey);
      if (cached) {
        // Use cached data if it's fresh
        setData(cached);
        setError(undefined);
        lastDataHashRef.current = generateHash(cached);
        setLoading(false);
      }
    }

    const timer = setInterval(run, intervalMs);
    run(); // Initial run

    return () => {
      clearInterval(timer);
    };
  }, [run, intervalMs, enabled, cacheKey]);

  return { data, error, loading };
}
