import { trace, SpanKind, SpanStatusCode } from "@opentelemetry/api";
import { HTTP_CONSTANTS } from "../../http/constants";
import { httpClient } from "../../http/client/scalable-http-client";
import { SERVICE_CATALOG } from "../catalog/service-catalog";
import type { RegisterInstanceRequest } from "../requests/register-instance.request";
import type { HeartbeatInstanceRequest } from "../requests/heartbeat-instance.request";
import type { DeregisterInstanceRequest } from "../requests/deregister-instance.request";
import type { RegisterInstanceResponse } from "../responses/register-instance.response";
import type { HeartbeatInstanceResponse } from "../responses/heartbeat-instance.response";
import type { DeregisterInstanceResponse } from "../responses/deregister-instance.response";

const tracer = trace.getTracer(HTTP_CONSTANTS.TRACER_NAME);

export interface ServiceRegistryManagerOptions {
  name?: string;
  host?: string;
  port?: number;
  protocol?: string;
  registryUrl?: string;
  secret?: string;
  heartbeatIntervalMs?: number;
}

export class ServiceRegistryManager {
  private name: string;
  private host: string;
  private port: number;
  private protocol: string;
  private registryUrl: string;
  private secret?: string;
  private instanceId: string | null = null;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private heartbeatIntervalMs: number;

  constructor(options: ServiceRegistryManagerOptions = {}) {
    const webAppDef = SERVICE_CATALOG[HTTP_CONSTANTS.SERVICE_NAME_WEB_APP];
    this.name = options.name || process.env[HTTP_CONSTANTS.ENV_SERVICE_NAME] || webAppDef?.name || HTTP_CONSTANTS.SERVICE_NAME_WEB_APP;
    this.host = options.host || process.env[HTTP_CONSTANTS.ENV_HOST] || HTTP_CONSTANTS.HOST_LOCALHOST;
    this.port = options.port || parseInt(process.env[HTTP_CONSTANTS.ENV_PORT] || String(webAppDef?.defaultPort || HTTP_CONSTANTS.DEFAULT_PORT_WEB_APP), 10);
    this.protocol = options.protocol || webAppDef?.protocol || HTTP_CONSTANTS.PROTOCOL_HTTP;
    this.registryUrl =
      options.registryUrl ||
      process.env[HTTP_CONSTANTS.ENV_SERVICE_REGISTRY_URL] ||
      HTTP_CONSTANTS.DEFAULT_SERVICE_REGISTRY_URL;
    this.secret =
      options.secret ||
      process.env[HTTP_CONSTANTS.ENV_SERVICE_REGISTRY_SECRET] ||
      process.env[HTTP_CONSTANTS.ENV_SERVICE_REGISTRY_TOKEN];
    this.heartbeatIntervalMs = options.heartbeatIntervalMs || HTTP_CONSTANTS.DEFAULT_HEARTBEAT_INTERVAL_MS;
  }

  private buildHeaders(): Record<string, string> {
    return {
      [HTTP_CONSTANTS.HEADER_CONTENT_TYPE]: HTTP_CONSTANTS.CONTENT_TYPE_JSON,
      ...(this.secret ? { [HTTP_CONSTANTS.HEADER_AUTHORIZATION]: `${HTTP_CONSTANTS.BEARER_PREFIX}${this.secret}` } : {}),
    };
  }

