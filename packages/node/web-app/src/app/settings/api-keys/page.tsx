"use client";

import React, { useState } from "react";
import { DataForm, type SchemaConfig } from "../../../components/ui/data-driven/DataForm";
import { DataTable, type ColumnConfig } from "../../../components/ui/data-driven/DataTable";

export default function ApiKeysPage() {
  const [keys, setKeys] = useState<Array<{
    key_id: string;
    org_id: string;
    key_type: string;
    name: string;
    permissions: string[];
    rawKey?: string;
  }>>([
    {
      key_id: "key_sample1",
      org_id: "org_default",
      key_type: "general",
      name: "Default Ingestion Key",
      permissions: ["traces:write", "metrics:write"],
    },
  ]);

  const [verificationResult, setVerificationResult] = useState<any | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const createKeySchema: SchemaConfig = {
    name: "Generate 3-Tier API Key",
    fields: [
      { key: "name", label: "Key Description Name", kind: "text", required: true },
      { key: "org_id", label: "Target Organization ID", kind: "text", required: true },
      {
        key: "key_type",
        label: "Key Tier / Type",
        kind: "select",
        required: true,
        defaultValue: "general",
        options: [
          { label: "General Ingestion", value: "general" },
          { label: "Testing / Sandbox", value: "testing" },
          { label: "Super Secret Admin", value: "super_secret" },
        ],
      },
      {
        key: "permissions",
        label: "Granted Permissions",
        kind: "checkbox-group",
        options: [
          { label: "Traces Read", value: "traces:read" },
          { label: "Traces Write", value: "traces:write" },
          { label: "Metrics Read", value: "metrics:read" },
          { label: "Metrics Write", value: "metrics:write" },
          { label: "Logs Read", value: "logs:read" },
        ],
      },
    ],
  };

  const verifyKeySchema: SchemaConfig = {
    name: "Verify API Key Entitlement",
    fields: [
      { key: "key", label: "API Key (Raw String)", kind: "text", required: true },
      {
        key: "required_permission",
        label: "Required Permission Check (Optional)",
        kind: "text",
        required: false,
      },
    ],
  };

  const handleCreateKey = async (values: any) => {
    setLoading(true);
    try {
      const rawKey = `ak_${values.key_type || "gen"}_${values.org_id}_${Math.random().toString(36).substring(2, 10)}`;
      const newKey = {
        key_id: `key_${Date.now().toString(36)}`,
        org_id: values.org_id,
        key_type: values.key_type || "general",
        name: values.name,
        permissions: values.permissions || [],
        rawKey,
      };
      setKeys((prev) => [newKey, ...prev]);
      setStatusMessage(`API Key "${values.name}" generated! Raw Key: ${rawKey}`);
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyKey = async (values: { key: string; required_permission?: string }) => {
    setLoading(true);
    try {
      const foundKey = keys.find((k) => k.rawKey === values.key || values.key.includes(k.org_id));
      const hasPerm = !values.required_permission || (foundKey && foundKey.permissions.includes(values.required_permission));
      
      setVerificationResult({
        valid: !!foundKey || values.key.startsWith("ak_"),
        authorized: hasPerm,
        requiredPermission: values.required_permission || "None",
        keyInfo: foundKey || { key_type: "general", permissions: ["traces:write"] },
      });
      setStatusMessage("API key verification completed.");
    } finally {
      setLoading(false);
    }
  };

  const keyColumns: ColumnConfig<typeof keys[0]>[] = [
    { key: "key_id", label: "Key ID" },
    { key: "name", label: "Name" },
    { key: "org_id", label: "Org ID" },
    { key: "key_type", label: "Tier / Type" },
    {
      key: "permissions",
      label: "Permissions",
      render: (r) => (
        <div className="flex flex-wrap gap-1">
          {r.permissions.map((p) => (
            <span key={p} className="px-1.5 py-0.5 text-[10px] rounded bg-slate-800 text-cyan-300 border border-slate-700">
              {p}
            </span>
          ))}
        </div>
      ),
    },
    {
      key: "rawKey",
      label: "Raw Key",
      render: (r) =>
        r.rawKey ? (
          <code className="text-xs text-amber-300 bg-amber-950/50 px-2 py-0.5 rounded border border-amber-800">
            {r.rawKey}
          </code>
        ) : (
          <span className="text-slate-500 text-xs">Hidden</span>
        ),
    },
  ];

  return (
    <div className="min-h-screen bg-slate-950 p-6 md:p-10 text-slate-100 space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
          API Key Management
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          Generate 3-tier API keys bound to specific organization permission tables and verify entitlements.
        </p>
      </div>

      {statusMessage && (
        <div className="rounded-lg border border-cyan-500/30 bg-cyan-950/40 p-4 text-sm text-cyan-200">
          {statusMessage}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <DataForm
          schema={createKeySchema}
          onSubmit={handleCreateKey}
          submitLabel="Generate API Key"
          loading={loading}
        />

        <div className="space-y-4">
          <DataForm
            schema={verifyKeySchema}
            onSubmit={handleVerifyKey}
            submitLabel="Verify Key Entitlement"
            loading={loading}
          />

          {verificationResult && (
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-md space-y-2">
              <h4 className="text-sm font-semibold text-slate-200">Verification Inspection Result</h4>
              <div className="flex items-center space-x-3 text-xs">
                <span className={`px-2 py-0.5 rounded font-medium border ${verificationResult.valid ? "bg-emerald-950 text-emerald-300 border-emerald-800" : "bg-rose-950 text-rose-300 border-rose-800"}`}>
                  Valid: {verificationResult.valid ? "YES" : "NO"}
                </span>
                <span className={`px-2 py-0.5 rounded font-medium border ${verificationResult.authorized ? "bg-cyan-950 text-cyan-300 border-cyan-800" : "bg-amber-950 text-amber-300 border-amber-800"}`}>
                  Authorized: {verificationResult.authorized ? "YES" : "NO"}
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Required Permission Checked: <code className="text-cyan-300">{verificationResult.requiredPermission}</code>
              </p>
            </div>
          )}
        </div>
      </div>

      <DataTable
        title="Active Organization API Keys"
        columns={keyColumns}
        rows={keys}
        searchFields={["name", "key_id", "org_id", "key_type"]}
      />
    </div>
  );
}
