import { TraceExplorerDependencies } from '../interfaces/traceDependencies';
import { useTraceState } from './useTraceState';
import { useTraceDataSync } from './useTraceDataSync';
import { useTraceHandlers } from './useTraceHandlers';
import { useTraceComputedValues } from './useTraceComputedValues';

// Main hook responsibility: Thin orchestrator (Axis 12 - Orchestrator constraint)
export function useTraceExplorer(dependencies: TraceExplorerDependencies) {
  // Delegate to specialized hooks - each with single responsibility
  const state = useTraceState(dependencies);
  useTraceDataSync(dependencies, state.selectedTraceId);
  const handlers = useTraceHandlers(dependencies);
  const computedValues = useTraceComputedValues(state, dependencies);

  // Thin orchestrator - only combines results, no embedded logic, no property access
  return {
    ...handlers,
    ...computedValues,
    state,
  };
}
