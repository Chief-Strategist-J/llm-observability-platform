export interface HealthCheckSpec {
  protocol: string;
  path?: string;
  timeoutMs?: number;
}

export interface RegisterInstanceRequest {
  name: string;
  host: string;
  port: number;
  protocol: string;
  version?: string;
  weight?: number;
  metadata?: Record<string, string>;
  healthCheck?: HealthCheckSpec;
}
