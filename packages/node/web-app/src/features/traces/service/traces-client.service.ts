import crypto from "crypto";
import { mapJson } from "../../../core/data-driven/json-map";
import type { JsonMapOp } from "../../../core/data-driven/transform.types";
import {
  withRetry,
  withCache,
  withCircuitBreaker,
  withTracing,
} from "../../../core/data-driven/adapter-decorators";
import type { TraceSummary, TraceDetailResult } from "../types";
import { TraceSummaryFromApiOps } from "../schema";
import { TRACES_CONFIG_DEFAULTS, TRACES_ENDPOINTS } from "../constants";

export interface TracesClientAdapter {
  listTraces(model?: string, status?: string, service?: string, limit?: number): Promise<TraceSummary[]>;
  getTraceDetail(traceId: string): Promise<TraceDetailResult | null>;
}

class RawTracesClientAdapter implements TracesClientAdapter {
  private readonly baseUrl: string;

  constructor() {
    this.baseUrl = process.env.LATENCY_ENGINE_URL || TRACES_CONFIG_DEFAULTS.DEFAULT_ENGINE_URL;
  }

  private getAuthHeaders(): Record<string, string> {
    const secret = process.env.JWT_SECRET || TRACES_CONFIG_DEFAULTS.DEFAULT_JWT_SECRET;
    const header = { alg: "HS256", typ: "JWT" };
    const now = Math.floor(Date.now() / 1000);
    const payload = {
      sub: TRACES_CONFIG_DEFAULTS.DEFAULT_SERVICE_SUB,
      iat: now,
      exp: now + TRACES_CONFIG_DEFAULTS.DEFAULT_JWT_EXPIRY_SECONDS,
    };

    const headerB64 = Buffer.from(JSON.stringify(header)).toString("base64url");
    const payloadB64 = Buffer.from(JSON.stringify(payload)).toString("base64url");
    const signingInput = `${headerB64}.${payloadB64}`;

    const signatureB64 = crypto
      .createHmac("sha256", secret)
      .update(signingInput)
      .digest("base64url");

    const traceId = crypto.randomBytes(16).toString("hex");
    const spanId = crypto.randomBytes(8).toString("hex");

    return {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${signingInput}.${signatureB64}`,
      "traceparent": `00-${traceId}-${spanId}-01`,
      "x-trace-id": traceId,
    };
  }

  private async executeQuery<T>(
    endpoint: string,
    params: Record<string, string | number | undefined>,
    transformOps?: JsonMapOp[]
  ): Promise<T> {
    const url = new URL(`${this.baseUrl}${endpoint}`);
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null) {
        url.searchParams.set(k, String(v));
      }
    });

    const res = await fetch(url.toString(), { headers: this.getAuthHeaders() });
    if (!res.ok) {
      throw new Error(`Traces request to ${endpoint} failed: ${res.status}`);
    }

    const raw = await res.json();
    return transformOps ? (mapJson(raw, transformOps) as unknown as T) : (raw as T);
  }

  async listTraces(
    model?: string,
    status?: string,
    service?: string,
    limit = TRACES_CONFIG_DEFAULTS.DEFAULT_PAGE_SIZE
  ): Promise<TraceSummary[]> {
    const raw = await this.executeQuery<TraceSummary[]>(
      TRACES_ENDPOINTS.LIST,
      { model, status, service, limit }
    );
    return Array.isArray(raw) ? raw.map((t) => mapJson(t as any, TraceSummaryFromApiOps) as unknown as TraceSummary) : [];
  }

  async getTraceDetail(traceId: string): Promise<TraceDetailResult | null> {
    return this.executeQuery<TraceDetailResult>(
      `${TRACES_ENDPOINTS.DETAIL}/${traceId}`,
      {}
    );
  }
}

const rawAdapter = new RawTracesClientAdapter();
export const tracesClientService: TracesClientAdapter = withTracing(
  withCircuitBreaker(withCache(withRetry(rawAdapter, 3, 200), 5000), 5, 10000),
  "traces-client-service"
);
