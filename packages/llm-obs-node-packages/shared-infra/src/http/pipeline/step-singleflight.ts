/**
 * @file step-singleflight.ts
 * @description Pipeline Step 5: SHA-256 Singleflight Request Collapsing.
 */

import type { PipelineStep, PipelineContext } from "./types";
import { generateHashedKey } from "../utils/http-utils";
import { HTTP_CONSTANTS } from "../constants";

export class StepSingleflight implements PipelineStep {
  public readonly name = "Singleflight";
  public readonly description = "SHA-256 Concurrent Request Collapsing & Deduplication";

  public async execute<T>(ctx: PipelineContext<T>): Promise<void> {
    ctx.stepIndex++;
    ctx.hashedRequestKey = generateHashedKey(ctx.tenantId, ctx.config.method, ctx.config.url, ctx.config.body);

    if (!ctx.config.cancelPrevious && ctx.config.method === HTTP_CONSTANTS.METHOD_GET) {
      const existingSingleflight = ctx.inFlightSingleflights.get(ctx.hashedRequestKey);
      if (existingSingleflight) {
        ctx.singleflightHit = true;
        ctx.span?.addEvent(HTTP_CONSTANTS.EVENT_SINGLEFLIGHT_HIT, {
          "singleflight.key": ctx.hashedRequestKey,
        });
      }
    }
  }
}
