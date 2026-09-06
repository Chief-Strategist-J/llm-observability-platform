import { createSlice, type PayloadAction } from "@reduxjs/toolkit";
import type { PercentilesResult, SLOResult, AttributionResult, BaselinePoint } from "./types";

export interface LatencyState {
  status: "idle" | "loading" | "success" | "error";
  percentiles: PercentilesResult | null;
  slo: SLOResult | null;
  attribution: AttributionResult | null;
  baseline: BaselinePoint[];
  error: string | null;
}

const initialState: LatencyState = {
  status: "idle",
  percentiles: null,
  slo: null,
  attribution: null,
  baseline: [],
  error: null,
};

export const latencySlice = createSlice({
  name: "latency",
  initialState,
  reducers: {
    fetchLatencySubmitted(
      state,
      _action: PayloadAction<{ model: string; hourOfDay: number; days?: number; endpoint?: string; hour?: string }>
    ) {
      state.status = "loading";
      state.error = null;
    },
    latencySuccess(
      state,
      action: PayloadAction<{
        percentiles?: PercentilesResult | null;
        slo?: SLOResult | null;
        attribution?: AttributionResult | null;
        baseline?: BaselinePoint[];
      }>
    ) {
      state.status = "success";
      if (action.payload.percentiles !== undefined) state.percentiles = action.payload.percentiles;
      if (action.payload.slo !== undefined) state.slo = action.payload.slo;
      if (action.payload.attribution !== undefined) state.attribution = action.payload.attribution;
      if (action.payload.baseline !== undefined) state.baseline = action.payload.baseline;
      state.error = null;
    },
    latencyFailed(state, action: PayloadAction<string>) {
      state.status = "error";
      state.error = action.payload;
    },
    resetLatencyStatus(state) {
      state.status = "idle";
      state.error = null;
    },
  },
});

export const latencyActions = latencySlice.actions;
export const latencyReducer = latencySlice.reducer;
