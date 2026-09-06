export interface JourneyState {
  userId?: string;
  userEmail?: string;
  userName?: string;
  orgId?: string;
  orgName?: string;
  authToken?: string;
  correlationId?: string;
  failedStepName?: string;
  failedServiceName?: string;
}

export class JourneyContext {
  private state: JourneyState = {};

  set<K extends keyof JourneyState>(key: K, value: JourneyState[K]): void {
    this.state[key] = value;
  }

  get<K extends keyof JourneyState>(key: K): JourneyState[K] {
    return this.state[key];
  }

  getState(): Readonly<JourneyState> {
    return this.state;
  }

  recordStepFailure(stepName: string, serviceName: string, error: Error): void {
    this.state.failedStepName = stepName;
    this.state.failedServiceName = serviceName;
    console.error(`[E2E Journey Failure] Step "${stepName}" failed in Service "${serviceName}": ${error.message}`);
  }

  reset(): void {
    this.state = {};
  }
}

export const journeyContext = new JourneyContext();
