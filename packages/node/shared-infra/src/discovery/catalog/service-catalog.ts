import { HTTP_CONSTANTS } from "../../http/constants";

export interface ServiceDefinition {
  name: string;
  defaultPort: number;
  protocol: string;
  defaultUrl: string;
  serviceSub: string;
  healthPath?: string;
}

export const SERVICE_CATALOG: Record<string, ServiceDefinition> = {
  [HTTP_CONSTANTS.SERVICE_NAME_LATENCY_ENGINE]: {
    name: HTTP_CONSTANTS.SERVICE_NAME_LATENCY_ENGINE,
    defaultPort: 8003,
    protocol: HTTP_CONSTANTS.PROTOCOL_HTTP,
    defaultUrl: "http://localhost:8003",
    serviceSub: "latency-engine-service",
    healthPath: "/health",
  },
  [HTTP_CONSTANTS.SERVICE_NAME_AUTH_SERVICE]: {
    name: HTTP_CONSTANTS.SERVICE_NAME_AUTH_SERVICE,
    defaultPort: 3001,
    protocol: HTTP_CONSTANTS.PROTOCOL_HTTP,
    defaultUrl: "http://localhost:3001",
    serviceSub: "auth-service",
    healthPath: "/health",
  },
  [HTTP_CONSTANTS.SERVICE_NAME_WEB_APP]: {
    name: HTTP_CONSTANTS.SERVICE_NAME_WEB_APP,
    defaultPort: 31400,
    protocol: HTTP_CONSTANTS.PROTOCOL_HTTP,
    defaultUrl: "http://localhost:31400",
    serviceSub: HTTP_CONSTANTS.DEFAULT_SERVICE_SUB,
    healthPath: HTTP_CONSTANTS.ENDPOINT_HEALTH,
  },
  [HTTP_CONSTANTS.SERVICE_NAME_CLICKHOUSE]: {
    name: HTTP_CONSTANTS.SERVICE_NAME_CLICKHOUSE,
    defaultPort: 31421,
    protocol: HTTP_CONSTANTS.PROTOCOL_HTTP,
    defaultUrl: "http://localhost:31421",
    serviceSub: "clickhouse-service",
    healthPath: "/ping",
  },
  [HTTP_CONSTANTS.SERVICE_NAME_REDIS]: {
    name: HTTP_CONSTANTS.SERVICE_NAME_REDIS,
    defaultPort: 31413,
    protocol: HTTP_CONSTANTS.PROTOCOL_TCP,
    defaultUrl: "redis://localhost:31413",
    serviceSub: "redis-service",
  },
  [HTTP_CONSTANTS.SERVICE_NAME_KAFKA]: {
    name: HTTP_CONSTANTS.SERVICE_NAME_KAFKA,
    defaultPort: 31414,
    protocol: HTTP_CONSTANTS.PROTOCOL_TCP,
    defaultUrl: "kafka://localhost:31414",
    serviceSub: "kafka-service",
  },
  [HTTP_CONSTANTS.SERVICE_NAME_OTEL_COLLECTOR]: {
    name: HTTP_CONSTANTS.SERVICE_NAME_OTEL_COLLECTOR,
    defaultPort: 31417,
    protocol: HTTP_CONSTANTS.PROTOCOL_HTTP,
    defaultUrl: "http://localhost:31417",
    serviceSub: "otel-collector-service",
  },
} as const;
