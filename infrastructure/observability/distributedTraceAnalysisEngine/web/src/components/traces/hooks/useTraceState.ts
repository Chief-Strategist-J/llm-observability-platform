import { useEffect, useState } from 'react';
import { ITraceExplorerController, TraceExplorerState } from '../interfaces/traceControllers';
import { TraceExplorerDependencies } from '../interfaces/traceDependencies';

// Hook responsibility: State management (Axis 7 - State Representation)
export function useTraceState(dependencies: TraceExplorerDependencies): TraceExplorerState {
  const [state, setState] = useState<TraceExplorerState>(dependencies.controller.getState());

  // Subscribe to state changes
  useEffect(() => {
    const unsubscribe = dependencies.controller.subscribe(setState);
    return unsubscribe;
  }, [dependencies.controller]);

  return state;
}
