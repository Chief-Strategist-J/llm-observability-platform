export interface EndpointMeta {
  path: string;
  method: "GET" | "POST" | "PATCH" | "DELETE";
  requiresAuth?: boolean;
}

export const AUTH_ENDPOINTS: Record<string, EndpointMeta> = {
  signUp: { path: "/api/v1/auth/sign-up", method: "POST" },
  signIn: { path: "/api/v1/auth/sign-in", method: "POST" },
  signOut: { path: "/api/v1/auth/sign-out", method: "POST", requiresAuth: true },
  getSession: { path: "/api/v1/auth/session", method: "GET", requiresAuth: true },
  forgotPassword: { path: "/api/v1/auth/forgot-password", method: "POST" },
  resetPassword: { path: "/api/v1/auth/reset-password", method: "POST" },
  changePassword: { path: "/api/v1/auth/change-password", method: "POST", requiresAuth: true },
  listOrganizations: { path: "/api/v1/auth/organizations", method: "GET", requiresAuth: true },
  createOrganization: { path: "/api/v1/auth/organizations", method: "POST", requiresAuth: true },
  getOrganization: { path: "/api/v1/auth/organizations/:id", method: "GET", requiresAuth: true },
  updateOrganization: { path: "/api/v1/auth/organizations/:id", method: "PATCH", requiresAuth: true },
  deleteOrganization: { path: "/api/v1/auth/organizations/:id", method: "DELETE", requiresAuth: true },
  switchOrganization: { path: "/api/v1/auth/organizations/:id/switch", method: "POST", requiresAuth: true },
  getMyProfile: { path: "/api/v1/auth/users/me", method: "GET", requiresAuth: true },
  updateMyProfile: { path: "/api/v1/auth/users/me", method: "PATCH", requiresAuth: true },
  listUsers: { path: "/api/v1/auth/users", method: "GET", requiresAuth: true },
  createUser: { path: "/api/v1/auth/users", method: "POST", requiresAuth: true },
  inviteUser: { path: "/api/v1/auth/users/invite", method: "POST", requiresAuth: true },
  getUser: { path: "/api/v1/auth/users/:id", method: "GET", requiresAuth: true },
  blockUser: { path: "/api/v1/auth/users/:id/block", method: "POST", requiresAuth: true },
  unblockUser: { path: "/api/v1/auth/users/:id/unblock", method: "DELETE", requiresAuth: true },
  deleteUser: { path: "/api/v1/auth/users/:id", method: "DELETE", requiresAuth: true },
  updateUserRole: { path: "/api/v1/auth/users/:id/role", method: "PATCH", requiresAuth: true },
  getUserPermissions: { path: "/api/v1/auth/users/:id/permissions", method: "GET", requiresAuth: true },
  updateUserPermissions: { path: "/api/v1/auth/users/:id/permissions", method: "PATCH", requiresAuth: true },
  listApiKeys: { path: "/api/v1/auth/api-keys", method: "GET", requiresAuth: true },
  createApiKey: { path: "/api/v1/auth/api-keys", method: "POST", requiresAuth: true },
  verifyApiKey: { path: "/api/v1/auth/api-keys/verify", method: "POST" },
  revokeApiKey: { path: "/api/v1/auth/api-keys/:id/revoke", method: "POST", requiresAuth: true },
  listPermissions: { path: "/api/v1/auth/permissions", method: "GET" },
  fetchAuditLogs: { path: "/api/v1/auth/audit-logs", method: "GET", requiresAuth: true },
};

export type ApiEndpointKey = keyof typeof AUTH_ENDPOINTS;

