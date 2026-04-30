import { create } from 'zustand';

type DashboardState = {
  selectedTraceId?: string;
  setSelectedTraceId: (traceId?: string) => void;
  histogramBins: number;
  setHistogramBins: (bins: number) => void;
};

export const useDashboardState = create<DashboardState>((set) => ({
  selectedTraceId: undefined,
  setSelectedTraceId: (selectedTraceId) => set({ selectedTraceId }),
  histogramBins: 20,
  setHistogramBins: (histogramBins) => set({ histogramBins }),
}));
