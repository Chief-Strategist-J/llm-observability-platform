import { trace, SpanKind, SpanStatusCode } from "@opentelemetry/api";
import { HTTP_CONSTANTS } from "../../http/constants";
import { SERVICE_CATALOG } from "../catalog/service-catalog";
import type { ResolveServiceResponse } from "../responses/resolve-service.response";

const tracer = trace.getTracer(HTTP_CONSTANTS.TRACER_NAME);

export interface ServiceResolverOptions {
  registryUrl?: string;
  secret?: string;
  ttlMs?: number;
}

export class ServiceResolver {
  private registryUrl: string;
  private secret?: string;
  private ttlMs: number;
  private cache = new Map<string, { endpoint: string; cachedAt: number }>();

  constructor(options: ServiceResolverOptions = {}) {
    this.registryUrl =
      options.registryUrl ||
      process.env[HTTP_CONSTANTS.ENV_SERVICE_REGISTRY_URL] ||
      HTTP_CONSTANTS.DEFAULT_SERVICE_REGISTRY_URL;
    this.secret =
      options.secret ||
      process.env[HTTP_CONSTANTS.ENV_SERVICE_REGISTRY_SECRET] ||
      process.env[HTTP_CONSTANTS.ENV_SERVICE_REGISTRY_TOKEN];
    this.ttlMs = options.ttlMs ?? HTTP_CONSTANTS.DEFAULT_RESOLVER_TTL_MS;
  }

  private isFresh(cachedAt: number): boolean {
    return Date.now() - cachedAt < this.ttlMs;
  }

  private buildHeaders(): Record<string, string> {
    return {
      [HTTP_CONSTANTS.HEADER_ACCEPT]: HTTP_CONSTANTS.CONTENT_TYPE_JSON,
      ...(this.secret ? { [HTTP_CONSTANTS.HEADER_AUTHORIZATION]: `${HTTP_CONSTANTS.BEARER_PREFIX}${this.secret}` } : {}),
    };
  }

  private async fetchRemoteEndpoint(serviceName: string): Promise<string | null> {
    const url = new URL(HTTP_CONSTANTS.ENDPOINT_RESOLVE, this.registryUrl);
    url.searchParams.set(HTTP_CONSTANTS.PARAM_SERVICE, serviceName);

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), HTTP_CONSTANTS.DEFAULT_RESOLVER_TIMEOUT_MS);

    try {
      const res = await fetch(url.toString(), {
        method: HTTP_CONSTANTS.METHOD_GET,
        headers: this.buildHeaders(),
        signal: controller.signal,
      }).finally(() => clearTimeout(timeoutId));

      const json: ResolveServiceResponse = res.ok ? await res.json() : {};
      return json.success && json.data?.endpoint ? json.data.endpoint : null;
    } catch {
      return null;
    }
  }

  public async resolve(serviceName: string, fallbackUrl?: string): Promise<string> {
    return tracer.startActiveSpan(
      `ServiceResolver.resolve:${serviceName}`,
      {
        kind: SpanKind.CLIENT,
        attributes: {
          [HTTP_CONSTANTS.ATTR_HTTP_METHOD]: HTTP_CONSTANTS.METHOD_GET,
          [HTTP_CONSTANTS.KEY_CACHE_KEY]: serviceName,
        },
      },
      async (span) => {
        try {
          const cached = this.cache.get(serviceName);
          if (cached && this.isFresh(cached.cachedAt)) {
            span.setAttribute(HTTP_CONSTANTS.KEY_CACHE_HIT, true);
            span.setAttribute(HTTP_CONSTANTS.ATTR_HTTP_URL, cached.endpoint);
            span.setStatus({ code: SpanStatusCode.OK });
            return cached.endpoint;
          }

          span.setAttribute(HTTP_CONSTANTS.KEY_CACHE_HIT, false);
          const remoteEndpoint = await this.fetchRemoteEndpoint(serviceName);
          if (remoteEndpoint) {
            this.cache.set(serviceName, { endpoint: remoteEndpoint, cachedAt: Date.now() });
            span.setAttribute(HTTP_CONSTANTS.ATTR_HTTP_URL, remoteEndpoint);
            span.setStatus({ code: SpanStatusCode.OK });
            return remoteEndpoint;
          }

          const catalogDef = SERVICE_CATALOG[serviceName];
          const resolvedFallback =
            cached?.endpoint || fallbackUrl || catalogDef?.defaultUrl || `${HTTP_CONSTANTS.PROTOCOL_HTTP}://${HTTP_CONSTANTS.HOST_LOCALHOST}:${serviceName}`;

          span.setAttribute(HTTP_CONSTANTS.ATTR_HTTP_URL, resolvedFallback);
          span.setStatus({ code: SpanStatusCode.OK });
          return resolvedFallback;
        } catch (err: any) {
          span.setStatus({ code: SpanStatusCode.ERROR, message: err?.message });
          throw err;
        } finally {
          span.end();
        }
      }
    );
  }

  public clearCache(): void {
    this.cache.clear();
  }
}

export const serviceResolver = new ServiceResolver();

export async function resolveServiceUrl(
  serviceName: string,
  fallbackUrl?: string
): Promise<string> {
  return serviceResolver.resolve(serviceName, fallbackUrl);
}
