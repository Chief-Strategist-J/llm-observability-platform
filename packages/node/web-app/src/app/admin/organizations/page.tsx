"use client";

import React, { useEffect, useState, useCallback } from "react";
import { DataForm, type SchemaConfig } from "../../../components/ui/data-driven/DataForm";
import { DataTable, type ColumnConfig } from "../../../components/ui/data-driven/DataTable";
import { Button } from "../../../components/primitives/Button";
import { authApiClient } from "../../../lib/api/auth-client";

export default function OrganizationsAdminPage() {
  const [orgs, setOrgs] = useState<Array<{ id: string; name: string; slug: string; soft_deleted?: boolean }>>([]);
  const [users, setUsers] = useState<Array<{
    id: string;
    email: string;
    name: string;
    org_id: string;
    role: string;
    blocked: boolean;
    user_permissions: string[];
    soft_deleted?: boolean;
  }>>([]);
  const [auditLogs, setAuditLogs] = useState<Array<{
    id: string;
    user_id: string;
    org_id: string;
    event_type: string;
    timestamp_ms: number;
  }>>([]);

  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function getCookieToken(): string | undefined {
    if (typeof document === "undefined") return undefined;
    const match = document.cookie.match(new RegExp("(?:^|; )authjs\\.session-token=([^;]*)"));
    return match && match[1] ? decodeURIComponent(match[1]) : undefined;
  }

  const loadData = useCallback(async () => {
    const token = getCookieToken();
    try {
      const fetchedOrgs = await authApiClient.listOrganizations(token);
      if (Array.isArray(fetchedOrgs)) setOrgs(fetchedOrgs);
    } catch {}

    try {
      const fetchedUsers = await authApiClient.listUsers(token);
      if (Array.isArray(fetchedUsers)) setUsers(fetchedUsers);
    } catch {}

    try {
      const fetchedLogs = await authApiClient.fetchAuditLogs(undefined, token);
      if (Array.isArray(fetchedLogs)) setAuditLogs(fetchedLogs);
    } catch {}
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const createOrgSchema: SchemaConfig = {
    name: "Create Standalone Organization",
    fields: [
      { key: "name", label: "Organization Name", kind: "text", required: true },
      { key: "slug", label: "Slug (Optional)", kind: "text", required: false },
    ],
  };

  const createUserSchema: SchemaConfig = {
    name: "Create User in Target Organization",
    fields: [
      { key: "email", label: "Email Address", kind: "email", required: true },
      { key: "name", label: "Full Name", kind: "text", required: true },
      { key: "org_id", label: "Target Organization ID", kind: "text", required: true },
      {
        key: "role",
        label: "Organization Role",
        kind: "select",
        required: true,
        defaultValue: "member",
        options: [
          { label: "Admin", value: "admin" },
          { label: "Member", value: "member" },
          { label: "Viewer", value: "viewer" },
        ],
      },
      {
        key: "permissions",
        label: "Granular Permissions",
        kind: "checkbox-group",
        options: [
          { label: "Traces Read", value: "traces:read" },
          { label: "Traces Write", value: "traces:write" },
          { label: "Metrics Read", value: "metrics:read" },
          { label: "Metrics Write", value: "metrics:write" },
          { label: "Logs Read", value: "logs:read" },
          { label: "Admin All", value: "admin:all" },
        ],
      },
    ],
  };

  const handleCreateOrg = async (values: { name: string; slug?: string }) => {
    setLoading(true);
    const token = getCookieToken();
    try {
      const created = await authApiClient.createOrganization(values.name, values.slug, token);
      setOrgs((prev) => [...prev, created]);
      setStatusMessage(`Organization "${created.name}" created successfully.`);
    } catch (err: any) {
      setStatusMessage(`Failed to create organization: ${err.message}`);
    } finally {
      setLoading(false);
      loadData();
    }
  };

  const handleCreateUser = async (values: any) => {
    setLoading(true);
    const token = getCookieToken();
    try {
      const newUser = await authApiClient.createUser({
        email: values.email,
        name: values.name,
        org_id: values.org_id,
        role: values.role || "member",
        permissions: values.permissions || [],
      }, token);
      setUsers((prev) => [...prev, newUser]);
      setStatusMessage(`User "${values.name}" created for Org ${values.org_id}.`);
    } catch (err: any) {
      setStatusMessage(`Failed to create user: ${err.message}`);
    } finally {
      setLoading(false);
      loadData();
    }
  };

  const handleBlockUser = async (userId: string) => {
    const token = getCookieToken();
    try {
      await authApiClient.blockUser(userId, token);
      setUsers((prev) => prev.map((u) => (u.id === userId ? { ...u, blocked: true } : u)));
      setStatusMessage(`User ${userId} blocked.`);
    } catch (err: any) {
      setStatusMessage(`Failed to block user: ${err.message}`);
    }
  };

  const handleUnblockUser = async (userId: string) => {
    const token = getCookieToken();
    try {
      await authApiClient.unblockUser(userId, token);
      setUsers((prev) => prev.map((u) => (u.id === userId ? { ...u, blocked: false } : u)));
      setStatusMessage(`User ${userId} unblocked.`);
    } catch (err: any) {
      setStatusMessage(`Failed to unblock user: ${err.message}`);
    }
  };

  const handleDeleteUser = async (userId: string) => {
    const token = getCookieToken();
    try {
      await authApiClient.deleteUser(userId, token);
      setUsers((prev) => prev.map((u) => (u.id === userId ? { ...u, soft_deleted: true } : u)));
      setStatusMessage(`User ${userId} soft-deleted (30-day backup retention).`);
    } catch (err: any) {
      setStatusMessage(`Failed to delete user: ${err.message}`);
    }
  };

  const handleDeleteOrg = async (orgId: string) => {
    const token = getCookieToken();
    try {
      await authApiClient.deleteOrganization(orgId, token);
      setOrgs((prev) => prev.map((o) => (o.id === orgId ? { ...o, soft_deleted: true } : o)));
      setUsers((prev) => prev.map((u) => (u.org_id === orgId ? { ...u, soft_deleted: true } : u)));
      setStatusMessage(`Organization ${orgId} soft-deleted (30-day backup retention).`);
    } catch (err: any) {
      setStatusMessage(`Failed to delete organization: ${err.message}`);
    }
  };

  const orgColumns: ColumnConfig<typeof orgs[0]>[] = [
    { key: "id", label: "Org ID" },
    { key: "name", label: "Name" },
    { key: "slug", label: "Slug" },
    {
      key: "soft_deleted",
      label: "Retention Status",
      render: (r) =>
        r.soft_deleted ? (
          <span className="inline-flex items-center px-2 py-0.5 rounded-[var(--radius-sm)] text-xs font-semibold bg-[hsl(var(--destructive)/.2)] text-[hsl(var(--destructive))] border border-[hsl(var(--destructive)/.4)]">
            Soft-Deleted (30d Backup)
          </span>
        ) : (
          <span className="inline-flex items-center px-2 py-0.5 rounded-[var(--radius-sm)] text-xs font-semibold bg-emerald-950/60 text-emerald-400 border border-emerald-800">
            Active
          </span>
        ),
    },
  ];

  const userColumns: ColumnConfig<typeof users[0]>[] = [
    { key: "id", label: "User ID" },
    { key: "name", label: "Name" },
    { key: "email", label: "Email" },
    { key: "org_id", label: "Org ID" },
    { key: "role", label: "Role" },
    {
      key: "user_permissions",
      label: "Permissions",
      render: (r) => (
        <div className="flex flex-wrap gap-1">
          {(r.user_permissions || []).map((p) => (
            <span key={p} className="px-1.5 py-0.5 text-[10px] rounded bg-[hsl(var(--muted)/.3)] text-[hsl(var(--foreground))] border border-[hsl(var(--border))] font-mono">
              {p}
            </span>
          ))}
        </div>
      ),
    },
    {
      key: "blocked",
      label: "Status",
      render: (r) =>
        r.soft_deleted ? (
          <span className="text-[hsl(var(--destructive))] text-xs font-semibold">Soft-Deleted</span>
        ) : r.blocked ? (
          <span className="text-amber-400 text-xs font-semibold">Blocked</span>
        ) : (
          <span className="text-emerald-400 text-xs font-semibold">Active</span>
        ),
    },
  ];

  const auditColumns: ColumnConfig<typeof auditLogs[0]>[] = [
    { key: "id", label: "Audit ID" },
    { key: "user_id", label: "User ID" },
    { key: "org_id", label: "Org ID" },
    { key: "event_type", label: "Event Type" },
    {
      key: "timestamp_ms",
      label: "Timestamp",
      render: (r) => new Date(r.timestamp_ms).toLocaleString(),
    },
  ];

  return (
    <div className="space-y-6 w-full text-left max-w-7xl mx-auto">
      <div className="border-b border-[hsl(var(--border))] pb-4">
        <h1 className="text-2xl font-bold tracking-tight text-[hsl(var(--foreground))]">
          Organization & User Administration
        </h1>
        <p className="text-[hsl(var(--muted-foreground))] text-xs mt-0.5">
          Manage multi-tenant organizations, granular user permissions, user blocking, soft deletion retention, and audit logs.
        </p>
      </div>

      {statusMessage && (
        <div className="rounded-[var(--radius-md)] border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-4 text-sm text-[hsl(var(--foreground))] shadow flex items-center justify-between">
          <span>{statusMessage}</span>
          <button onClick={() => setStatusMessage(null)} className="text-xs text-[hsl(var(--muted-foreground))] hover:underline">Dismiss</button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <DataForm
          schema={createOrgSchema}
          onSubmit={handleCreateOrg}
          submitLabel="Create Standalone Organization"
          loading={loading}
        />

        <DataForm
          schema={createUserSchema}
          onSubmit={handleCreateUser}
          submitLabel="Create User in Target Organization"
          loading={loading}
        />
      </div>

      <DataTable
        title="Organizations Directory"
        columns={orgColumns}
        rows={orgs}
        searchFields={["name", "id", "slug"]}
        actions={(r) => (
          !r.soft_deleted && (
            <Button
              variant="destructive"
              size="sm"
              onClick={() => handleDeleteOrg(r.id)}
            >
              Soft Delete Org
            </Button>
          )
        )}
      />

      <DataTable
        title="Users Directory & Access Controls"
        columns={userColumns}
        rows={users}
        searchFields={["name", "email", "id", "org_id"]}
        actions={(r) => (
          !r.soft_deleted && (
            <div className="flex items-center justify-end space-x-2">
              {!r.blocked ? (
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => handleBlockUser(r.id)}
                >
                  Block
                </Button>
              ) : (
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => handleUnblockUser(r.id)}
                >
                  Unblock
                </Button>
              )}
              <Button
                variant="destructive"
                size="sm"
                onClick={() => handleDeleteUser(r.id)}
              >
                Soft Delete
              </Button>
            </div>
          )
        )}
      />

      <DataTable
        title="Audit Logs"
        columns={auditColumns}
        rows={auditLogs}
        searchFields={["event_type", "user_id", "org_id"]}
      />
    </div>
  );
}
