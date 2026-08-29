import { propagation, context } from "@opentelemetry/api";
import { AUTH_ENDPOINTS, type EndpointMeta } from "./auth-endpoints";

export interface ExecuteParams {
  body?: any;
  pathParams?: Record<string, string>;
  token?: string;
  queryParams?: Record<string, string>;
}

export async function executeHttpRequest<T = any>(
  baseUrl: string,
  actionKey: keyof typeof AUTH_ENDPOINTS,
  params?: ExecuteParams
): Promise<T> {
  const meta: EndpointMeta = AUTH_ENDPOINTS[actionKey];
  if (!meta) {
    throw new Error(`Endpoint key "${String(actionKey)}" not defined in AUTH_ENDPOINTS registry`);
  }

  let urlPath = meta.path;
  if (params?.pathParams) {
    Object.entries(params.pathParams).forEach(([k, v]) => {
      urlPath = urlPath.replace(`:${k}`, encodeURIComponent(v));
    });
  }

  if (params?.queryParams) {
    const search = new URLSearchParams(params.queryParams).toString();
    if (search) urlPath += `?${search}`;
  }

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  const carrier: Record<string, string> = {};
  propagation.inject(context.active(), carrier);
  if (carrier.traceparent) {
    headers["traceparent"] = carrier.traceparent;
  }

  const reqId = `req-${Date.now()}-${Math.random().toString(36).substring(2, 8)}`;
  headers["x-request-id"] = reqId;
  headers["x-correlation-id"] = reqId;

  if (params?.token) {
    headers["Authorization"] = `Bearer ${params.token}`;
  }

  const response = await fetch(`${baseUrl}${urlPath}`, {
    method: meta.method,
    headers,
    body: params?.body ? JSON.stringify(params.body) : undefined,
  });

  const json = await response.json();

  if (!response.ok || json.status === "error" || json.error) {
    const err = new Error(json.error?.details || json.message || `HTTP ${response.status}`);
    (err as any).code = json.error?.code || (response.status === 401 ? "UNAUTHORIZED" : "HTTP_ERROR");
    (err as any).status = response.status;

    if (typeof window !== "undefined" && (response.status === 401 || json.message?.includes("expired"))) {
      if (!window.location.pathname.startsWith("/auth/")) {
        window.location.href = `/auth/sign-in?callbackUrl=${encodeURIComponent(window.location.pathname)}`;
      }
    }
    throw err;
  }

  return json.data as T;
}
