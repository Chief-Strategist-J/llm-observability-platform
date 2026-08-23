import { describe, it, expect, beforeEach, vi } from "vitest";
import { RawAuthApiClient } from "./auth-client";
import { AUTH_ENDPOINTS } from "./auth-endpoints";

describe("RawAuthApiClient & AUTH_ENDPOINTS Registry", () => {
  let client: RawAuthApiClient;
  const mockBaseUrl = "http://localhost:3001";

  beforeEach(() => {
    client = new RawAuthApiClient(mockBaseUrl);
    vi.restoreAllMocks();
  });

  it("should contain all 31 endpoints in centralized AUTH_ENDPOINTS registry", () => {
    const keys = Object.keys(AUTH_ENDPOINTS);
    expect(keys.length).toBe(31);
    expect(keys).toEqual([
      "signUp",
      "signIn",
      "signOut",
      "getSession",
      "forgotPassword",
      "resetPassword",
      "changePassword",
      "listOrganizations",
      "createOrganization",
      "getOrganization",
      "updateOrganization",
      "deleteOrganization",
      "switchOrganization",
      "getMyProfile",
      "updateMyProfile",
      "listUsers",
      "createUser",
      "inviteUser",
      "getUser",
      "blockUser",
      "unblockUser",
      "deleteUser",
      "updateUserRole",
      "getUserPermissions",
      "updateUserPermissions",
      "listApiKeys",
      "createApiKey",
      "verifyApiKey",
      "revokeApiKey",
      "listPermissions",
      "fetchAuditLogs",
    ]);
  });

  it("should execute createOrganization request dynamically via endpoint registry", async () => {
    const mockData = { id: "org_123", name: "Test Org", slug: "test-org" };
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => ({ status: "success", message: "Created", data: mockData, error: null }),
    } as any);

    const res = await client.createOrganization("Test Org", "test-org");
    expect(res).toEqual(mockData);
    expect(fetch).toHaveBeenCalledWith(`${mockBaseUrl}/api/v1/auth/organizations`, expect.objectContaining({
      method: "POST",
      body: JSON.stringify({ name: "Test Org", slug: "test-org" }),
    }));
  });

  it("should replace path parameters correctly for deleteOrganization", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => ({ status: "success", message: "Deleted", data: { success: true }, error: null }),
    } as any);

    await client.deleteOrganization("org_456", "token123");
    expect(fetch).toHaveBeenCalledWith(`${mockBaseUrl}/api/v1/auth/organizations/org_456`, expect.objectContaining({
      method: "DELETE",
      headers: expect.objectContaining({ Authorization: "Bearer token123" }),
    }));
  });

  it("should replace path parameters correctly for blockUser", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => ({ status: "success", message: "Blocked", data: { success: true }, error: null }),
    } as any);

    await client.blockUser("usr_789", "token123");
    expect(fetch).toHaveBeenCalledWith(`${mockBaseUrl}/api/v1/auth/users/usr_789/block`, expect.objectContaining({
      method: "POST",
      headers: expect.objectContaining({ Authorization: "Bearer token123" }),
    }));
  });

  it("should throw standardized Error on failed API response", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
      ok: false,
      status: 401,
      json: async () => ({
        status: "error",
        message: "Unauthorized",
        data: null,
        error: { code: "USER_BLOCKED", details: "User account blocked" },
      }),
    } as any);

    await expect(client.signIn({ email: "blocked@user.com", password: "password123" })).rejects.toThrow("User account blocked");
  });
});
