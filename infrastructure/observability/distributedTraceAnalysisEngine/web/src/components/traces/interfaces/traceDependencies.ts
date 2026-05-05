// Axis 8 - Dependency Type Definitions Only (SRP Rule 1)
import type { ITraceAnalysisService } from './traceServices';
import type { ITraceExplorerController, IUIStylingService } from './traceControllers';

// Dependency injection interface for orchestrator
export interface TraceExplorerDependencies {
  analysisService: ITraceAnalysisService;
  uiStylingService: IUIStylingService;
  controller: ITraceExplorerController;
}
