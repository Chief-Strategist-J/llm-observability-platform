import {
  createServiceClient,
  executeServiceClientQuery,
  HTTP_CONSTANTS,
} from "@observability/shared-infra";
import type { CostSummaryResult, CostByProvider } from "../types";
import { CostSummaryFromApiOps } from "../schema";
import { COST_QUERIES } from "../queries";

export interface CostsClientAdapter {
  getCostSummary(timeRange?: string): Promise<CostSummaryResult>;
  getCostProviders(timeRange?: string): Promise<CostByProvider[]>;
}

const rawAdapter: CostsClientAdapter = {
  getCostSummary(timeRange = "30d") {
    return executeServiceClientQuery<CostSummaryResult>(
      HTTP_CONSTANTS.SERVICE_NAME_LATENCY_ENGINE,
      { ...COST_QUERIES.QUERY_COST_SUMMARY, transformOps: CostSummaryFromApiOps },
      { time_range: timeRange }
    );
  },
  getCostProviders(timeRange = "30d") {
    return executeServiceClientQuery<CostByProvider[]>(
      HTTP_CONSTANTS.SERVICE_NAME_LATENCY_ENGINE,
      COST_QUERIES.QUERY_COST_PROVIDERS,
      { time_range: timeRange }
    );
  },
};

export const costsClientService: CostsClientAdapter = createServiceClient(
  HTTP_CONSTANTS.SERVICE_NAME_LATENCY_ENGINE,
  rawAdapter
);
