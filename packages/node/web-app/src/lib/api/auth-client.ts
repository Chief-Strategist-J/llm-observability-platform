import { withRetry, withCache, withCircuitBreaker } from "../../core/data-driven/adapter-decorators";
import { executeHttpRequest, type ExecuteParams } from "./executor";
import type {
  AuthResponse,
  Organization,
  UserMember,
  ApiKeyItem,
  AuditLogItem,
  GenericStatusResponse,
} from "./responses";

export * from "./responses";

const AUTH_SERVICE_URL = process.env.NEXT_PUBLIC_AUTH_SERVICE_URL || process.env.AUTH_SERVICE_URL || "http://localhost:3001";

export class RawAuthApiClient {
  private baseUrl: string;

  constructor(baseUrl = AUTH_SERVICE_URL) {
    this.baseUrl = baseUrl;
  }

  execute<T = any>(actionKey: Parameters<typeof executeHttpRequest>[1], params?: ExecuteParams): Promise<T> {
    return executeHttpRequest<T>(this.baseUrl, actionKey, params);
  }

  signUp(payload: { email: string; password?: string; name: string; organization_name: string; role?: string }): Promise<AuthResponse> {
    return this.execute<AuthResponse>("signUp", { body: payload });
  }

  signIn(payload: { email: string; password?: string }): Promise<AuthResponse> {
    return this.execute<AuthResponse>("signIn", { body: payload });
  }

  signOut(token?: string): Promise<GenericStatusResponse> {
    return this.execute<GenericStatusResponse>("signOut", { token });
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

  deleteOrganization(orgId: string, token?: string): Promise<GenericStatusResponse> {
    return this.execute<GenericStatusResponse>("deleteOrganization", { pathParams: { id: orgId }, token });
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

  blockUser(userId: string, token?: string): Promise<GenericStatusResponse> {
    return this.execute<GenericStatusResponse>("blockUser", { pathParams: { id: userId }, token });
  }

  unblockUser(userId: string, token?: string): Promise<GenericStatusResponse> {
    return this.execute<GenericStatusResponse>("unblockUser", { pathParams: { id: userId }, token });
  }

  deleteUser(userId: string, token?: string): Promise<GenericStatusResponse> {
    return this.execute<GenericStatusResponse>("deleteUser", { pathParams: { id: userId }, token });
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

  revokeApiKey(keyId: string, token?: string): Promise<GenericStatusResponse> {
    return this.execute<GenericStatusResponse>("revokeApiKey", { pathParams: { id: keyId }, token });
  }

  listPermissions(): Promise<string[]> {
    return this.execute<string[]>("listPermissions");
  }

  fetchAuditLogs(filters?: { event_type?: string; from?: string; to?: string }, token?: string): Promise<AuditLogItem[]> {
    return this.execute<AuditLogItem[]>("fetchAuditLogs", { queryParams: filters, token });
  }

  forgotPassword(email: string): Promise<GenericStatusResponse> {
    return this.execute<GenericStatusResponse>("forgotPassword", { body: { email } });
  }

  resetPassword(token: string, new_password?: string): Promise<GenericStatusResponse> {
    return this.execute<GenericStatusResponse>("resetPassword", { body: { token, new_password } });
  }

  changePassword(current_password?: string, new_password?: string, token?: string): Promise<GenericStatusResponse> {
    return this.execute<GenericStatusResponse>("changePassword", { body: { current_password, new_password }, token });
  }
}

const rawClient = new RawAuthApiClient();
export const authApiClient = withCircuitBreaker(withCache(withRetry(rawClient as any)));
