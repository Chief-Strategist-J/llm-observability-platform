import {
  executeQueryAdapter,
  mapJson,
  withRetry,
  withCache,
  withCircuitBreaker,
  withTracing,
} from "@observability/shared-infra";
import type { TraceSummary, TraceDetailResult } from "../types";
import { TraceSummaryFromApiOps } from "../schema";
import { TRACES_CONFIG_DEFAULTS, TRACES_ENDPOINTS } from "../constants";

export interface TracesClientAdapter {
  listTraces(model?: string, status?: string, service?: string, limit?: number): Promise<TraceSummary[]>;
  getTraceDetail(traceId: string): Promise<TraceDetailResult | null>;
}

class RawTracesClientAdapter implements TracesClientAdapter {
  private readonly baseUrl = process.env.LATENCY_ENGINE_URL || TRACES_CONFIG_DEFAULTS.DEFAULT_ENGINE_URL;
  private readonly serviceSub = TRACES_CONFIG_DEFAULTS.DEFAULT_SERVICE_SUB;

  async listTraces(
    model?: string,
    status?: string,
    service?: string,
    limit = TRACES_CONFIG_DEFAULTS.DEFAULT_PAGE_SIZE
  ): Promise<TraceSummary[]> {
    const raw = await executeQueryAdapter<TraceSummary[]>(
      this.baseUrl, TRACES_ENDPOINTS.LIST, { model, status, service, limit }, this.serviceSub
    );
    return Array.isArray(raw) ? raw.map((t) => mapJson(t as any, TraceSummaryFromApiOps) as unknown as TraceSummary) : [];
  }

  async getTraceDetail(traceId: string): Promise<TraceDetailResult | null> {
    return executeQueryAdapter<TraceDetailResult>(
      this.baseUrl, `${TRACES_ENDPOINTS.DETAIL}/${traceId}`, {}, this.serviceSub
    );
  }
}

const rawAdapter = new RawTracesClientAdapter();
export const tracesClientService: TracesClientAdapter = withTracing(
  withCircuitBreaker(withCache(withRetry(rawAdapter, 3, 200), 5000), 5, 10000),
  "traces-client-service"
);
