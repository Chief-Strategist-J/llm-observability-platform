import { AnalysisResult } from '../../../types/trace';
import { IAnomalyThresholdService, createAnomalyThresholdService } from './anomalyThresholdService';

// Trace analysis service interface (Port)
export interface ITraceAnalysisService {
  getAnomalyScore(result: AnalysisResult | null): number;
  getAnomalyColor(score: number): string;
  getAnomalyLabel(score: number): string;
  shouldShowAnomaly(result: AnalysisResult | null): boolean;
}

// Trace analysis service implementation
export class TraceAnalysisService implements ITraceAnalysisService {
  constructor(private thresholdService: IAnomalyThresholdService = createAnomalyThresholdService()) {}

  getAnomalyScore(result: AnalysisResult | null): number {
    if (!result || typeof result.confidence !== 'number') return 0;
    return result.confidence;
  }

  getAnomalyColor(score: number): string {
    return this.thresholdService.getAnomalyColor(score);
  }

  getAnomalyLabel(score: number): string {
    return this.thresholdService.getAnomalyLabel(score);
  }

  shouldShowAnomaly(result: AnalysisResult | null): boolean {
    if (!result) return false;
    const score = this.getAnomalyScore(result);
    return this.thresholdService.shouldShowAnomaly(score);
  }
}

