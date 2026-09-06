'use client';

import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import type { RootState } from "@/core/store/configure-store";
import type { DashboardFilters } from "@/hooks/useDashboardFilters";
import { tracesActions } from "../traces.slice";
import type { TraceSummary } from "../types";

export interface TracesDashboardState {
  traces: TraceSummary[];
  loading: boolean;
  error: string | null;
}

export function useTracesDashboardData(filters: DashboardFilters): TracesDashboardState {
  const dispatch = useDispatch();
  const tracesState = useSelector((state: RootState) => state.traces);

  useEffect(() => {
    dispatch(
      tracesActions.fetchTracesSubmitted({
        model: filters.model || undefined,
        service: filters.service || undefined,
        limit: 20,
      })
    );
  }, [dispatch, filters.model, filters.service, filters.timeRange, filters.environment]);

  return {
    traces: tracesState?.traces || [],
    loading: tracesState?.status === "loading",
    error: tracesState?.error || null,
  };
}
