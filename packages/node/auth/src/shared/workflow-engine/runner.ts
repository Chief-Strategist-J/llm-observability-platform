import { trace } from '@opentelemetry/api';
import { stepRegistry } from './step-registry';

export interface WorkflowStep {
  id: string;
  type: string;
  params: Record<string, unknown>;
  next?: string;
}

export interface WorkflowDefinition {
  name: string;
  steps: WorkflowStep[];
}

export async function runWorkflow(
  workflow: WorkflowDefinition,
  initialContext: Record<string, unknown> = {}
): Promise<Record<string, unknown>> {
  const tracer = trace.getTracer('workflow-engine');
  return tracer.startActiveSpan(`workflow:${workflow.name}`, async (span) => {
    const context: Record<string, unknown> = { ...initialContext, results: {} };

    try {
      for (const step of workflow.steps) {
        const handler = stepRegistry.get(step.type);
        if (!handler) {
          throw new Error(`Unknown step type: ${step.type} in step ${step.id}`);
        }

        const stepResult = await tracer.startActiveSpan(`step:${step.id}`, async (stepSpan) => {
          try {
            const res = await handler(step.params, context);
            stepSpan.end();
            return res;
          } catch (err) {
            stepSpan.recordException(err as Error);
            stepSpan.end();
            throw err;
          }
        });

        (context.results as Record<string, unknown>)[step.id] = stepResult;
      }
      span.end();
      return context;
    } catch (err) {
      span.recordException(err as Error);
      span.end();
      throw err;
    }
  });
}
