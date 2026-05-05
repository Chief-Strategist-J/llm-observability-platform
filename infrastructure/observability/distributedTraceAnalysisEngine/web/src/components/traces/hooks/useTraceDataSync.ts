import { useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { ITraceExplorerController } from '../interfaces/traceControllers';
import { TraceListItem } from '../interfaces/traceTypes';
import { TraceExplorerDependencies } from '../interfaces/traceDependencies';
import { useTraceExternalSync } from './useTraceExternalSync';
import { api } from '../../../api';

// Hook responsibility: Pure orchestration (Axis 2 - Application Orchestration Only)
export function useTraceDataSync(
  dependencies: TraceExplorerDependencies,
  selectedTraceId: string | null
) {
  const [searchParams] = useSearchParams();

  // Initialize from search params - independent execution
  useEffect(() => {
    if (searchParams.has('trace')) {
      const traceId = searchParams.get('trace');
      if (traceId) {
        dependencies.controller.handleTraceSelect(traceId);
      }
    }
  }, [searchParams, dependencies.controller]);

  // Get external data from dedicated hook
  const { traceListData, tracesLoading } = useTraceExternalSync();

  // Update controller with trace list data - independent execution (eliminates CoE coupling)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    dependencies.controller.updateTraceListData(traceListData || []);
  }, [traceListData]);

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    dependencies.controller.updateTracesLoading(tracesLoading);
  }, [tracesLoading]);

  // Fetch trace data when a trace is selected
  useEffect(() => {
    if (selectedTraceId) {
      dependencies.controller.updateTraceLoading(true);
      api.traceById(selectedTraceId)
        .then(trace => {
          dependencies.controller.updateTraceData(trace);
        })
        .catch(err => {
          console.error('Failed to fetch trace:', err);
          dependencies.controller.updateTraceData(null);
        })
        .finally(() => {
          dependencies.controller.updateTraceLoading(false);
        });
    }
  }, [selectedTraceId]); // Remove dependencies.controller to prevent re-renders

  // Reset tab when trace selection changes
  useEffect(() => {
    if (selectedTraceId) {
      dependencies.controller.handleTabChange('dag');
    }
  }, [selectedTraceId]); // Remove dependencies.controller to prevent re-renders
}
