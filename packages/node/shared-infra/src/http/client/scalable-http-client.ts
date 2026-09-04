/**
 * @file scalable-http-client.ts
 * @description Master ScalableHttpClient Facade Orchestrating Decoupled Step Pipelines.
 * 
 * ALGORITHM & PIPELINE EXECUTION SPECIFICATION:
 * 1. Step Pipeline Orchestration:
 *    - Executes decoupled pipeline steps in ordered sequence:
 *      Step 1: StepAdmissionControl (Inbound Capacity Load Shedding)
 *      Step 2: StepContextIsolation (Tenant Context & Payload Guard)
 *      Step 3: StepSsrfValidation (Rules-Engine Security Check)
 *      Step 4: StepRateLimit (Per-Tenant Token Bucket Outbound Limit)
 *      Step 5: StepSingleflight (SHA-256 Request Collapsing)
 *      Step 6: StepCacheEval (Tenant LRU Partition Cache Lookup & Invalidation)
 *      Step 7: StepCircuitBreaker (Bounded Circuit Breaker State Verification)
 *      Step 8: StepNetworkExecution (Socket Fetch with AWS Full Jitter Retry Loop)
 * 2. Step Counter & Telemetry Logging:
 *    - Records `execution.step_count` and `execution.current_step` in OpenTelemetry spans.
 *    - Automatically handles singleflight deduplication ($N \to 1$ RPCs).
 *    - Releases admission counters safely in `finally` blocks.
 */

import { trace, SpanKind, SpanStatusCode } from "@opentelemetry/api";
import { getCallerInfo } from "../../tracing/caller-info";
import { HTTP_CONSTANTS } from "../constants";
import { TracedSpanFacade } from "../telemetry/traced-span-facade";
import { ConcurrencyAdmissionControl } from "../resilience/concurrency-admission-control";
import { FleetRetryBudget } from "../resilience/fleet-retry-budget";
import { TenantRateLimiter } from "../resilience/tenant-rate-limiter";
import { StandardCircuitBreaker } from "../resilience/standard-circuit-breaker";
import { TenantPartitionedCacheStore } from "../resilience/tenant-partitioned-cache-store";
import { sanitizeUrlForTelemetry } from "../utils/http-utils";
import type { RequestConfig, PipelineContext, PipelineStep } from "../pipeline/types";
import { StepAdmissionControl } from "../pipeline/step-admission-control";
import { StepContextIsolation } from "../pipeline/step-context-isolation";
import { StepSsrfValidation } from "../pipeline/step-ssrf-validation";
import { StepRateLimit } from "../pipeline/step-rate-limit";
import { StepSingleflight } from "../pipeline/step-singleflight";
import { StepCacheEval } from "../pipeline/step-cache-eval";
import { StepCircuitBreaker } from "../pipeline/step-circuit-breaker";
import { StepNetworkExecution } from "../pipeline/step-network-execution";

const tracer = trace.getTracer(HTTP_CONSTANTS.TRACER_NAME);

export class ScalableHttpClient {
  private readonly admissionControl = new ConcurrencyAdmissionControl();
  private readonly retryBudget = new FleetRetryBudget();
  private readonly rateLimiter = new TenantRateLimiter();
  private readonly circuitBreaker = new StandardCircuitBreaker();
  private readonly cacheStore = new TenantPartitionedCacheStore();
  private readonly inFlightSingleflights = new Map<string, Promise<unknown>>();

  private readonly steps: PipelineStep[] = [
    new StepAdmissionControl(),
    new StepContextIsolation(),
    new StepSsrfValidation(),
    new StepRateLimit(),
    new StepSingleflight(),
    new StepCacheEval(),
    new StepCircuitBreaker(),
    new StepNetworkExecution(),
  ];

