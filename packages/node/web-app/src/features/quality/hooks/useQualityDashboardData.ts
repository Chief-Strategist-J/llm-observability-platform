'use client';

import { useEffect, useState } from "react";
import type { DashboardFilters } from "@/hooks/useDashboardFilters";
import type {
  QualitySummaryResult,
  QualityTrendPoint,
  ModelQualityBreakdown,
  FlaggedContentAlert,
} from "../types";

export interface QualityDashboardState {
  summary: QualitySummaryResult | null;
  trend: QualityTrendPoint[];
  models: ModelQualityBreakdown[];
  flaggedAlerts: FlaggedContentAlert[];
  loading: boolean;
  error: string | null;
}

export function useQualityDashboardData(filters: DashboardFilters): QualityDashboardState {
  const [state, setState] = useState<QualityDashboardState>({
    summary: null,
    trend: [],
    models: [],
    flaggedAlerts: [],
    loading: true,
    error: null,
  });

  useEffect(() => {
    let isMounted = true;
    async function load() {
      setState((prev) => ({ ...prev, loading: true }));
      const model = filters.model || "gpt-4o";
      const timeRange = filters.timeRange || "24h";

      try {
        const [sumRes, trRes, modRes, flRes] = await Promise.all([
          fetch(`/api/v1/quality/summary?model=${encodeURIComponent(model)}&time_range=${encodeURIComponent(timeRange)}`),
          fetch(`/api/v1/quality/trend?model=${encodeURIComponent(model)}&days=7`),
          fetch(`/api/v1/quality/models?time_range=${encodeURIComponent(timeRange)}`),
          fetch(`/api/v1/quality/flagged?limit=20`),
        ]);

        const [sumData, trData, modData, flData] = await Promise.all([
          sumRes.ok ? sumRes.json() : null,
          trRes.ok ? trRes.json() : [],
          modRes.ok ? modRes.json() : [],
          flRes.ok ? flRes.json() : [],
        ]);

        if (isMounted) {
          setState({
            summary: sumData,
            trend: Array.isArray(trData) ? trData : [],
            models: Array.isArray(modData) ? modData : [],
            flaggedAlerts: Array.isArray(flData) ? flData : [],
            loading: false,
            error: null,
          });
        }
      } catch (err: any) {
        if (isMounted) {
          setState((prev) => ({
            ...prev,
            loading: false,
            error: err.message || "Failed to fetch quality evaluation metrics",
          }));
        }
      }
    }

    load();
    return () => { isMounted = false; };
  }, [filters.model, filters.timeRange, filters.service, filters.environment]);

  return state;
}
