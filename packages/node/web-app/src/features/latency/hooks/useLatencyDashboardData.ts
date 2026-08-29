'use client';

import { useEffect, useState } from "react";
import type { DashboardFilters } from "@/hooks/useDashboardFilters";
import type { PercentilesResult, SLOResult, AttributionResult, BaselinePoint } from "../types";

export interface LatencyDashboardState {
  percentiles: PercentilesResult | null;
  slo: SLOResult | null;
  attribution: AttributionResult | null;
  baseline: BaselinePoint[];
  loading: boolean;
  error: string | null;
}

export function useLatencyDashboardData(filters: DashboardFilters): LatencyDashboardState {
  const [state, setState] = useState<LatencyDashboardState>({
    percentiles: null,
    slo: null,
    attribution: null,
    baseline: [],
    loading: true,
    error: null,
  });

  useEffect(() => {
    let isMounted = true;
    async function load() {
      setState((prev) => ({ ...prev, loading: true }));
      const model = filters.model || "gpt-4";
      const hourOfDay = new Date().getHours();
      const todayStr = new Date().toISOString().substring(0, 10);

      try {
        const [pRes, sRes, aRes, bRes] = await Promise.all([
          fetch(`/api/v1/latency/percentiles?model=${encodeURIComponent(model)}&hour_of_day=${hourOfDay}`),
          fetch(`/api/v1/latency/slo?model=${encodeURIComponent(model)}&endpoint=/v1/chat/completions`),
          fetch(`/api/v1/latency/attribution?model=${encodeURIComponent(model)}&hour=${todayStr}`),
          fetch(`/api/v1/latency/baseline?model=${encodeURIComponent(model)}&hour_of_day=${hourOfDay}&days=7`),
        ]);

        const [pData, sData, aData, bData] = await Promise.all([
          pRes.ok ? pRes.json() : null,
          sRes.ok ? sRes.json() : null,
          aRes.ok ? aRes.json() : null,
          bRes.ok ? bRes.json() : [],
        ]);

        if (isMounted) {
          setState({
            percentiles: pData,
            slo: sData,
            attribution: aData,
            baseline: Array.isArray(bData) ? bData : [],
            loading: false,
            error: null,
          });
        }
      } catch (err: any) {
        if (isMounted) {
          setState((prev) => ({
            ...prev,
            loading: false,
            error: err.message || "Failed to fetch latency metrics",
          }));
        }
      }
    }

    load();
    return () => { isMounted = false; };
  }, [filters.model, filters.timeRange, filters.service, filters.environment]);

  return state;
}
