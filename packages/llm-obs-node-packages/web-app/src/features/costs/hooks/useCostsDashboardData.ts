'use client';

import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import type { RootState } from "@/core/store/configure-store";
import type { DashboardFilters } from "@/hooks/useDashboardFilters";
import { costsActions } from "../costs.slice";
import type { CostSummaryResult, CostByProvider } from "../types";

export interface CostsDashboardState {
  summary: CostSummaryResult | null;
  providers: CostByProvider[];
  loading: boolean;
  error: string | null;
}

export function useCostsDashboardData(filters: DashboardFilters): CostsDashboardState {
  const dispatch = useDispatch();
  const costsState = useSelector((state: RootState) => state.costs);

  useEffect(() => {
    dispatch(
      costsActions.fetchCostsSubmitted({
        timeRange: filters.timeRange || "30d",
      })
    );
  }, [dispatch, filters.timeRange, filters.model, filters.service, filters.environment]);

  return {
    summary: costsState?.summary || null,
    providers: costsState?.providers || [],
    loading: costsState?.status === "loading",
    error: costsState?.error || null,
  };
}
