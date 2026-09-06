/**
 * @file step-ssrf-validation.ts
 * @description Pipeline Step 3: Rules-Engine Powered SSRF & Target URL Validation.
 */

import type { PipelineStep, PipelineContext } from "./types";
import { validateDestinationUrl } from "../validation/destination-validator";

export class StepSsrfValidation implements PipelineStep {
  public readonly name = "SsrfValidation";
  public readonly description = "Rules-Engine SSRF Destination & IP Allowlist Guard";

  public async execute<T>(ctx: PipelineContext<T>): Promise<void> {
    ctx.stepIndex++;
    await validateDestinationUrl(ctx.config.url, ctx.config.allowedHosts);
  }
}
