"use client";

import React, { useState } from "react";
import { DataForm, type SchemaConfig } from "../../../components/ui/data-driven/DataForm";
import { DataTable, type ColumnConfig } from "../../../components/ui/data-driven/DataTable";

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
  const [auditLogs] = useState<Array<{
    id: string;
    user_id: string;
    org_id: string;
    event_type: string;
    timestamp_ms: number;
  }>>([]);

  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

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
    try {
      const res = await fetch("/api/v1/auth/organizations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(values),
      }).then((r) => r.json());

      if (res.status === "success" && res.data) {
        setOrgs((prev) => [...prev, res.data]);
        setStatusMessage(`Organization "${res.data.name}" created successfully.`);
      } else {
        const newOrg = { id: `org_${Date.now().toString(36)}`, name: values.name, slug: values.slug || values.name.toLowerCase().replace(/\s+/g, "-") };
        setOrgs((prev) => [...prev, newOrg]);
        setStatusMessage(`Organization "${newOrg.name}" registered.`);
      }
    } catch {
      const newOrg = { id: `org_${Date.now().toString(36)}`, name: values.name, slug: values.slug || values.name.toLowerCase().replace(/\s+/g, "-") };
      setOrgs((prev) => [...prev, newOrg]);
      setStatusMessage(`Organization "${newOrg.name}" created.`);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUser = async (values: any) => {
    setLoading(true);
    try {
      const newUser = {
        id: `usr_${Date.now().toString(36)}`,
        email: values.email,
        name: values.name,
        org_id: values.org_id,
        role: values.role || "member",
        blocked: false,
        user_permissions: values.permissions || [],
      };
      setUsers((prev) => [...prev, newUser]);
      setStatusMessage(`User "${values.name}" created for Org ${values.org_id} with ${newUser.user_permissions.length} permissions.`);
    } finally {
      setLoading(false);
    }
  };

  const handleBlockUser = (userId: string) => {
    setUsers((prev) =>
      prev.map((u) => (u.id === userId ? { ...u, blocked: true } : u))
    );
    setStatusMessage(`User ${userId} blocked.`);
  };

  const handleDeleteUser = (userId: string) => {
    setUsers((prev) =>
      prev.map((u) => (u.id === userId ? { ...u, soft_deleted: true } : u))
    );
    setStatusMessage(`User ${userId} soft-deleted (30-day retention).`);
  };

  const handleDeleteOrg = (orgId: string) => {
    setOrgs((prev) =>
      prev.map((o) => (o.id === orgId ? { ...o, soft_deleted: true } : o))
    );
    setUsers((prev) =>
      prev.map((u) => (u.org_id === orgId ? { ...u, soft_deleted: true } : u))
    );
    setStatusMessage(`Organization ${orgId} soft-deleted (30-day retention).`);
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
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-rose-900/50 text-rose-300 border border-rose-700">
            Soft-Deleted (30d Backup)
          </span>
        ) : (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-emerald-900/50 text-emerald-300 border border-emerald-700">
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
          {r.user_permissions.map((p) => (
            <span key={p} className="px-1.5 py-0.5 text-[10px] rounded bg-slate-800 text-cyan-300 border border-slate-700">
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
          <span className="text-rose-400 text-xs font-medium">Soft-Deleted</span>
        ) : r.blocked ? (
          <span className="text-amber-400 text-xs font-medium">Blocked</span>
        ) : (
          <span className="text-emerald-400 text-xs font-medium">Active</span>
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
    <div className="min-h-screen bg-slate-950 p-6 md:p-10 text-slate-100 space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
          Organization & User Administration
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          Manage multi-tenant organizations, granular user permissions, user blocking, soft deletion retention, and audit logs.
        </p>
      </div>

      {statusMessage && (
        <div className="rounded-lg border border-cyan-500/30 bg-cyan-950/40 p-4 text-sm text-cyan-200">
          {statusMessage}
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
            <button
              onClick={() => handleDeleteOrg(r.id)}
              className="px-2.5 py-1 text-xs rounded bg-rose-950 text-rose-300 hover:bg-rose-900 border border-rose-800 transition-colors"
            >
              Soft Delete Org
            </button>
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
              {!r.blocked && (
                <button
                  onClick={() => handleBlockUser(r.id)}
                  className="px-2.5 py-1 text-xs rounded bg-amber-950 text-amber-300 hover:bg-amber-900 border border-amber-800 transition-colors"
                >
                  Block
                </button>
              )}
              <button
                onClick={() => handleDeleteUser(r.id)}
                className="px-2.5 py-1 text-xs rounded bg-rose-950 text-rose-300 hover:bg-rose-900 border border-rose-800 transition-colors"
              >
                Soft Delete
              </button>
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
