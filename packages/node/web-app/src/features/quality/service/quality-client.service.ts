import {
  createServiceClient,
  executeServiceClientQuery,
  HTTP_CONSTANTS,
} from "@observability/shared-infra";
import type {
  QualitySummaryResult,
  QualityTrendPoint,
  ModelQualityBreakdown,
  FlaggedContentAlert,
} from "../types";
import { QualitySummaryFromApiOps, ModelQualityFromApiOps } from "../schema";
import { QUALITY_QUERIES } from "../queries";
import { QUALITY_CONFIG_DEFAULTS } from "../constants";

const SERVICE_NAME = HTTP_CONSTANTS.SERVICE_NAME_LATENCY_ENGINE;

export interface QualityClientAdapter {
  getQualitySummary(
    model?: string,
    timeRange?: string,
    service?: string
  ): Promise<QualitySummaryResult>;
  getQualityTrend(model?: string, days?: number): Promise<QualityTrendPoint[]>;
  getModelBreakdown(timeRange?: string): Promise<ModelQualityBreakdown[]>;
  getFlaggedContent(
    severity?: string,
    limit?: number
  ): Promise<FlaggedContentAlert[]>;
}

const rawAdapter: QualityClientAdapter = {
  getQualitySummary(
    model = QUALITY_CONFIG_DEFAULTS.DEFAULT_MODEL,
    timeRange = QUALITY_CONFIG_DEFAULTS.DEFAULT_TIME_RANGE,
    service?: string
  ) {
    return executeServiceClientQuery<QualitySummaryResult>(
      SERVICE_NAME,
      { ...QUALITY_QUERIES.QUERY_QUALITY_SUMMARY, transformOps: QualitySummaryFromApiOps },
      { model, time_range: timeRange, service }
    );
  },
  getQualityTrend(
    model = QUALITY_CONFIG_DEFAULTS.DEFAULT_MODEL,
    days = QUALITY_CONFIG_DEFAULTS.DEFAULT_LOOKBACK_DAYS
  ) {
    return executeServiceClientQuery<QualityTrendPoint[]>(
      SERVICE_NAME,
      QUALITY_QUERIES.QUERY_QUALITY_TREND,
      { model, days }
    );
  },
  getModelBreakdown(
    timeRange = QUALITY_CONFIG_DEFAULTS.DEFAULT_TIME_RANGE
  ) {
    return executeServiceClientQuery<ModelQualityBreakdown[]>(
      SERVICE_NAME,
      { ...QUALITY_QUERIES.QUERY_MODEL_BREAKDOWN, transformOps: ModelQualityFromApiOps },
      { time_range: timeRange }
    );
  },
  getFlaggedContent(
    severity?: string,
    limit = QUALITY_CONFIG_DEFAULTS.DEFAULT_LIMIT
  ) {
    return executeServiceClientQuery<FlaggedContentAlert[]>(
      SERVICE_NAME,
      QUALITY_QUERIES.QUERY_FLAGGED_CONTENT,
      { severity, limit }
    );
  },
};

export const qualityClientService: QualityClientAdapter = createServiceClient(
  SERVICE_NAME,
  rawAdapter
);
