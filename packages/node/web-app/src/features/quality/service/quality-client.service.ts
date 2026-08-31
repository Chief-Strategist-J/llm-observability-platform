import {
  executeQueryAdapter,
  withRetry,
  withCache,
  withCircuitBreaker,
  withTracing,
} from "@observability/shared-infra";
import type {
  QualitySummaryResult,
  QualityTrendPoint,
  ModelQualityMetric,
  FlaggedContentAlert,
} from "../types";
import { QualitySummaryFromApiOps } from "../schema";
import { QUALITY_QUERIES } from "../queries";
import { QUALITY_CONFIG_DEFAULTS } from "../constants";

export interface QualityClientAdapter {
  getQualitySummary(model?: string, timeRange?: string): Promise<QualitySummaryResult>;
  getQualityTrend(timeRange?: string): Promise<QualityTrendPoint[]>;
  getModelQualityMetrics(timeRange?: string): Promise<ModelQualityMetric[]>;
  getFlaggedAlerts(limit?: number): Promise<FlaggedContentAlert[]>;
}

class RawQualityClientAdapter implements QualityClientAdapter {
  private readonly baseUrl = process.env.LATENCY_ENGINE_URL || QUALITY_CONFIG_DEFAULTS.DEFAULT_ENGINE_URL;
  private readonly serviceSub = QUALITY_CONFIG_DEFAULTS.DEFAULT_SERVICE_SUB;

  async getQualitySummary(model = "gpt-4o", timeRange = "24h"): Promise<QualitySummaryResult> {
    return executeQueryAdapter<QualitySummaryResult>(
      this.baseUrl, QUALITY_QUERIES.QUERY_QUALITY_SUMMARY.endpoint, { model, time_range: timeRange },
      this.serviceSub, QualitySummaryFromApiOps
    );
  }

  async getQualityTrend(timeRange = "7d"): Promise<QualityTrendPoint[]> {
    return executeQueryAdapter<QualityTrendPoint[]>(
      this.baseUrl, QUALITY_QUERIES.QUERY_QUALITY_TREND.endpoint, { time_range: timeRange },
      this.serviceSub
    );
  }

  async getModelQualityMetrics(timeRange = "24h"): Promise<ModelQualityMetric[]> {
    return executeQueryAdapter<ModelQualityMetric[]>(
      this.baseUrl, QUALITY_QUERIES.QUERY_MODEL_METRICS.endpoint, { time_range: timeRange },
      this.serviceSub
    );
  }

  async getFlaggedAlerts(limit = 10): Promise<FlaggedContentAlert[]> {
    return executeQueryAdapter<FlaggedContentAlert[]>(
      this.baseUrl, QUALITY_QUERIES.QUERY_FLAGGED_ALERTS.endpoint, { limit },
      this.serviceSub
    );
  }
}

const rawAdapter = new RawQualityClientAdapter();
export const qualityClientService: QualityClientAdapter = withTracing(
  withCircuitBreaker(withCache(withRetry(rawAdapter, 3, 200), 5000), 5, 10000),
  "quality-client-service"
);
