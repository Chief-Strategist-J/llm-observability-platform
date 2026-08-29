import crypto from "crypto";
import { mapJson } from "@/core/data-driven/json-map";
import type { JsonMapOp } from "@/core/data-driven/transform.types";
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
    this.baseUrl = process.env.LATENCY_ENGINE_URL || "http://localhost:8003";
  }

  private getAuthHeaders(): Record<string, string> {
    const secret = process.env.JWT_SECRET || "dev-secret-key-change-in-production";
    const header = { alg: "HS256", typ: "JWT" };
    const now = Math.floor(Date.now() / 1000);
    const payload = { sub: "nextjs-web-app", iat: now, exp: now + 3600 };

    const headerB64 = Buffer.from(JSON.stringify(header)).toString("base64url");
    const payloadB64 = Buffer.from(JSON.stringify(payload)).toString("base64url");
    const signingInput = `${headerB64}.${payloadB64}`;

    const signatureB64 = crypto
      .createHmac("sha256", secret)
      .update(signingInput)
      .digest("base64url");

    return {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${signingInput}.${signatureB64}`,
    };
  }

  private async executeQuery<T>(
    endpoint: string,
    params: Record<string, string | number>,
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
      throw new Error(`LatencyEngine request to ${endpoint} failed: ${res.status}`);
    }

    const raw = await res.json();
    return transformOps ? (mapJson(raw, transformOps) as unknown as T) : (raw as T);
  }

  async getPercentiles(model: string, hourOfDay: number, quantiles = "0.50,0.95,0.99"): Promise<PercentilesResult> {
    return this.executeQuery<PercentilesResult>(
      LATENCY_QUERIES.FLOW_QUERY_PERCENTILES.endpoint,
      { model, hour_of_day: hourOfDay, quantiles },
      PercentilesFromApiOps
    );
  }

  async getSLO(model: string, endpoint: string): Promise<SLOResult> {
    return this.executeQuery<SLOResult>(
      LATENCY_QUERIES.FLOW_QUERY_SLO.endpoint,
      { model, endpoint },
      SLOFromApiOps
    );
  }

  async getBaseline(model: string, hourOfDay: number, days = 7): Promise<BaselinePoint[]> {
    return this.executeQuery<BaselinePoint[]>(
      LATENCY_QUERIES.FLOW_QUERY_BASELINE.endpoint,
      { model, hour_of_day: hourOfDay, days }
    );
  }

  async getAttribution(model: string, hour: string): Promise<AttributionResult> {
    return this.executeQuery<AttributionResult>(
      LATENCY_QUERIES.FLOW_QUERY_ATTRIBUTION.endpoint,
      { model, hour }
    );
  }
}

const rawAdapter = new RawLatencyClientAdapter();
export const latencyClientService: LatencyClientAdapter = withTracing(
  withCircuitBreaker(withCache(withRetry(rawAdapter, 3, 200), 5000), 5, 10000),
  "latency-client-service"
);
