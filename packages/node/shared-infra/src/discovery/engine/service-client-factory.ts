import {
  withRetry,
  withCache,
  withCircuitBreaker,
  withTracing,
} from "../../data-driven/adapter-decorators";
import { executeQueryAdapter } from "../../http/http-client";
import { SERVICE_CATALOG } from "../catalog/service-catalog";
import type { JsonMapOp } from "../../data-driven/transform.types";

export interface QuerySpec {
  endpoint: string;
  serviceSub?: string;
  transformOps?: JsonMapOp[];
}

export function executeServiceClientQuery<T>(
  serviceKey: string,
  querySpec: QuerySpec,
  params: Record<string, string | number | undefined> = {}
): Promise<T> {
  const serviceDef = SERVICE_CATALOG[serviceKey];
  const serviceSub = querySpec.serviceSub || serviceDef?.serviceSub || serviceKey;
  return executeQueryAdapter<T>(
    serviceKey,
    querySpec.endpoint,
    params,
    serviceSub,
    querySpec.transformOps
  );
}

export function createServiceClient<T extends object>(
  serviceKey: string,
  implementation: T,
  options: {
    retryCount?: number;
    retryDelayMs?: number;
    cacheTtlMs?: number;
    circuitFailureThreshold?: number;
    circuitResetTimeoutMs?: number;
  } = {}
): T {
  const retryCount = options.retryCount ?? 3;
  const retryDelayMs = options.retryDelayMs ?? 200;
  const cacheTtlMs = options.cacheTtlMs ?? 5000;
  const failureThreshold = options.circuitFailureThreshold ?? 5;
  const resetTimeoutMs = options.circuitResetTimeoutMs ?? 10000;

  return withTracing(
    withCircuitBreaker(
      withCache(
        withRetry(implementation as any, {
          retries: retryCount,
          backoffMs: retryDelayMs,
        }),
        { ttlMs: cacheTtlMs }
      ),
      {
        failureThreshold,
        resetTimeoutMs,
      }
    ),
    `${serviceKey}-client-service`
  ) as T;
}
