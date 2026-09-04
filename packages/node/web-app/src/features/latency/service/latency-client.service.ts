import {
  createServiceClient,
  executeServiceClientQuery,
  HTTP_CONSTANTS,
} from "@observability/shared-infra";
import type {
  PercentilesResult,
  SLOResult,
  BaselinePoint,
  AttributionResult,
} from "../types";
import {
  PercentilesFromApiOps,
  SLOFromApiOps,
} from "../schema";
import { LATENCY_QUERIES } from "../queries";
import { LATENCY_CONFIG_DEFAULTS } from "../constants";

export interface LatencyClientAdapter {
  getPercentiles(model: string, hourOfDay: number, quantiles?: string): Promise<PercentilesResult>;
  getSLO(model: string, endpoint: string): Promise<SLOResult>;
  getBaseline(model: string, hourOfDay: number, days?: number): Promise<BaselinePoint[]>;
  getAttribution(model: string, hour: string): Promise<AttributionResult>;
}

const SERVICE_NAME = HTTP_CONSTANTS.SERVICE_NAME_LATENCY_ENGINE;

const rawAdapter: LatencyClientAdapter = {
  getPercentiles(
    model: string,
    hourOfDay: number,
    quantiles = LATENCY_CONFIG_DEFAULTS.DEFAULT_QUANTILES
  ) {
    return executeServiceClientQuery<PercentilesResult>(
      SERVICE_NAME,
      { ...LATENCY_QUERIES.FLOW_QUERY_PERCENTILES, transformOps: PercentilesFromApiOps },
      { model, hour_of_day: hourOfDay, quantiles }
    );
  },
  getSLO(model: string, endpoint: string) {
    return executeServiceClientQuery<SLOResult>(
      SERVICE_NAME,
      { ...LATENCY_QUERIES.FLOW_QUERY_SLO, transformOps: SLOFromApiOps },
      { model, endpoint }
    );
  },
  getBaseline(
    model: string,
    hourOfDay: number,
    days = LATENCY_CONFIG_DEFAULTS.DEFAULT_LOOKBACK_DAYS
  ) {
    return executeServiceClientQuery<BaselinePoint[]>(
      SERVICE_NAME,
      LATENCY_QUERIES.FLOW_QUERY_BASELINE,
      { model, hour_of_day: hourOfDay, days }
    );
  },
  getAttribution(model: string, hour: string) {
    return executeServiceClientQuery<AttributionResult>(
      SERVICE_NAME,
      LATENCY_QUERIES.FLOW_QUERY_ATTRIBUTION,
      { model, hour }
    );
  },
};

export const latencyClientService: LatencyClientAdapter = createServiceClient(
  SERVICE_NAME,
  rawAdapter
);

