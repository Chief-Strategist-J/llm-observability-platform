import { describe, it, expect, vi, beforeEach } from "vitest";
import { RawAuthApiClient } from "../../../../src/lib/api/auth-client";

describe("Register Organization & Sign Up Unit Test", () => {
  let client: RawAuthApiClient;

  beforeEach(() => {
    client = new RawAuthApiClient("http://localhost:3001");
    vi.restoreAllMocks();
  });

  it("should successfully execute organization registration with specified payload parameters", async () => {
    const mockResponse = {
      user: { id: "usr_jaydeep1", email: "jaydeep@gmail.com", name: "Jaydeep", org_id: "org_scaibu1" },
      organization: { id: "org_scaibu1", name: "Scaibu", slug: "scaibu" },
    };

    vi.spyOn(client, "execute").mockResolvedValueOnce(mockResponse as any);

    const payload = {
      name: "Jaydeep",
      organization_name: "Scaibu",
      email: "jaydeep@gmail.com",
      password: "password12345",
      role: "admin",
    };

    const res = await client.signUp(payload);

    expect(client.execute).toHaveBeenCalledWith("signUp", { body: payload });
    expect(res.organization?.name).toBe("Scaibu");
    expect(res.user?.email).toBe("jaydeep@gmail.com");
    expect(res.user?.name).toBe("Jaydeep");
  });
});