  public async execute<T>(rawConfig: RequestConfig): Promise<{ data: T; status: number; headers: any }> {
    const caller = getCallerInfo(2);
    const sanitizedUrl = sanitizeUrlForTelemetry(rawConfig.url);

    return tracer.startActiveSpan(
      `HTTP ${rawConfig.method.toUpperCase()} ${sanitizedUrl}`,
      {
        kind: SpanKind.CLIENT,
        attributes: {
          [HTTP_CONSTANTS.ATTR_HTTP_METHOD]: rawConfig.method.toUpperCase(),
          [HTTP_CONSTANTS.ATTR_HTTP_URL]: sanitizedUrl,
          [HTTP_CONSTANTS.ATTR_CODE_FUNCTION]: caller.functionName,
          [HTTP_CONSTANTS.ATTR_CODE_FILEPATH]: caller.filePath,
          [HTTP_CONSTANTS.ATTR_CODE_LINENO]: caller.lineNumber,
        },
      },
      async (rawSpan) => {
        const span = new TracedSpanFacade(rawSpan);
        const ctx: PipelineContext<T> = {
          config: rawConfig,
          stepIndex: 0,
          tenantId: HTTP_CONSTANTS.DEFAULT_TENANT_ID,
          caller,
          span,
          admissionControl: this.admissionControl,
          retryBudget: this.retryBudget,
          rateLimiter: this.rateLimiter,
          circuitBreaker: this.circuitBreaker,
          cacheStore: this.cacheStore,
          inFlightSingleflights: this.inFlightSingleflights,
        };

        try {
          // Execute decoupled steps sequentially
          for (const step of this.steps) {
            span.setAttribute("execution.current_step", step.name);
            try {
              await step.execute(ctx);
              console.log(`Step - ${ctx.stepIndex} - [${step.name}] - ${step.description} - [DONE]`);
            } catch (stepErr: any) {
              console.error(`Step - ${ctx.stepIndex} - [${step.name}] - ${step.description} - [FAILED]`);
              throw stepErr;
            }

            if (ctx.singleflightHit && ctx.hashedRequestKey) {
              const sharedPromise = this.inFlightSingleflights.get(ctx.hashedRequestKey);
              if (sharedPromise) {
                return (await sharedPromise) as { data: T; status: number; headers: any };
              }
            }

            if (ctx.cachedResponse !== undefined && step.name !== "NetworkExecution") {
              // Early exit on cache hit
              span.setStatus({ code: SpanStatusCode.OK });
              return { data: ctx.cachedResponse, status: 200, headers: {} };
            }
          }

          span.setAttribute("execution.step_count", ctx.stepIndex);

          const result = { data: ctx.cachedResponse as T, status: 200, headers: {} };

          if (rawConfig.method.toUpperCase() === HTTP_CONSTANTS.METHOD_GET && ctx.hashedRequestKey) {
            this.inFlightSingleflights.set(ctx.hashedRequestKey, Promise.resolve(result));
          }

          span.setStatus({ code: SpanStatusCode.OK });
          return result;
        } catch (err: any) {
          span.setStatus({ code: SpanStatusCode.ERROR, message: err?.message });
          span.recordException(err);
          throw err;
        } finally {
          this.admissionControl.release();
          if (ctx.hashedRequestKey) {
            this.inFlightSingleflights.delete(ctx.hashedRequestKey);
          }
          span.end();
        }
      }
    );
  }

  public async get<T>(url: string, headers?: Record<string, string>, options: Partial<RequestConfig> = {}): Promise<{ data: T; status: number; headers: any }> {
    return this.execute<T>({ ...options, method: HTTP_CONSTANTS.METHOD_GET, url, headers });
  }

  public async post<T>(url: string, body?: unknown, headers?: Record<string, string>, options: Partial<RequestConfig> = {}): Promise<{ data: T; status: number; headers: any }> {
    return this.execute<T>({ ...options, method: HTTP_CONSTANTS.METHOD_POST, url, body, headers });
  }

  public async put<T>(url: string, body?: unknown, headers?: Record<string, string>, options: Partial<RequestConfig> = {}): Promise<{ data: T; status: number; headers: any }> {
    return this.execute<T>({ ...options, method: HTTP_CONSTANTS.METHOD_PUT, url, body, headers });
  }

  public async patch<T>(url: string, body?: unknown, headers?: Record<string, string>, options: Partial<RequestConfig> = {}): Promise<{ data: T; status: number; headers: any }> {
    return this.execute<T>({ ...options, method: HTTP_CONSTANTS.METHOD_PATCH, url, body, headers });
  }

  public async delete<T>(url: string, headers?: Record<string, string>, options: Partial<RequestConfig> = {}): Promise<{ data: T; status: number; headers: any }> {
    return this.execute<T>({ ...options, method: HTTP_CONSTANTS.METHOD_DELETE, url, headers });
  }
}

export const httpClient = new ScalableHttpClient();
