/**
 * @file step-circuit-breaker.ts
 * @description Pipeline Step 7: Bounded Circuit Breaker State Verification.
 */

import type { PipelineStep, PipelineContext } from "./types";
import { deriveRouteTemplate } from "../utils/http-utils";
import { HTTP_CONSTANTS } from "../constants";

export class StepCircuitBreaker implements PipelineStep {
  public readonly name = "CircuitBreaker";
  public readonly description = "Bounded LRU Circuit Breaker State Verification";

  public async execute<T>(ctx: PipelineContext<T>): Promise<void> {
    ctx.stepIndex++;
    ctx.routeTemplate = deriveRouteTemplate(ctx.config.url);
    ctx.circuitKey = ctx.circuitBreaker.getCircuitKey(ctx.tenantId, ctx.routeTemplate);

    if (!ctx.circuitBreaker.canExecute(ctx.circuitKey)) {
      const state = ctx.circuitBreaker.getState(ctx.circuitKey);
      ctx.span?.setAttribute(HTTP_CONSTANTS.KEY_CIRCUIT_STATE, state?.state || HTTP_CONSTANTS.CIRCUIT_OPEN);
      ctx.span?.addEvent(HTTP_CONSTANTS.EVENT_CIRCUIT_EVALUATED, {
        "circuit.state": state?.state,
        "circuit.key": ctx.circuitKey,
      });
      throw new Error(`Circuit breaker is ${state?.state || "OPEN"} for key ${ctx.circuitKey}`);
    }
  }
}
