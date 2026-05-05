import { ANOMALY_THRESHOLDS, ANOMALY_COLORS } from '../../../constants/api';

// Anomaly threshold service interface (Port)
export interface IAnomalyThresholdService {
  getAnomalyLevel(score: number): 'high' | 'medium' | 'normal';
  getAnomalyColor(score: number): string;
  getAnomalyLabel(score: number): string;
  shouldShowAnomaly(score: number): boolean;
}

// Constants - Single source of truth (DRY Rule 5)
export const ANOMALY_SHOW_THRESHOLD = 0.3;

// Anomaly threshold service implementation
export class AnomalyThresholdService implements IAnomalyThresholdService {
  // Single algorithm for threshold evaluation - eliminates CoA coupling
  private evaluateThreshold(score: number): 'high' | 'medium' | 'normal' {
    if (score >= ANOMALY_THRESHOLDS.HIGH) return 'high';
    if (score >= ANOMALY_THRESHOLDS.MEDIUM) return 'medium';
    return 'normal';
  }

  getAnomalyLevel(score: number): 'high' | 'medium' | 'normal' {
    return this.evaluateThreshold(score);
  }

  getAnomalyColor(score: number): string {
    const level = this.evaluateThreshold(score);
    const colorMap = {
      high: ANOMALY_COLORS.HIGH,
      medium: ANOMALY_COLORS.MEDIUM,
      normal: ANOMALY_COLORS.LOW
    };
    return colorMap[level];
  }

  getAnomalyLabel(score: number): string {
    const level = this.evaluateThreshold(score);
    const labelMap = {
      high: 'High anomaly',
      medium: 'Medium anomaly',
      normal: 'Normal'
    };
    return labelMap[level];
  }

  shouldShowAnomaly(score: number): boolean {
    return score > ANOMALY_SHOW_THRESHOLD;
  }
}

// Factory function - eliminates CoV coupling
export function createAnomalyThresholdService(): IAnomalyThresholdService {
  return new AnomalyThresholdService();
}

