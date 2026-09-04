/**
 * @file types.ts
 * @description Decoupled Pipeline Step Types & Execution Context Contracts.
 */


import type { TracedSpanFacade } from "../telemetry/traced-span-facade";
import type { ConcurrencyAdmissionControl } from "../resilience/concurrency-admission-control";
import type { FleetRetryBudget } from "../resilience/fleet-retry-budget";
import type { TenantRateLimiter } from "../resilience/tenant-rate-limiter";
import type { StandardCircuitBreaker } from "../resilience/standard-circuit-breaker";
import type { TenantPartitionedCacheStore } from "../resilience/tenant-partitioned-cache-store";

export interface RequestConfig {
  method: string;
  url: string;
  headers?: Record<string, string>;
  body?: unknown;
  timeoutMs?: number;
  noCache?: boolean;
  cancelPrevious?: boolean;
  allowedHosts?: string[];
  maxBodySizeBytes?: number;
  [key: string]: unknown;
}

export interface PipelineContext<T = unknown> {
  config: RequestConfig;
  stepIndex: number;
  tenantId: string;
  caller: { functionName: string; filePath: string; lineNumber: number };
  span?: TracedSpanFacade;
  hashedRequestKey?: string;
  routeTemplate?: string;
  circuitKey?: string;
  singleflightHit?: boolean;
  cachedResponse?: T;
  
  // Shared Resilience References
  admissionControl: ConcurrencyAdmissionControl;
  retryBudget: FleetRetryBudget;
  rateLimiter: TenantRateLimiter;
  circuitBreaker: StandardCircuitBreaker;
  cacheStore: TenantPartitionedCacheStore;
  inFlightSingleflights: Map<string, Promise<unknown>>;
}

export interface PipelineStep {
  name: string;
  description: string;
  execute<T>(ctx: PipelineContext<T>): Promise<void>;
}
