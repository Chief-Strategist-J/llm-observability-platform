/**
 * @file step-cache-eval.ts
 * @description Pipeline Step 6: Tenant LRU Cache Evaluation & Invalidation.
 */

import type { PipelineStep, PipelineContext } from "./types";
import { isCacheDisabled } from "../utils/http-utils";
import { HTTP_CONSTANTS } from "../constants";

export class StepCacheEval implements PipelineStep {
  public readonly name = "CacheEval";
  public readonly description = "Tenant Partitioned LRU Cache Lookup & Invalidation";

  public async execute<T>(ctx: PipelineContext<T>): Promise<void> {
    ctx.stepIndex++;
    const method = ctx.config.method.toUpperCase();

    if (([HTTP_CONSTANTS.METHOD_POST, HTTP_CONSTANTS.METHOD_PUT, HTTP_CONSTANTS.METHOD_PATCH, HTTP_CONSTANTS.METHOD_DELETE] as string[]).includes(method)) {

      ctx.cacheStore.clear(ctx.tenantId);
      return;
    }

    if (method === HTTP_CONSTANTS.METHOD_GET) {
      const disabled = isCacheDisabled(ctx.config.noCache, ctx.config.headers || {});
      if (!disabled && ctx.hashedRequestKey) {
        const cached = ctx.cacheStore.get<T>(ctx.tenantId, ctx.hashedRequestKey);
        if (cached !== undefined) {
          ctx.cachedResponse = cached;
          ctx.span?.setAttribute(HTTP_CONSTANTS.KEY_CACHE_HIT, true);
          ctx.span?.addEvent(HTTP_CONSTANTS.EVENT_CACHE_EVALUATED, {
            "cache.hit": true,
            "cache.key": ctx.hashedRequestKey,
          });
        }
      }
    }
  }
}
