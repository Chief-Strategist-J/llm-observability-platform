import { ITraceExplorerController } from '../interfaces/traceControllers';
import { ServiceFactory } from '../interfaces/traceFactories';
import { TraceExplorerDependencies } from '../interfaces/traceDependencies';

// Hook responsibility: Input handling (Axis 1 - Input Handling Only)
export function useTraceHandlers(dependencies: TraceExplorerDependencies) {
  // Event handlers created via centralized factory - eliminates useCallback duplication (DRY Rule 10)
  const handleTraceSelect = ServiceFactory.createTraceSelectHandler(dependencies.controller);
  const handleTabChange = ServiceFactory.createTabChangeHandler(dependencies.controller);
  const clearError = ServiceFactory.createClearErrorHandler(dependencies.controller);

  return {
    handleTraceSelect,
    handleTabChange,
    clearError,
  };
}
