'use client';

import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import type { RootState } from "@/core/store/configure-store";
import type { DashboardFilters } from "@/hooks/useDashboardFilters";
import { overviewActions } from "../overview.slice";
import type { OverviewKPIAggregates, SystemHealthSLOBanner, RecentTracePreview } from "../types";

export interface OverviewDashboardState {
  kpi: OverviewKPIAggregates | null;
  health: SystemHealthSLOBanner | null;
  recentTraces: RecentTracePreview[];
  loading: boolean;
  error: string | null;
}

export function useOverviewDashboardData(filters: DashboardFilters): OverviewDashboardState {
  const dispatch = useDispatch();
  const overviewState = useSelector((state: RootState) => state.overview);

  useEffect(() => {
    dispatch(
      overviewActions.fetchOverviewSubmitted({
        timeRange: filters.timeRange || "24h",
      })
    );
  }, [dispatch, filters.timeRange, filters.model, filters.service, filters.environment]);

  return {
    kpi: overviewState?.kpi || null,
    health: overviewState?.health || null,
    recentTraces: overviewState?.recentTraces || [],
    loading: overviewState?.status === "loading",
    error: overviewState?.error || null,
  };
}
