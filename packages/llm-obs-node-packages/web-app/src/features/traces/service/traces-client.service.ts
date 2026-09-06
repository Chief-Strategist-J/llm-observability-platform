import {
  createServiceClient,
  executeServiceClientQuery,
  mapJson,
  HTTP_CONSTANTS,
} from "@observability/shared-infra";
import type { TraceSummary, TraceDetailResult } from "../types";
import { TraceSummaryFromApiOps } from "../schema";
import { TRACES_CONFIG_DEFAULTS, TRACES_ENDPOINTS } from "../constants";

export interface TracesClientAdapter {
  listTraces(model?: string, status?: string, service?: string, limit?: number): Promise<TraceSummary[]>;
  getTraceDetail(traceId: string): Promise<TraceDetailResult | null>;
}

const rawAdapter: TracesClientAdapter = {
  async listTraces(
    model?: string,
    status?: string,
    service?: string,
    limit = TRACES_CONFIG_DEFAULTS.DEFAULT_PAGE_SIZE
  ) {
    const raw = await executeServiceClientQuery<TraceSummary[]>(
      HTTP_CONSTANTS.SERVICE_NAME_LATENCY_ENGINE,
      { endpoint: TRACES_ENDPOINTS.LIST },
      { model, status, service, limit }
    );
    return Array.isArray(raw) ? raw.map((t) => mapJson(t as any, TraceSummaryFromApiOps) as unknown as TraceSummary) : [];
  },
  getTraceDetail(traceId: string) {
    return executeServiceClientQuery<TraceDetailResult>(
      HTTP_CONSTANTS.SERVICE_NAME_LATENCY_ENGINE,
      { endpoint: `${TRACES_ENDPOINTS.DETAIL}/${traceId}` },
      {}
    );
  },
};

export const tracesClientService: TracesClientAdapter = createServiceClient(
  HTTP_CONSTANTS.SERVICE_NAME_LATENCY_ENGINE,
  rawAdapter
);
