import { createSlice, type PayloadAction } from "@reduxjs/toolkit";
import type { CostSummaryResult, CostByProvider } from "./types";

export interface CostsState {
  status: "idle" | "loading" | "success" | "error";
  summary: CostSummaryResult | null;
  providers: CostByProvider[];
  error: string | null;
}

const initialState: CostsState = {
  status: "idle",
  summary: null,
  providers: [],
  error: null,
};

export const costsSlice = createSlice({
  name: "costs",
  initialState,
  reducers: {
    fetchCostsSubmitted(state, _action: PayloadAction<{ timeRange?: string }>) {
      state.status = "loading";
      state.error = null;
    },
    costsSuccess(
      state,
      action: PayloadAction<{
        summary?: CostSummaryResult | null;
        providers?: CostByProvider[];
      }>
    ) {
      state.status = "success";
      if (action.payload.summary !== undefined) state.summary = action.payload.summary;
      if (action.payload.providers !== undefined) state.providers = action.payload.providers;
      state.error = null;
    },
    costsFailed(state, action: PayloadAction<string>) {
      state.status = "error";
      state.error = action.payload;
    },
  },
});

export const costsActions = costsSlice.actions;
export const costsReducer = costsSlice.reducer;