  public async register(): Promise<void> {
    return tracer.startActiveSpan(
      `ServiceRegistryManager.register:${this.name}`,
      {
        kind: SpanKind.CLIENT,
        attributes: {
          [HTTP_CONSTANTS.ATTR_HTTP_METHOD]: HTTP_CONSTANTS.METHOD_POST,
          [HTTP_CONSTANTS.ATTR_HTTP_URL]: `${this.registryUrl}${HTTP_CONSTANTS.ENDPOINT_REGISTER}`,
        },
      },
      async (span) => {
        try {
          const url = new URL(HTTP_CONSTANTS.ENDPOINT_REGISTER, this.registryUrl);
          const payload: RegisterInstanceRequest = {
            name: this.name,
            host: this.host,
            port: this.port,
            protocol: this.protocol,
            healthCheck: {
              protocol: HTTP_CONSTANTS.PROTOCOL_HTTP,
              path: HTTP_CONSTANTS.ENDPOINT_HEALTH,
            },
          };

          const res = await httpClient.post<RegisterInstanceResponse>(
            url.toString(),
            payload,
            this.buildHeaders()
          );

          const json = res.data;
          if (!json.success || !json.data?.id) {
            span.setStatus({ code: SpanStatusCode.ERROR, message: HTTP_CONSTANTS.MSG_MISSING_INSTANCE_ID });
            return;
          }

          this.instanceId = json.data.id;
          this.startHeartbeat();
          this.attachShutdownHooks();
          span.setStatus({ code: SpanStatusCode.OK });
        } catch (err: any) {
          span.setStatus({ code: SpanStatusCode.ERROR, message: err?.message || String(err) });
          span.recordException(err);
        } finally {
          span.end();
        }
      }
    );
  }

  public async sendHeartbeat(): Promise<void> {
    if (!this.instanceId) return;

    return tracer.startActiveSpan(
      `ServiceRegistryManager.sendHeartbeat:${this.name}`,
      {
        kind: SpanKind.CLIENT,
        attributes: {
          [HTTP_CONSTANTS.ATTR_HTTP_METHOD]: HTTP_CONSTANTS.METHOD_POST,
        },
      },
      async (span) => {
        try {
          const url = new URL(HTTP_CONSTANTS.ENDPOINT_HEARTBEAT, this.registryUrl);
          const payload: HeartbeatInstanceRequest = {
            name: this.name,
            instanceId: this.instanceId!,
          };

          const res = await httpClient.post<HeartbeatInstanceResponse>(
            url.toString(),
            payload,
            this.buildHeaders()
          );

          const json = res.data;
          span.setStatus({ code: json.success ? SpanStatusCode.OK : SpanStatusCode.ERROR });
        } catch (err: any) {
          span.setStatus({ code: SpanStatusCode.ERROR, message: err?.message || String(err) });
          span.recordException(err);
        } finally {
          span.end();
        }
      }
    );
  }

  public async deregister(): Promise<void> {
    this.stopHeartbeat();
    if (!this.instanceId) return;

    return tracer.startActiveSpan(
      `ServiceRegistryManager.deregister:${this.name}`,
      {
        kind: SpanKind.CLIENT,
        attributes: {
          [HTTP_CONSTANTS.ATTR_HTTP_METHOD]: HTTP_CONSTANTS.METHOD_POST,
        },
      },
      async (span) => {
        try {
          const url = new URL(HTTP_CONSTANTS.ENDPOINT_DEREGISTER, this.registryUrl);
          const payload: DeregisterInstanceRequest = {
            name: this.name,
            instanceId: this.instanceId!,
          };

          const res = await httpClient.post<DeregisterInstanceResponse>(
            url.toString(),
            payload,
            this.buildHeaders()
          );

          const json = res.data;
          this.instanceId = null;
          span.setStatus({ code: json.success ? SpanStatusCode.OK : SpanStatusCode.ERROR });
        } catch (err: any) {
          span.setStatus({ code: SpanStatusCode.ERROR, message: err?.message || String(err) });
          span.recordException(err);
        } finally {
          span.end();
        }
      }
    );
  }

  private startHeartbeat(): void {
    this.stopHeartbeat();
    this.heartbeatTimer = setInterval(
      () => this.sendHeartbeat(),
      this.heartbeatIntervalMs
    );
  }

  private stopHeartbeat(): void {
    if (!this.heartbeatTimer) return;
    clearInterval(this.heartbeatTimer);
    this.heartbeatTimer = null;
  }

  private attachShutdownHooks(): void {
    const shutdown = () => this.deregister();
    process.once(HTTP_CONSTANTS.SIGNAL_SIGINT, shutdown);
    process.once(HTTP_CONSTANTS.SIGNAL_SIGTERM, shutdown);
  }

}

export const platformRegistryManager = new ServiceRegistryManager();
