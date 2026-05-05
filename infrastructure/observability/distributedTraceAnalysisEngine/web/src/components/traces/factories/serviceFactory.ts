// Single source of truth factory - eliminates DRY violations (DRY Rule 10)
import { TraceAnalysisService, ITraceAnalysisService } from '../services/traceAnalysisService';
import { AnomalyThresholdService, IAnomalyThresholdService } from '../services/anomalyThresholdService';
import { LayoutService, ILayoutService } from '../services/layoutService';
import { NodeCreationService } from '../services/nodeCreationService';
import { EdgeCreationService } from '../services/edgeCreationService';
import { UIStylingService, IUIStylingService } from '../controller/traceExplorerController';
import { TraceExplorerController, ITraceExplorerController, ITraceExplorerStore } from '../controller/traceExplorerController';
import { ITraceCacheRepository, TraceCacheRepository } from '../repositories/traceCacheRepository';
import { createTraceExplorerStore } from '../controller/traceState';
import { FormattingService, IFormattingService } from '../services/formattingService';
import { SpanDetailMapperService, ISpanDetailMapperService } from '../services/spanDetailMapperService';
import { TraceStatsService, ITraceStatsService } from '../services/traceStatsService';

export class ServiceFactory {
  // Single factory methods - eliminates duplication across multiple files
  static createTraceAnalysisService(): ITraceAnalysisService {
    return new TraceAnalysisService();
  }

  static createAnomalyThresholdService(): IAnomalyThresholdService {
    return new AnomalyThresholdService();
  }

  static createLayoutService(cacheRepository: ITraceCacheRepository): ILayoutService {
    return new LayoutService(cacheRepository);
  }

  static createNodeCreationService(): NodeCreationService {
    return new NodeCreationService();
  }

  static createEdgeCreationService(): EdgeCreationService {
    return new EdgeCreationService();
  }

  static createUIStylingService(): IUIStylingService {
    return new UIStylingService();
  }

  static createTraceExplorerController(analysisService: ITraceAnalysisService, store?: ITraceExplorerStore): ITraceExplorerController {
    return new TraceExplorerController(analysisService, store);
  }

  static createTraceCacheRepository(): ITraceCacheRepository {
    return new TraceCacheRepository();
  }

  static createTraceExplorerStoreInstance() {
    return createTraceExplorerStore();
  }

  static createFormattingService(): IFormattingService {
    return new FormattingService();
  }

  static createSpanDetailMapperService(): ISpanDetailMapperService {
    return new SpanDetailMapperService();
  }

  static createTraceStatsService(): ITraceStatsService {
    return new TraceStatsService();
  }

  // Handler factory methods - eliminates useCallback duplication
  static createTraceSelectHandler(controller: ITraceExplorerController) {
    return (traceId: string) => controller.handleTraceSelect(traceId);
  }

  static createTabChangeHandler(controller: ITraceExplorerController) {
    return (tab: string) => controller.handleTabChange(tab);
  }

  static createClearErrorHandler(controller: ITraceExplorerController) {
    return () => controller.clearError();
  }

  // Generic factory method for extensibility
  static create<T>(ServiceClass: new (...args: unknown[]) => T, ...args: ConstructorParameters<typeof ServiceClass>): T {
    return new ServiceClass(...args);
  }
}
