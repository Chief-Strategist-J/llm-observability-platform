import { describe, it, expect, beforeEach, vi } from "vitest";
import { RawAuthApiClient } from "../../../src/lib/api/auth-client";

describe("Auth Lifecycle & Organization Management Integration Suite", () => {
  let client: RawAuthApiClient;
  const mockBaseUrl = "http://localhost:3001";

  beforeEach(() => {
    client = new RawAuthApiClient(mockBaseUrl);
    vi.restoreAllMocks();
  });

  it("should complete user registration, authentication, and session retrieval pipeline", async () => {
    // 1. Sign Up
    const signUpResponse = {
      user: { id: "usr_int_01", email: "lead@observability.io", name: "Lead Engineer", org_id: "org_int_01" },
      token: "mock-jwt-token-123",
      status: "success",
    };
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => ({ status: "success", data: signUpResponse }),
    } as any);

    const signUpRes = await client.signUp({
      email: "lead@observability.io",
      name: "Lead Engineer",
      organization_name: "Observability Platform Corp",
    });

    expect(signUpRes.token).toBe("mock-jwt-token-123");
    expect(signUpRes.user?.org_id).toBe("org_int_01");

    // 2. Fetch Session
    const sessionResponse = {
      user: { id: "usr_int_01", email: "lead@observability.io", name: "Lead Engineer", org_id: "org_int_01", role: "owner" },
      status: "active",
    };
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => ({ status: "success", data: sessionResponse }),
    } as any);

    const sessionRes = await client.getSession("mock-jwt-token-123");
    expect(sessionRes.user?.role).toBe("owner");
  });

  it("should integrate user invitation, role management, and audit log generation", async () => {
    // 1. Invite User
    const invitedUser = {
      id: "usr_invited_99",
      email: "dev@company.com",
      name: "Dev Engineer",
      org_id: "org_int_01",
      role: "member" as const,
      blocked: false,
    };
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => ({ status: "success", data: invitedUser }),
    } as any);

    const inviteRes = await client.inviteUser({
      email: "dev@company.com",
      name: "Dev Engineer",
      role: "member",
    }, "token-123");

    expect(inviteRes.email).toBe("dev@company.com");
    expect(inviteRes.role).toBe("member");

    // 2. Audit Logs Fetch
    const auditLogs = [
      { id: "log-1", event_type: "user.invited", actor_id: "usr_int_01", created_at: "2026-08-29T09:00:00Z" },
    ];
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => ({ status: "success", data: auditLogs }),
    } as any);

    const logs = await client.fetchAuditLogs({ event_type: "user.invited" }, "token-123");
    expect(logs.length).toBe(1);
    expect(logs[0]?.event_type).toBe("user.invited");
  });
});
