import { createSlice, type PayloadAction } from "@reduxjs/toolkit";
import type {
  QualitySummaryResult,
  QualityTrendPoint,
  ModelQualityBreakdown,
  FlaggedContentAlert,
} from "./types";

export interface QualityState {
  status: "idle" | "loading" | "success" | "error";
  summary: QualitySummaryResult | null;
  trend: QualityTrendPoint[];
  models: ModelQualityBreakdown[];
  flaggedAlerts: FlaggedContentAlert[];
  error: string | null;
}

const initialState: QualityState = {
  status: "idle",
  summary: null,
  trend: [],
  models: [],
  flaggedAlerts: [],
  error: null,
};

export const qualitySlice = createSlice({
  name: "quality",
  initialState,
  reducers: {
    fetchQualitySubmitted(
      state,
      _action: PayloadAction<{ model?: string; timeRange?: string; days?: number; service?: string }>
    ) {
      state.status = "loading";
      state.error = null;
    },
    qualitySuccess(
      state,
      action: PayloadAction<{
        summary?: QualitySummaryResult | null;
        trend?: QualityTrendPoint[];
        models?: ModelQualityBreakdown[];
        flaggedAlerts?: FlaggedContentAlert[];
      }>
    ) {
      state.status = "success";
      if (action.payload.summary !== undefined) state.summary = action.payload.summary;
      if (action.payload.trend !== undefined) state.trend = action.payload.trend;
      if (action.payload.models !== undefined) state.models = action.payload.models;
      if (action.payload.flaggedAlerts !== undefined) state.flaggedAlerts = action.payload.flaggedAlerts;
      state.error = null;
    },
    qualityFailed(state, action: PayloadAction<string>) {
      state.status = "error";
      state.error = action.payload;
    },
    resetQualityStatus(state) {
      state.status = "idle";
      state.error = null;
    },
  },
});

export const qualityActions = qualitySlice.actions;
export const qualityReducer = qualitySlice.reducer;
