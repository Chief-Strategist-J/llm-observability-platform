/**
 * @file step-admission-control.ts
 * @description Pipeline Step 1: Concurrency Admission Control & Load Shedding.
 */

import type { PipelineStep, PipelineContext } from "./types";
import { HTTP_CONSTANTS } from "../constants";

export class StepAdmissionControl implements PipelineStep {
  public readonly name = "AdmissionControl";
  public readonly description = "Concurrency Admission Control & Fleet Capacity Guard";

  public async execute<T>(ctx: PipelineContext<T>): Promise<void> {
    ctx.stepIndex++;
    if (!ctx.admissionControl.acquire()) {
      const activeCount = ctx.admissionControl.getActiveCount();
      ctx.span?.addEvent(HTTP_CONSTANTS.EVENT_EXECUTION_FAILURE, {
        "admission_control.shed": true,
        "active_count": activeCount,
      });
      throw new Error(`Too Many Requests - Fleet In-Flight Concurrency Capacity (${activeCount}) Exceeded`);
    }
  }
}
