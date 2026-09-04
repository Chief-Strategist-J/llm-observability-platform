'use client';

import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import type { RootState } from "../../../core/store/configure-store";
import type { DashboardFilters } from "../../../hooks/useDashboardFilters";

import { qualityActions } from "../quality.slice";
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
  const dispatch = useDispatch();
  const qualityState = useSelector((state: RootState) => state.quality);

  useEffect(() => {
    dispatch(
      qualityActions.fetchQualitySubmitted({
        model: filters.model || "gpt-4o",
        timeRange: filters.timeRange || "24h",
        service: filters.service,
        days: 7,
      })
    );
  }, [dispatch, filters.model, filters.timeRange, filters.service, filters.environment]);

  return {
    summary: qualityState?.summary || null,
    trend: qualityState?.trend || [],
    models: qualityState?.models || [],
    flaggedAlerts: qualityState?.flaggedAlerts || [],
    loading: qualityState?.status === "loading",
    error: qualityState?.error || null,
  };
}


