'use client';

import React, { useEffect, useState, use } from 'react';
import { TraceDetailWaterfallUI } from '@/features/traces/ui/TraceDetailWaterfallUI';
import type { TraceDetailResult } from '@/features/traces/types';

export default function TraceDetailPage({ params }: { params: Promise<{ traceId: string }> }) {
  const resolvedParams = use(params);
  const [trace, setTrace] = useState<TraceDetailResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    async function load() {
      setLoading(true);
      try {
        const res = await fetch(`/api/v1/traces/${resolvedParams.traceId}`);
        if (!res.ok) throw new Error(`Failed to load trace ${resolvedParams.traceId}`);
        const data = await res.json();
        if (isMounted) {
          setTrace(data);
          setLoading(false);
        }
      } catch (err: any) {
        if (isMounted) {
          setError(err.message || "Failed to load trace details");
          setLoading(false);
        }
      }
    }
    load();
    return () => { isMounted = false; };
  }, [resolvedParams.traceId]);

  return (
    <TraceDetailWaterfallUI
      trace={trace}
      loading={loading}
      error={error}
    />
  );
}
