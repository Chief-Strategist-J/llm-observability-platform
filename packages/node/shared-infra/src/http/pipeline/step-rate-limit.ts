/**
 * @file step-rate-limit.ts
 * @description Pipeline Step 4: Token Bucket Rate Limiting per Tenant.
 */

import type { PipelineStep, PipelineContext } from "./types";

export class StepRateLimit implements PipelineStep {
  public readonly name = "RateLimit";
  public readonly description = "Per-Tenant Token Bucket Outbound Rate Limiting";

  public async execute<T>(ctx: PipelineContext<T>): Promise<void> {
    ctx.stepIndex++;
    if (!ctx.rateLimiter.allowRequest(ctx.tenantId)) {
      throw new Error(`Rate limit exceeded for tenant ${ctx.tenantId}`);
    }
    ctx.retryBudget.recordRequest();
  }
}
