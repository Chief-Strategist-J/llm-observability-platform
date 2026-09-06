/**
 * @file step-network-execution.ts
 * @description Pipeline Step 8: Network Socket Fetch with AWS Full Jitter Retry Loop.
 */


import type { PipelineStep, PipelineContext } from "./types";
import { calculateFullJitterBackoff } from "../utils/http-utils";
import { HTTP_CONSTANTS } from "../constants";

export class StepNetworkExecution implements PipelineStep {
  public readonly name = "NetworkExecution";
  public readonly description = "Network Socket Fetch & AWS Full Jitter Retry Execution";

  public async execute<T>(ctx: PipelineContext<T>): Promise<void> {
    ctx.stepIndex++;

    if (ctx.cachedResponse !== undefined) {
      return;
    }

    const maxAttempts = ctx.retryBudget.canRetry() ? 3 : 1;
    let attempt = 0;
    let lastError: Error | null = null;

    while (attempt < maxAttempts) {
      attempt++;
      ctx.span?.setAttribute(HTTP_CONSTANTS.KEY_RETRY_ATTEMPT, attempt);

      try {
        const timeoutMs = ctx.config.timeoutMs ?? 15000;
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), timeoutMs);

        const res: Response = await fetch(ctx.config.url, {
          method: ctx.config.method,
          headers: ctx.config.headers as any,
          body: ctx.config.body ? JSON.stringify(ctx.config.body) : undefined,
          signal: controller.signal as any,
        }).finally(() => clearTimeout(timer));

        if (!res.ok) {
          throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        }

        let data: T;
        const getHeader = typeof res.headers?.get === "function" ? (k: string) => res.headers.get(k) : () => null;
        const contentType = getHeader(HTTP_CONSTANTS.HEADER_CONTENT_TYPE) || "";

        if (typeof res.json === "function" && (contentType.includes(HTTP_CONSTANTS.CONTENT_TYPE_JSON) || typeof res.text !== "function")) {
          data = (await res.json()) as T;
        } else if (typeof res.text === "function") {
          data = (await res.text()) as unknown as T;
        } else if (typeof res.json === "function") {
          data = (await res.json()) as T;
        } else {
          data = {} as T;
        }

        if (ctx.circuitKey) {
          ctx.circuitBreaker.onSuccess(ctx.circuitKey);
        }

        if (ctx.config.method === HTTP_CONSTANTS.METHOD_GET && ctx.hashedRequestKey) {
          ctx.cacheStore.set(ctx.tenantId, ctx.hashedRequestKey, data);
        }

        ctx.cachedResponse = data;
        ctx.span?.setStatus({ code: 1 }); // OK
        return;
      } catch (err: any) {
        lastError = err;
        if (ctx.circuitKey) {
          ctx.circuitBreaker.onFailure(ctx.circuitKey);
        }

        if (attempt < maxAttempts) {
          ctx.retryBudget.recordRetry();
          const backoff = calculateFullJitterBackoff(attempt);
          ctx.span?.addEvent(HTTP_CONSTANTS.EVENT_RETRY_DECISION, {
            "retry.attempt": attempt,
            "retry.backoff_ms": backoff,
            "retry.error": err?.message,
          });
          await new Promise((resolve) => setTimeout(resolve, backoff));
        }
      }
    }

    if (lastError) {
      throw lastError;
    }
  }
}
