import { trace, SpanKind, SpanStatusCode } from "@opentelemetry/api";
import { httpClient } from "../../http/client/scalable-http-client";
import { HTTP_CONSTANTS } from "../../http/constants";
import { SERVICE_CATALOG, ServiceDefinition } from "../catalog/service-catalog";
import type { ResolveServiceResponse, ResolveServiceResponseData } from "../responses/resolve-service.response";

const tracer = trace.getTracer(HTTP_CONSTANTS.TRACER_NAME);

export interface ServiceEndpoint {
  serviceKey: string;
  name: string;
  port: number;
  baseUrl: string;
}

const SERVICE_SUFFIX = "-service";

interface ResolutionCacheEntry {
  url: string;
  expiresAt: number;
}

interface ServiceEndpointCacheEntry {
  endpoint: ServiceEndpoint;
  expiresAt: number;
}

export class ServiceResolver {
  private catalog: Record<string, ServiceDefinition> = SERVICE_CATALOG;
  private registryUrl: string;
  private cache = new Map<string, ResolutionCacheEntry>();
  private endpointCache = new Map<string, ServiceEndpointCacheEntry>();
  private readonly ttlMs = HTTP_CONSTANTS.DEFAULT_RESOLVER_TTL_MS || 30000;

  constructor() {
    this.registryUrl = process.env[HTTP_CONSTANTS.ENV_SERVICE_REGISTRY_URL] || HTTP_CONSTANTS.DEFAULT_SERVICE_REGISTRY_URL;
  }

  public clearCache(): void {
    this.cache.clear();
    this.endpointCache.clear();
  }

  public invalidate(serviceKey: string): void {
    this.cache.delete(serviceKey);
    this.endpointCache.delete(serviceKey);
  }

  private findCatalogEntry(key: string): ServiceDefinition | undefined {
    if (this.catalog[key]) return this.catalog[key];
    const normalized = key.endsWith(SERVICE_SUFFIX) ? key.slice(0, -SERVICE_SUFFIX.length) : key;
    if (this.catalog[normalized]) return this.catalog[normalized];
    if (this.catalog[`${normalized}${SERVICE_SUFFIX}`]) return this.catalog[`${normalized}${SERVICE_SUFFIX}`];
    return undefined;
  }

  public async resolve(serviceKey: string, fallbackUrl?: string): Promise<string> {
    const cached = this.cache.get(serviceKey);
    if (cached && cached.expiresAt > Date.now()) {
      return cached.url;
    }

    return tracer.startActiveSpan(
      `ServiceResolver.resolve:${serviceKey}`,
      {
        kind: SpanKind.CLIENT,
        attributes: {
          [HTTP_CONSTANTS.ATTR_HTTP_METHOD]: HTTP_CONSTANTS.METHOD_GET,
        },
      },
      async (span) => {
        let resolvedUrl = "";

        const keysToTry = [serviceKey];
        const normalized = serviceKey.endsWith(SERVICE_SUFFIX) ? serviceKey.slice(0, -SERVICE_SUFFIX.length) : `${serviceKey}${SERVICE_SUFFIX}`;
        if (!keysToTry.includes(normalized)) {
          keysToTry.push(normalized);
        }

        for (const targetKey of keysToTry) {
          try {
            const url = `${this.registryUrl}${HTTP_CONSTANTS.ENDPOINT_RESOLVE}?${HTTP_CONSTANTS.PARAM_SERVICE}=${encodeURIComponent(targetKey)}`;
            const response = await httpClient.get<ResolveServiceResponse>(url);
            const responseData: ResolveServiceResponse | undefined = response.data;

            if (responseData && responseData.success && responseData.data?.endpoint) {
              resolvedUrl = responseData.data.endpoint;
              span.setStatus({ code: SpanStatusCode.OK });
              break;
            }
          } catch (err: any) {
            span.setStatus({
              code: SpanStatusCode.ERROR,
              message: `Service Discovery HTTP resolution failed for '${targetKey}': ${err?.message || String(err)}`,
            });
            span.recordException(err);
          }
        }
        span.end();

        if (!resolvedUrl) {
          const entry = this.findCatalogEntry(serviceKey);
          resolvedUrl = entry ? entry.defaultUrl : (fallbackUrl || "");
        }

        if (resolvedUrl) {
          this.cache.set(serviceKey, {
            url: resolvedUrl,
            expiresAt: Date.now() + this.ttlMs,
          });
        }

        return resolvedUrl;
      }
    );
  }

  public async resolveService(serviceKey: string): Promise<ServiceEndpoint | null> {
    const cached = this.endpointCache.get(serviceKey);
    if (cached && cached.expiresAt > Date.now()) {
      return cached.endpoint;
    }

    return tracer.startActiveSpan(
      `ServiceResolver.resolveService:${serviceKey}`,
      {
        kind: SpanKind.CLIENT,
        attributes: {
          [HTTP_CONSTANTS.ATTR_HTTP_METHOD]: HTTP_CONSTANTS.METHOD_GET,
        },
      },
      async (span) => {
        const entry = this.findCatalogEntry(serviceKey);
        let resultEndpoint: ServiceEndpoint | null = null;

        try {
          const url = `${this.registryUrl}${HTTP_CONSTANTS.ENDPOINT_RESOLVE}?${HTTP_CONSTANTS.PARAM_SERVICE}=${encodeURIComponent(serviceKey)}`;
          const response = await httpClient.get<ResolveServiceResponse>(url);
          const responseData: ResolveServiceResponse | undefined = response.data;

          if (responseData && responseData.success && responseData.data?.endpoint) {
            const data: ResolveServiceResponseData = responseData.data;
            const ep = data.endpoint;
            const primaryInstance = data.instances?.[0];
            span.setStatus({ code: SpanStatusCode.OK });
            resultEndpoint = {
              serviceKey,
              name: data.service || serviceKey,
              port: primaryInstance?.port || (entry ? entry.defaultPort : HTTP_CONSTANTS.DEFAULT_PORT_WEB_APP),
              baseUrl: ep,
            };
          }
        } catch (err: any) {
          span.setStatus({
            code: SpanStatusCode.ERROR,
            message: `Service Discovery detailed resolution failed for '${serviceKey}': ${err?.message || String(err)}`,
          });
          span.recordException(err);
        } finally {
          span.end();
        }

        if (!resultEndpoint && entry) {
          resultEndpoint = {
            serviceKey,
            name: entry.name,
            port: entry.defaultPort,
            baseUrl: entry.defaultUrl,
          };
        }

        if (resultEndpoint) {
          this.endpointCache.set(serviceKey, {
            endpoint: resultEndpoint,
            expiresAt: Date.now() + this.ttlMs,
          });
        }

        return resultEndpoint;
      }
    );
  }

  public listServices(): ServiceEndpoint[] {
    return Object.keys(this.catalog).map((key) => {
      const entry = this.catalog[key]!;
      return {
        serviceKey: key,
        name: entry.name,
        port: entry.defaultPort,
        baseUrl: entry.defaultUrl,
      };
    });
  }
}

export const serviceResolver = new ServiceResolver();

