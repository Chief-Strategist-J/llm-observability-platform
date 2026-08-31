import {
  executeQueryAdapter,
  withRetry,
  withCache,
  withCircuitBreaker,
  withTracing,
} from "@observability/shared-infra";
import type { CostSummaryResult, CostByProvider } from "../types";
import { CostSummaryFromApiOps } from "../schema";
import { COST_QUERIES } from "../queries";
import { COSTS_CONFIG_DEFAULTS } from "../constants";

export interface CostsClientAdapter {
  getCostSummary(timeRange?: string): Promise<CostSummaryResult>;
  getCostProviders(timeRange?: string): Promise<CostByProvider[]>;
}

class RawCostsClientAdapter implements CostsClientAdapter {
  private readonly baseUrl = process.env.LATENCY_ENGINE_URL || COSTS_CONFIG_DEFAULTS.DEFAULT_ENGINE_URL;
  private readonly serviceSub = COSTS_CONFIG_DEFAULTS.DEFAULT_SERVICE_SUB;

  async getCostSummary(timeRange = "30d"): Promise<CostSummaryResult> {
    return executeQueryAdapter<CostSummaryResult>(
      this.baseUrl, COST_QUERIES.QUERY_COST_SUMMARY.endpoint, { time_range: timeRange },
      this.serviceSub, CostSummaryFromApiOps
    );
  }

  async getCostProviders(timeRange = "30d"): Promise<CostByProvider[]> {
    return executeQueryAdapter<CostByProvider[]>(
      this.baseUrl, COST_QUERIES.QUERY_COST_PROVIDERS.endpoint, { time_range: timeRange },
      this.serviceSub
    );
  }
}

const rawAdapter = new RawCostsClientAdapter();
export const costsClientService: CostsClientAdapter = withTracing(
  withCircuitBreaker(withCache(withRetry(rawAdapter, 3, 200), 5000), 5, 10000),
  "costs-client-service"
);
