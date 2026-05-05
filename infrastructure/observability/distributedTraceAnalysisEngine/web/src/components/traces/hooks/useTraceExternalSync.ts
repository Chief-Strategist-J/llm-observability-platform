import { usePolling } from '../../../hooks';
import { api } from '../../../api';
import { API_CONFIG } from '../../../constants/api';
import { Trace } from '../../../types/trace';
import { TraceListItem } from '../interfaces/traceTypes';

// Hook responsibility: External integration (Axis 5 - External Integration Only)
export function useTraceExternalSync() {
  // Polling for trace list data with caching
  const { data: traceListData, loading: tracesLoading } = usePolling(
    () => api.traces(),
    API_CONFIG.POLLING_INTERVAL_MS,
    true,
    'trace-list' // Cache key for trace list data
  );

  // Note: traceData and resultData are fetched on-demand based on selected trace
  // This hook only manages the trace list polling
  const traceData = null;
  const traceLoading = false;
  const resultData = null;

  return {
    traceListData,
    tracesLoading,
    traceData,
    traceLoading,
    resultData,
  };
}
