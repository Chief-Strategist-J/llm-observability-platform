import {
  executeQueryAdapter,
  withRetry,
  withCache,
  withCircuitBreaker,
  withTracing,
} from "@observability/shared-infra";
import type {
  OverviewKPIAggregates,
  SystemHealthSLOBanner,
  RecentTracePreview,
} from "../types";
import { OverviewKPIFromApiOps } from "../schema";
import { OVERVIEW_CONFIG_DEFAULTS, OVERVIEW_ENDPOINTS } from "../constants";

export interface OverviewClientAdapter {
  getKPISummary(timeRange?: string): Promise<OverviewKPIAggregates>;
  getSystemHealth(): Promise<SystemHealthSLOBanner>;
  getRecentTraces(limit?: number): Promise<RecentTracePreview[]>;
}

class RawOverviewClientAdapter implements OverviewClientAdapter {
  private readonly baseUrl = process.env.LATENCY_ENGINE_URL || OVERVIEW_CONFIG_DEFAULTS.DEFAULT_ENGINE_URL;
  private readonly serviceSub = OVERVIEW_CONFIG_DEFAULTS.DEFAULT_SERVICE_SUB;

  async getKPISummary(timeRange = OVERVIEW_CONFIG_DEFAULTS.DEFAULT_TIME_RANGE): Promise<OverviewKPIAggregates> {
    return executeQueryAdapter<OverviewKPIAggregates>(
      this.baseUrl, OVERVIEW_ENDPOINTS.SUMMARY, { time_range: timeRange },
      this.serviceSub, OverviewKPIFromApiOps
    );
  }

  async getSystemHealth(): Promise<SystemHealthSLOBanner> {
    return executeQueryAdapter<SystemHealthSLOBanner>(
      this.baseUrl, OVERVIEW_ENDPOINTS.HEALTH, {}, this.serviceSub
    );
  }

  async getRecentTraces(limit = 10): Promise<RecentTracePreview[]> {
    return executeQueryAdapter<RecentTracePreview[]>(
      this.baseUrl, OVERVIEW_ENDPOINTS.RECENT_TRACES, { limit }, this.serviceSub
    );
  }
}

const rawAdapter = new RawOverviewClientAdapter();
export const overviewClientService: OverviewClientAdapter = withTracing(
  withCircuitBreaker(withCache(withRetry(rawAdapter, 3, 200), 5000), 5, 10000),
  "overview-client-service"
);
