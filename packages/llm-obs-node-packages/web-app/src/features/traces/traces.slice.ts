import { createSlice, type PayloadAction } from "@reduxjs/toolkit";
import type { TraceSummary, TraceDetailResult } from "./types";

export interface TracesFilterState {
  searchQuery: string;
  selectedService: string;
  selectedStatus: string;
  selectedModel: string;
  minDurationMs: number;
}

export interface TracesState {
  status: "idle" | "loading" | "success" | "error";
  detailStatus: "idle" | "loading" | "success" | "error";
  traces: TraceSummary[];
  activeTrace: TraceDetailResult | null;
  filters: TracesFilterState;
  error: string | null;
  detailError: string | null;
}

const initialFilters: TracesFilterState = {
  searchQuery: "",
  selectedService: "all",
  selectedStatus: "all",
  selectedModel: "all",
  minDurationMs: 0,
};

const initialState: TracesState = {
  status: "idle",
  detailStatus: "idle",
  traces: [],
  activeTrace: null,
  filters: initialFilters,
  error: null,
  detailError: null,
};

export const tracesSlice = createSlice({
  name: "traces",
  initialState,
  reducers: {
    fetchTracesSubmitted(
      state,
      _action: PayloadAction<{ model?: string; status?: string; service?: string; limit?: number } | undefined>
    ) {
      state.status = "loading";
      state.error = null;
    },
    tracesSuccess(state, action: PayloadAction<TraceSummary[]>) {
      state.status = "success";
      state.traces = action.payload;
      state.error = null;
    },
    tracesFailed(state, action: PayloadAction<string>) {
      state.status = "error";
      state.error = action.payload;
    },
    fetchTraceDetailSubmitted(state, _action: PayloadAction<{ traceId: string }>) {
      state.detailStatus = "loading";
      state.detailError = null;
    },
    traceDetailSuccess(state, action: PayloadAction<TraceDetailResult>) {
      state.detailStatus = "success";
      state.activeTrace = action.payload;
      state.detailError = null;
    },
    traceDetailFailed(state, action: PayloadAction<string>) {
      state.detailStatus = "error";
      state.detailError = action.payload;
    },
    setSearchQuery(state, action: PayloadAction<string>) {
      state.filters.searchQuery = action.payload;
    },
    setSelectedService(state, action: PayloadAction<string>) {
      state.filters.selectedService = action.payload;
    },
    setSelectedStatus(state, action: PayloadAction<string>) {
      state.filters.selectedStatus = action.payload;
    },
    setSelectedModel(state, action: PayloadAction<string>) {
      state.filters.selectedModel = action.payload;
    },
    setMinDurationMs(state, action: PayloadAction<number>) {
      state.filters.minDurationMs = action.payload;
    },
    resetFilters(state) {
      state.filters = initialFilters;
    },
    setActiveTrace(state, action: PayloadAction<TraceDetailResult | null>) {
      state.activeTrace = action.payload;
    },
  },
});

export const tracesActions = tracesSlice.actions;
export const tracesReducer = tracesSlice.reducer;
