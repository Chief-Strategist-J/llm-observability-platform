import { propagation, context } from "@opentelemetry/api";
import { withRetry, withCache, withCircuitBreaker } from "../core/data-driven/adapter-decorators";
import { AUTH_ENDPOINTS } from "./auth-endpoints";

const AUTH_SERVICE_URL = process.env.NEXT_PUBLIC_AUTH_SERVICE_URL || process.env.AUTH_SERVICE_URL || "http://localhost:3001";

export class RawAuthApiClient {
  private baseUrl: string;

  constructor(baseUrl = AUTH_SERVICE_URL) {
    this.baseUrl = baseUrl;
  }

  async execute<T = any>(actionKey: keyof typeof AUTH_ENDPOINTS, params?: { body?: any; pathParams?: Record<string, string>; token?: string; queryParams?: Record<string, string> }): Promise<T> {
    const meta = AUTH_ENDPOINTS[actionKey];
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

    const response = await fetch(`${this.baseUrl}${urlPath}`, {
      method: meta.method,
      headers,
      body: params?.body ? JSON.stringify(params.body) : undefined,
    });

    const json = await response.json();
    if (!response.ok || json.status === "error" || json.error) {
      const err = new Error(json.error?.details || json.message || `HTTP ${response.status}`);
      (err as any).code = json.error?.code || "HTTP_ERROR";
      (err as any).status = response.status;
      throw err;
    }

    return json.data as T;
  }

  signUp(payload: { email: string; password?: string; name: string; organization_name: string; role?: string }) {
    return this.execute("signUp", { body: payload });
  }

  signIn(payload: { email: string; password?: string }) {
    return this.execute("signIn", { body: payload });
  }

  signOut(token?: string) {
    return this.execute("signOut", { token });
  }

  getSession(token: string) {
    return this.execute("getSession", { token });
  }

  listOrganizations(token?: string) {
    return this.execute("listOrganizations", { token });
  }

  createOrganization(name: string, slug?: string, token?: string) {
    return this.execute("createOrganization", { body: { name, slug }, token });
  }

  getOrganization(orgId: string, token?: string) {
    return this.execute("getOrganization", { pathParams: { id: orgId }, token });
  }

  updateOrganization(orgId: string, payload: { name?: string; slug?: string }, token?: string) {
    return this.execute("updateOrganization", { pathParams: { id: orgId }, body: payload, token });
  }

  deleteOrganization(orgId: string, token?: string) {
    return this.execute("deleteOrganization", { pathParams: { id: orgId }, token });
  }

  switchOrganization(orgId: string, token?: string) {
    return this.execute("switchOrganization", { pathParams: { id: orgId }, token });
  }

  getMyProfile(token?: string) {
    return this.execute("getMyProfile", { token });
  }

  updateMyProfile(payload: { name?: string }, token?: string) {
    return this.execute("updateMyProfile", { body: payload, token });
  }

  listUsers(token?: string) {
    return this.execute("listUsers", { token });
  }

  createUser(payload: { email: string; password?: string; name: string; org_id: string; role?: string; permissions: string[] }, token?: string) {
    return this.execute("createUser", { body: payload, token });
  }

  inviteUser(payload: { email: string; name: string; role?: string; permissions?: string[] }, token?: string) {
    return this.execute("inviteUser", { body: payload, token });
  }

  getUser(userId: string, token?: string) {
    return this.execute("getUser", { pathParams: { id: userId }, token });
  }

  blockUser(userId: string, token?: string) {
    return this.execute("blockUser", { pathParams: { id: userId }, token });
  }

  unblockUser(userId: string, token?: string) {
    return this.execute("unblockUser", { pathParams: { id: userId }, token });
  }

  deleteUser(userId: string, token?: string) {
    return this.execute("deleteUser", { pathParams: { id: userId }, token });
  }

  updateUserRole(userId: string, role: string, token?: string) {
    return this.execute("updateUserRole", { pathParams: { id: userId }, body: { role }, token });
  }

  getUserPermissions(userId: string, token?: string) {
    return this.execute("getUserPermissions", { pathParams: { id: userId }, token });
  }

  updateUserPermissions(userId: string, permissions: string[], token?: string) {
    return this.execute("updateUserPermissions", { pathParams: { id: userId }, body: { permissions }, token });
  }

  listApiKeys(token?: string) {
    return this.execute("listApiKeys", { token });
  }

  createApiKey(payload: { name: string; org_id: string; key_type?: string; permissions: string[] }, token?: string) {
    return this.execute("createApiKey", { body: payload, token });
  }

  verifyApiKey(key: string, required_permission?: string) {
    return this.execute("verifyApiKey", { body: { key, required_permission } });
  }

  revokeApiKey(keyId: string, token?: string) {
    return this.execute("revokeApiKey", { pathParams: { id: keyId }, token });
  }

  listPermissions() {
    return this.execute("listPermissions");
  }

  fetchAuditLogs(filters?: { event_type?: string; from?: string; to?: string }, token?: string) {
    return this.execute("fetchAuditLogs", { queryParams: filters, token });
  }

  forgotPassword(email: string) {
    return this.execute("forgotPassword", { body: { email } });
  }

  resetPassword(token: string, new_password?: string) {
    return this.execute("resetPassword", { body: { token, new_password } });
  }

  changePassword(current_password?: string, new_password?: string, token?: string) {
    return this.execute("changePassword", { body: { current_password, new_password }, token });
  }
}

const rawClient = new RawAuthApiClient();
export const authApiClient = withCircuitBreaker(withCache(withRetry(rawClient as any)));
