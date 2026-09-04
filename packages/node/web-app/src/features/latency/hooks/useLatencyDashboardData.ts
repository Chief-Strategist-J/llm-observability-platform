'use client';

import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import type { RootState } from "../../../core/store/configure-store";
import type { DashboardFilters } from "../../../hooks/useDashboardFilters";

import { latencyActions } from "../latency.slice";
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
  const dispatch = useDispatch();
  const latencyState = useSelector((state: RootState) => state.latency);

  useEffect(() => {
    dispatch(
      latencyActions.fetchLatencySubmitted({
        model: filters.model || "gpt-4",
        hourOfDay: new Date().getHours(),
        days: 7,
      })
    );
  }, [dispatch, filters.model, filters.timeRange, filters.service, filters.environment]);

  return {
    percentiles: latencyState?.percentiles || null,
    slo: latencyState?.slo || null,
    attribution: latencyState?.attribution || null,
    baseline: latencyState?.baseline || [],
    loading: latencyState?.status === "loading",
    error: latencyState?.error || null,
  };
}


