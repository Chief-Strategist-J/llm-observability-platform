export interface WorkflowStep {
  name: string;
  type: 'validateTenant' | 'evaluateRules' | 'provisionSession' | 'emitAuthEvent';
}

export const AUTH_PROVISIONING_WORKFLOW: WorkflowStep[] = [
  { name: 'Step 1: Validate Tenant Domain Context', type: 'validateTenant' },
  { name: 'Step 2: Evaluate Auth & RBAC Rules', type: 'evaluateRules' },
  { name: 'Step 3: Provision JWT & Redis Session', type: 'provisionSession' },
  { name: 'Step 4: Emit Auth Event Notification', type: 'emitAuthEvent' },
];

export async function executeAuthProvisioningWorkflow(
  workflow: WorkflowStep[],
  executor: (step: WorkflowStep) => Promise<void>
): Promise<void> {
  for (const step of workflow) {
    await executor(step);
  }
}
