import { propagation, context } from "@opentelemetry/api";
import { withRetry, withCache, withCircuitBreaker } from "../../core/data-driven/adapter-decorators";
import { AUTH_ENDPOINTS } from "./auth-endpoints";

const AUTH_SERVICE_URL = process.env.NEXT_PUBLIC_AUTH_SERVICE_URL || process.env.AUTH_SERVICE_URL || "http://localhost:3001";

export interface AuthUser {
  id: string;
  email: string;
  name: string;
  org_id: string;
  org_name?: string;
  role?: string;
  permissions?: string[];
}

export interface AuthResponse {
  user?: AuthUser;
  token?: string;
  status?: string;
  message?: string;
  payload?: any;
}

export interface Organization {
  id: string;
  name: string;
  slug?: string;
  role?: string;
  created_at?: string;
}

export interface UserMember {
  id: string;
  name: string;
  email: string;
  org_id: string;
  role: 'owner' | 'admin' | 'member' | 'viewer';
  blocked: boolean;
  permissions?: string[];
}

export interface ApiKeyItem {
  id: string;
  name: string;
  key_type?: string;
  org_id: string;
  permissions?: string[];
  created_at?: string;
}

export interface AuditLogItem {
  id: string;
  event_type: string;
  actor_id?: string;
  details?: Record<string, unknown>;
  created_at: string;
}

export class RawAuthApiClient {
  private baseUrl: string;

  constructor(baseUrl = AUTH_SERVICE_URL) {
    this.baseUrl = baseUrl;
  }

  async execute<T = any>(
    actionKey: keyof typeof AUTH_ENDPOINTS,
    params?: { body?: any; pathParams?: Record<string, string>; token?: string; queryParams?: Record<string, string> }
  ): Promise<T> {
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

  signUp(payload: { email: string; password?: string; name: string; organization_name: string; role?: string }): Promise<AuthResponse> {
    return this.execute<AuthResponse>("signUp", { body: payload });
  }

  signIn(payload: { email: string; password?: string }): Promise<AuthResponse> {
    return this.execute<AuthResponse>("signIn", { body: payload });
  }

  signOut(token?: string): Promise<{ success: boolean }> {
    return this.execute<{ success: boolean }>("signOut", { token });
  }

  getSession(token: string): Promise<AuthResponse> {
    return this.execute<AuthResponse>("getSession", { token });
  }

  listOrganizations(token?: string): Promise<Organization[]> {
    return this.execute<Organization[]>("listOrganizations", { token });
  }

  createOrganization(name: string, slug?: string, token?: string): Promise<Organization> {
    return this.execute<Organization>("createOrganization", { body: { name, slug }, token });
  }

  getOrganization(orgId: string, token?: string): Promise<Organization> {
    return this.execute<Organization>("getOrganization", { pathParams: { id: orgId }, token });
  }

  updateOrganization(orgId: string, payload: { name?: string; slug?: string }, token?: string): Promise<Organization> {
    return this.execute<Organization>("updateOrganization", { pathParams: { id: orgId }, body: payload, token });
  }

  deleteOrganization(orgId: string, token?: string): Promise<{ success: boolean }> {
    return this.execute<{ success: boolean }>("deleteOrganization", { pathParams: { id: orgId }, token });
  }

  switchOrganization(orgId: string, token?: string): Promise<AuthResponse> {
    return this.execute<AuthResponse>("switchOrganization", { pathParams: { id: orgId }, token });
  }

  getMyProfile(token?: string): Promise<UserMember> {
    return this.execute<UserMember>("getMyProfile", { token });
  }

  updateMyProfile(payload: { name?: string }, token?: string): Promise<UserMember> {
    return this.execute<UserMember>("updateMyProfile", { body: payload, token });
  }

  listUsers(token?: string): Promise<UserMember[]> {
    return this.execute<UserMember[]>("listUsers", { token });
  }

  createUser(payload: { email: string; password?: string; name: string; org_id: string; role?: string; permissions: string[] }, token?: string): Promise<UserMember> {
    return this.execute<UserMember>("createUser", { body: payload, token });
  }

  inviteUser(payload: { email: string; name: string; role?: string; permissions?: string[] }, token?: string): Promise<UserMember> {
    return this.execute<UserMember>("inviteUser", { body: payload, token });
  }

  getUser(userId: string, token?: string): Promise<UserMember> {
    return this.execute<UserMember>("getUser", { pathParams: { id: userId }, token });
  }

  blockUser(userId: string, token?: string): Promise<{ success: boolean }> {
    return this.execute<{ success: boolean }>("blockUser", { pathParams: { id: userId }, token });
  }

  unblockUser(userId: string, token?: string): Promise<{ success: boolean }> {
    return this.execute<{ success: boolean }>("unblockUser", { pathParams: { id: userId }, token });
  }

  deleteUser(userId: string, token?: string): Promise<{ success: boolean }> {
    return this.execute<{ success: boolean }>("deleteUser", { pathParams: { id: userId }, token });
  }

  updateUserRole(userId: string, role: string, token?: string): Promise<UserMember> {
    return this.execute<UserMember>("updateUserRole", { pathParams: { id: userId }, body: { role }, token });
  }

  getUserPermissions(userId: string, token?: string): Promise<string[]> {
    return this.execute<string[]>("getUserPermissions", { pathParams: { id: userId }, token });
  }

  updateUserPermissions(userId: string, permissions: string[], token?: string): Promise<string[]> {
    return this.execute<string[]>("updateUserPermissions", { pathParams: { id: userId }, body: { permissions }, token });
  }

  listApiKeys(token?: string): Promise<ApiKeyItem[]> {
    return this.execute<ApiKeyItem[]>("listApiKeys", { token });
  }

  createApiKey(payload: { name: string; org_id: string; key_type?: string; permissions: string[] }, token?: string): Promise<ApiKeyItem> {
    return this.execute<ApiKeyItem>("createApiKey", { body: payload, token });
  }

  verifyApiKey(key: string, required_permission?: string): Promise<{ valid: boolean; key?: ApiKeyItem }> {
    return this.execute<{ valid: boolean; key?: ApiKeyItem }>("verifyApiKey", { body: { key, required_permission } });
  }

  revokeApiKey(keyId: string, token?: string): Promise<{ success: boolean }> {
    return this.execute<{ success: boolean }>("revokeApiKey", { pathParams: { id: keyId }, token });
  }

  listPermissions(): Promise<string[]> {
    return this.execute<string[]>("listPermissions");
  }

  fetchAuditLogs(filters?: { event_type?: string; from?: string; to?: string }, token?: string): Promise<AuditLogItem[]> {
    return this.execute<AuditLogItem[]>("fetchAuditLogs", { queryParams: filters, token });
  }

  forgotPassword(email: string): Promise<{ success: boolean; message?: string }> {
    return this.execute<{ success: boolean; message?: string }>("forgotPassword", { body: { email } });
  }

  resetPassword(token: string, new_password?: string): Promise<{ success: boolean; message?: string }> {
    return this.execute<{ success: boolean; message?: string }>("resetPassword", { body: { token, new_password } });
  }

  changePassword(current_password?: string, new_password?: string, token?: string): Promise<{ success: boolean; message?: string }> {
    return this.execute<{ success: boolean; message?: string }>("changePassword", { body: { current_password, new_password }, token });
  }
}

const rawClient = new RawAuthApiClient();
export const authApiClient = withCircuitBreaker(withCache(withRetry(rawClient as any)));
