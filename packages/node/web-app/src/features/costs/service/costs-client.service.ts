import crypto from "crypto";
import { mapJson } from "../../../core/data-driven/json-map";
import type { JsonMapOp } from "../../../core/data-driven/transform.types";
import {
  withRetry,
  withCache,
  withCircuitBreaker,
  withTracing,
} from "../../../core/data-driven/adapter-decorators";
import type { CostSummaryResult, CostByProvider } from "../types";
import { CostSummaryFromApiOps } from "../schema";
import { COST_QUERIES } from "../queries";
import { COSTS_CONFIG_DEFAULTS } from "../constants";

export interface CostsClientAdapter {
  getCostSummary(timeRange?: string): Promise<CostSummaryResult>;
  getCostProviders(timeRange?: string): Promise<CostByProvider[]>;
}

class RawCostsClientAdapter implements CostsClientAdapter {
  private readonly baseUrl: string;

  constructor() {
    this.baseUrl = process.env.LATENCY_ENGINE_URL || COSTS_CONFIG_DEFAULTS.DEFAULT_ENGINE_URL;
  }

  private getAuthHeaders(): Record<string, string> {
    const secret = process.env.JWT_SECRET || COSTS_CONFIG_DEFAULTS.DEFAULT_JWT_SECRET;
    const header = { alg: "HS256", typ: "JWT" };
    const now = Math.floor(Date.now() / 1000);
    const payload = {
      sub: COSTS_CONFIG_DEFAULTS.DEFAULT_SERVICE_SUB,
      iat: now,
      exp: now + COSTS_CONFIG_DEFAULTS.DEFAULT_JWT_EXPIRY_SECONDS,
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
      throw new Error(`Costs request to ${endpoint} failed: ${res.status}`);
    }

    const raw = await res.json();
    return transformOps ? (mapJson(raw, transformOps) as unknown as T) : (raw as T);
  }

  async getCostSummary(timeRange = "30d"): Promise<CostSummaryResult> {
    return this.executeQuery<CostSummaryResult>(
      COST_QUERIES.QUERY_COST_SUMMARY.endpoint,
      { time_range: timeRange },
      CostSummaryFromApiOps
    );
  }

  async getCostProviders(timeRange = "30d"): Promise<CostByProvider[]> {
    return this.executeQuery<CostByProvider[]>(
      COST_QUERIES.QUERY_COST_PROVIDERS.endpoint,
      { time_range: timeRange }
    );
  }
}

const rawAdapter = new RawCostsClientAdapter();
export const costsClientService: CostsClientAdapter = withTracing(
  withCircuitBreaker(withCache(withRetry(rawAdapter, 3, 200), 5000), 5, 10000),
  "costs-client-service"
);
