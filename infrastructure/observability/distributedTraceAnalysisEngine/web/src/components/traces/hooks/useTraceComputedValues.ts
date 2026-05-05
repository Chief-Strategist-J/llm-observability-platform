import { ITraceAnalysisService } from '../interfaces/traceServices';
import { IUIStylingService, Tab, TraceExplorerState } from '../interfaces/traceControllers';
import { TraceExplorerDependencies } from '../interfaces/traceDependencies';

// Hook responsibility: Computed values (Axis 7 - State Representation Only)
export function useTraceComputedValues(
  state: TraceExplorerState,
  dependencies: TraceExplorerDependencies
) {
  // Computed values (delegated to services) - eliminates useCallback duplication (DRY Rule 10)
  const anomalyScore = dependencies.analysisService.getAnomalyScore(state.selectedResult);
  const showAnomaly = dependencies.analysisService.shouldShowAnomaly(state.selectedResult);
  const getAnomalyColor = (score: number) => dependencies.analysisService.getAnomalyColor(score);
  const getAnomalyLabel = (score: number) => dependencies.analysisService.getAnomalyLabel(score);
  const getTabStyle = (activeTab: Tab, currentTab: Tab) => dependencies.uiStylingService.getTabStyle(activeTab, currentTab);

  return {
    anomalyScore,
    showAnomaly,
    getAnomalyColor,
    getAnomalyLabel,
    getTabStyle,
  };
}
