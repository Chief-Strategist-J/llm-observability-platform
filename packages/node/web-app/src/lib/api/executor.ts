/**
 * ============================================================================
 * ALGORITHM: HTTP REQUEST EXECUTION & OPEN-TELEMETRY PROPAGATION ENGINE
 * ============================================================================
 * STEP 1: REGISTRY LOOKUP
 *         Retrieve target endpoint metadata from centralized AUTH_ENDPOINTS registry.
 * STEP 2: PATH PARAMETER INTERPOLATION
 *         Substitute dynamic URI tokens (e.g. ":id") with URI-encoded values.
 * STEP 3: QUERY STRING COMPOSITION
 *         Append serialized URLSearchParams string to final request path.
 * STEP 4: OPENTELEMETRY TRACE PROPAGATION
 *         Inject active OpenTelemetry context headers (traceparent) into request headers.
 * STEP 5: CORRELATION IDENTIFIERS
 *         Generate unique "x-request-id" and "x-correlation-id" header tokens.
 * STEP 6: AUTHORIZATION TOKEN ATTACHMENT
 *         If bearer token is provided, attach "Authorization: Bearer <token>".
 * STEP 7: HTTP FETCH DISPATCH & RESPONSE PARSING
 *         Perform asynchronous fetch request with JSON body. Parse JSON response.
 * STEP 8: ERROR CLASSIFICATION & SESSION SANITATION
 *         If status >= 400 or payload reports error, throw standardized Error.
 *         On 401 Unauthorized in client browser, redirect to login screen.
 * ============================================================================
 */

import { propagation, context } from "@opentelemetry/api";
import { AUTH_ENDPOINTS, type ApiEndpointKey } from "./auth-endpoints";
import { httpClient } from "@observability/shared-infra";

export interface ExecuteParams {
  pathParams?: Record<string, string>;
  queryParams?: Record<string, string>;
  body?: any;
  token?: string;
}

export async function executeHttpRequest<T = any>(
  baseUrl: string,
  key: ApiEndpointKey,
  params?: ExecuteParams
): Promise<T> {
  const meta = AUTH_ENDPOINTS[key];
  if (!meta) {
    throw new Error(`Endpoint key "${key}" not registered in AUTH_ENDPOINTS.`);
  }

  let urlPath = meta.path;
  if (params?.pathParams) {
    for (const [pKey, pVal] of Object.entries(params.pathParams)) {
      urlPath = urlPath.replace(`:${pKey}`, encodeURIComponent(pVal));
    }
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

  const host = baseUrl || process.env.NEXT_PUBLIC_API_URL || "";
  const fullUrl = `${host}${urlPath}`;

  try {
    const res = await httpClient.execute<any>({
      method: meta.method,
      url: fullUrl,
      headers,
      body: params?.body,
    });

    const json = res.data;

    if (json?.status === "error" || json?.error) {
      const err = new Error(json.error?.details || json.message || `HTTP ${res.status}`);
      (err as any).code = json.error?.code || (res.status === 401 ? "UNAUTHORIZED" : "HTTP_ERROR");
      (err as any).status = res.status;
      throw err;
    }

    return json as T;
  } catch (err: any) {
    if (typeof window !== "undefined" && (err?.status === 401 || err?.message?.includes("expired"))) {
      if (!window.location.pathname.startsWith("/auth/")) {
        window.location.href = `/auth/sign-in?callbackUrl=${encodeURIComponent(window.location.pathname)}`;
      }
    }
    throw err;
  }
}

export async function executeApiRequest<T = any>(
  key: ApiEndpointKey,
  params?: ExecuteParams
): Promise<T> {
  return executeHttpRequest<T>("", key, params);
}

