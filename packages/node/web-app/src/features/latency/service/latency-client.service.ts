import { mapJson } from "@/core/data-driven/json-map";
import {
  withRetry,
  withCache,
  withCircuitBreaker,
  withTracing,
} from "@/core/data-driven/adapter-decorators";
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

export interface LatencyClientAdapter {
  getPercentiles(model: string, hourOfDay: number, quantiles?: string): Promise<PercentilesResult>;
  getSLO(model: string, endpoint: string): Promise<SLOResult>;
  getBaseline(model: string, hourOfDay: number, days?: number): Promise<BaselinePoint[]>;
  getAttribution(model: string, hour: string): Promise<AttributionResult>;
}

class RawLatencyClientAdapter implements LatencyClientAdapter {
  private readonly baseUrl: string;

  constructor() {
    this.baseUrl = process.env.LATENCY_ENGINE_URL || "http://localhost:8002";
  }

  private getAuthHeaders(): Record<string, string> {
    const jwtToken = process.env.SERVICE_JWT_TOKEN || "service-jwt-token";
    return {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${jwtToken}`,
    };
  }

  async getPercentiles(model: string, hourOfDay: number, quantiles = "0.50,0.95,0.99"): Promise<PercentilesResult> {
    const queryDef = LATENCY_QUERIES.FLOW_QUERY_PERCENTILES;
    const url = new URL(`${this.baseUrl}${queryDef.endpoint}`);
    url.searchParams.set("model", model);
    url.searchParams.set("hour_of_day", String(hourOfDay));
    url.searchParams.set("quantiles", quantiles);

    const res = await fetch(url.toString(), { headers: this.getAuthHeaders() });
    if (!res.ok) {
      throw new Error(`LatencyEngine getPercentiles failed: ${res.status}`);
    }
    const raw = await res.json();
    return mapJson(raw, PercentilesFromApiOps) as unknown as PercentilesResult;
  }

  async getSLO(model: string, endpoint: string): Promise<SLOResult> {
    const queryDef = LATENCY_QUERIES.FLOW_QUERY_SLO;
    const url = new URL(`${this.baseUrl}${queryDef.endpoint}`);
    url.searchParams.set("model", model);
    url.searchParams.set("endpoint", endpoint);

    const res = await fetch(url.toString(), { headers: this.getAuthHeaders() });
    if (!res.ok) {
      throw new Error(`LatencyEngine getSLO failed: ${res.status}`);
    }
    const raw = await res.json();
    return mapJson(raw, SLOFromApiOps) as unknown as SLOResult;
  }

  async getBaseline(model: string, hourOfDay: number, days = 7): Promise<BaselinePoint[]> {
    const queryDef = LATENCY_QUERIES.FLOW_QUERY_BASELINE;
    const url = new URL(`${this.baseUrl}${queryDef.endpoint}`);
    url.searchParams.set("model", model);
    url.searchParams.set("hour_of_day", String(hourOfDay));
    url.searchParams.set("days", String(days));

    const res = await fetch(url.toString(), { headers: this.getAuthHeaders() });
    if (!res.ok) {
      throw new Error(`LatencyEngine getBaseline failed: ${res.status}`);
    }
    return (await res.json()) as BaselinePoint[];
  }

  async getAttribution(model: string, hour: string): Promise<AttributionResult> {
    const queryDef = LATENCY_QUERIES.FLOW_QUERY_ATTRIBUTION;
    const url = new URL(`${this.baseUrl}${queryDef.endpoint}`);
    url.searchParams.set("model", model);
    url.searchParams.set("hour", hour);

    const res = await fetch(url.toString(), { headers: this.getAuthHeaders() });
    if (!res.ok) {
      throw new Error(`LatencyEngine getAttribution failed: ${res.status}`);
    }
    return (await res.json()) as AttributionResult;
  }
}

const rawAdapter = new RawLatencyClientAdapter();
export const latencyClientService: LatencyClientAdapter = withTracing(
  withCircuitBreaker(withCache(withRetry(rawAdapter, 3, 200), 5000), 5, 10000),
  "latency-client-service"
);
