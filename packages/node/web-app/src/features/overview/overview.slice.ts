import { createSlice, type PayloadAction } from "@reduxjs/toolkit";
import type { OverviewKPIAggregates, SystemHealthSLOBanner, RecentTracePreview } from "./types";

export interface OverviewState {
  status: "idle" | "loading" | "success" | "error";
  kpi: OverviewKPIAggregates | null;
  health: SystemHealthSLOBanner | null;
  recentTraces: RecentTracePreview[];
  error: string | null;
}

const initialState: OverviewState = {
  status: "idle",
  kpi: null,
  health: null,
  recentTraces: [],
  error: null,
};

export const overviewSlice = createSlice({
  name: "overview",
  initialState,
  reducers: {
    fetchOverviewSubmitted(state, _action: PayloadAction<{ timeRange?: string }>) {
      state.status = "loading";
      state.error = null;
    },
    overviewSuccess(
      state,
      action: PayloadAction<{
        kpi?: OverviewKPIAggregates | null;
        health?: SystemHealthSLOBanner | null;
        recentTraces?: RecentTracePreview[];
      }>
    ) {
      state.status = "success";
      if (action.payload.kpi !== undefined) state.kpi = action.payload.kpi;
      if (action.payload.health !== undefined) state.health = action.payload.health;
      if (action.payload.recentTraces !== undefined) state.recentTraces = action.payload.recentTraces;
      state.error = null;
    },
    overviewFailed(state, action: PayloadAction<string>) {
      state.status = "error";
      state.error = action.payload;
    },
  },
});

export const overviewActions = overviewSlice.actions;
export const overviewReducer = overviewSlice.reducer;
