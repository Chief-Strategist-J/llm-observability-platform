import { createSlice, type PayloadAction } from "@reduxjs/toolkit";
import type { TraceSummary, TraceDetailResult } from "./types";

export interface TracesState {
  status: "idle" | "loading" | "success" | "error";
  traces: TraceSummary[];
  activeTrace: TraceDetailResult | null;
  error: string | null;
}

const initialState: TracesState = {
  status: "idle",
  traces: [],
  activeTrace: null,
  error: null,
};

export const tracesSlice = createSlice({
  name: "traces",
  initialState,
  reducers: {
    fetchTracesSubmitted(
      state,
      _action: PayloadAction<{ model?: string; status?: string; service?: string; limit?: number }>
    ) {
      state.status = "loading";
      state.error = null;
    },
    tracesSuccess(state, action: PayloadAction<TraceSummary[]>) {
      state.status = "success";
      state.traces = action.payload;
      state.error = null;
    },
    setActiveTrace(state, action: PayloadAction<TraceDetailResult | null>) {
      state.activeTrace = action.payload;
    },
    tracesFailed(state, action: PayloadAction<string>) {
      state.status = "error";
      state.error = action.payload;
    },
  },
});

export const tracesActions = tracesSlice.actions;
export const tracesReducer = tracesSlice.reducer;
