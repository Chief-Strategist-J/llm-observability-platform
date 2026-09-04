/**
 * @file http-client.ts
 * @description Centralized HTTP Infrastructure Barrel Export File.
 * 
 * ALGORITHM & MODULE TOPOLOGY:
 * Re-exports all decoupled HTTP infrastructure sub-modules:
 * - `client/scalable-http-client.ts`: Master ScalableHttpClient Facade & httpClient singleton.
 * - `resilience/*`: Concurrency Admission Control, Fleet Retry Budget, Tenant Rate Limiter, Circuit Breaker, LRU Cache Store.
 * - `telemetry/*`: TracedSpanFacade with Default-Deny Telemetry Filtering.
 * - `validation/*`: Rules-Engine Powered SSRF & Destination Validator.
 * - `utils/*`: URL Sanitization, Key Hashing, Route Templating, Jitter Backoff.
 * - `pipeline/*`: Decoupled Step Pipelines.
 */

import { serviceResolver } from "../discovery/engine/service-resolver";

import { mapJson } from "../data-driven/json-map";
import type { JsonMapOp } from "../data-driven/transform.types";
import { httpClient } from "./client/scalable-http-client";

export * from "./constants";
export * from "./telemetry/traced-span-facade";
export * from "./resilience/concurrency-admission-control";
export * from "./resilience/fleet-retry-budget";
export * from "./resilience/tenant-rate-limiter";
export * from "./resilience/standard-circuit-breaker";
export * from "./resilience/tenant-partitioned-cache-store";
export * from "./resilience/retry-policy";
export * from "./validation/destination-validator";
export * from "./utils/http-utils";
export * from "./utils/status-badge-registry";
export * from "./middleware/index";
export * from "./pipeline/types";
export * from "./client/scalable-http-client";


export async function executeQueryAdapter<T>(
  baseUrlOrServiceName: string,
  endpoint: string,
  params: Record<string, string | number | undefined> = {},
  serviceSub: string,
  transformOps?: JsonMapOp[]
): Promise<T> {
  let resolvedBaseUrl = baseUrlOrServiceName;

  if (!baseUrlOrServiceName.startsWith("http://") && !baseUrlOrServiceName.startsWith("https://")) {
    resolvedBaseUrl = await serviceResolver.resolve(baseUrlOrServiceName);
  } else {
    const serviceName = serviceSub.replace(/-service$/, "");
    resolvedBaseUrl = await serviceResolver.resolve(serviceName, baseUrlOrServiceName);
  }

  const url = new URL(`${resolvedBaseUrl}${endpoint}`);
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null) {
      url.searchParams.set(k, String(v));
    }
  }

  const { data } = await httpClient.get<unknown>(url.toString(), undefined, { serviceSub });

  if (transformOps) {
    return mapJson(data as Record<string, unknown>, transformOps) as unknown as T;
  }

  return data as T;
}
