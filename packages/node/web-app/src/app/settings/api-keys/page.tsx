"use client";

import React, { useEffect, useState, useCallback } from "react";
import { DataForm, type SchemaConfig } from "../../../components/ui/data-driven/DataForm";
import { DataTable, type ColumnConfig } from "../../../components/ui/data-driven/DataTable";
import { Button } from "../../../components/primitives/Button";
import { authApiClient } from "../../../lib/auth-client";

export default function ApiKeysPage() {
  const [keys, setKeys] = useState<Array<{
    key_id: string;
    org_id: string;
    key_type: string;
    name: string;
    permissions: string[];
    rawKey?: string;
    revoked?: boolean;
  }>>([]);

  const [verificationResult, setVerificationResult] = useState<any | null>(null);
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
      const fetchedKeys = await authApiClient.listApiKeys(token);
      if (Array.isArray(fetchedKeys)) setKeys(fetchedKeys);
    } catch {}
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

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
    const token = getCookieToken();
    try {
      const res = await authApiClient.createApiKey({
        name: values.name,
        org_id: values.org_id,
        key_type: values.key_type || "general",
        permissions: values.permissions || [],
      }, token);

      const createdItem = {
        key_id: res.keyRecord?.key_id || `key_${Date.now().toString(36)}`,
        org_id: values.org_id,
        key_type: values.key_type || "general",
        name: values.name,
        permissions: values.permissions || [],
        rawKey: res.rawKey,
        revoked: false,
      };

      setKeys((prev) => [createdItem, ...prev]);
      setStatusMessage(`API Key "${values.name}" generated! Raw Key: ${res.rawKey}`);
    } catch (err: any) {
      setStatusMessage(`Failed to generate API Key: ${err.message}`);
    } finally {
      setLoading(false);
      loadData();
    }
  };

  const handleVerifyKey = async (values: { key: string; required_permission?: string }) => {
    setLoading(true);
    try {
      const result = await authApiClient.verifyApiKey(values.key, values.required_permission);
      setVerificationResult({
        valid: result.valid,
        authorized: result.authorized,
        requiredPermission: values.required_permission || "None",
        record: result.record,
      });
      setStatusMessage("API key verification completed.");
    } catch (err: any) {
      setStatusMessage(`Key verification failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleRevokeKey = async (keyId: string) => {
    const token = getCookieToken();
    try {
      await authApiClient.revokeApiKey(keyId, token);
      setKeys((prev) => prev.map((k) => (k.key_id === keyId ? { ...k, revoked: true } : k)));
      setStatusMessage(`API key ${keyId} revoked.`);
    } catch (err: any) {
      setStatusMessage(`Failed to revoke API key: ${err.message}`);
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
          {(r.permissions || []).map((p) => (
            <span key={p} className="px-1.5 py-0.5 text-[10px] rounded bg-[hsl(var(--muted)/.3)] text-[hsl(var(--foreground))] border border-[hsl(var(--border))] font-mono">
              {p}
            </span>
          ))}
        </div>
      ),
    },
    {
      key: "rawKey",
      label: "Raw Key / Status",
      render: (r) =>
        r.revoked ? (
          <span className="text-[hsl(var(--destructive))] text-xs font-semibold">Revoked</span>
        ) : r.rawKey ? (
          <code className="text-xs text-amber-400 bg-amber-950/40 px-2 py-0.5 rounded border border-amber-800 font-mono">
            {r.rawKey}
          </code>
        ) : (
          <span className="text-emerald-400 text-xs font-semibold">Active</span>
        ),
    },
  ];

  return (
    <div className="min-h-screen bg-[hsl(var(--background))] p-6 md:p-10 text-[hsl(var(--foreground))] space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-[hsl(var(--foreground))]">
          API Key Management
        </h1>
        <p className="text-[hsl(var(--muted-foreground))] text-sm mt-1">
          Generate 3-tier API keys bound to specific organization permission tables, verify entitlements, and revoke access.
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
            <div className="rounded-[var(--radius-xl)] border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-6 shadow-md space-y-2">
              <h4 className="text-sm font-semibold text-[hsl(var(--foreground))]">Verification Inspection Result</h4>
              <div className="flex items-center space-x-3 text-xs">
                <span className={`px-2 py-0.5 rounded font-semibold border ${verificationResult.valid ? "bg-emerald-950/60 text-emerald-300 border-emerald-800" : "bg-[hsl(var(--destructive)/.2)] text-[hsl(var(--destructive))] border border-[hsl(var(--destructive)/.4)]"}`}>
                  Valid: {verificationResult.valid ? "YES" : "NO"}
                </span>
                <span className={`px-2 py-0.5 rounded font-semibold border ${verificationResult.authorized ? "bg-cyan-950/60 text-cyan-300 border-cyan-800" : "bg-amber-950/60 text-amber-300 border-amber-800"}`}>
                  Authorized: {verificationResult.authorized ? "YES" : "NO"}
                </span>
              </div>
              <p className="text-xs text-[hsl(var(--muted-foreground))]">
                Required Permission Checked: <code className="text-[hsl(var(--primary))] font-mono">{verificationResult.requiredPermission}</code>
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
        actions={(r) => (
          !r.revoked && (
            <Button
              variant="destructive"
              size="sm"
              onClick={() => handleRevokeKey(r.key_id)}
            >
              Revoke Key
            </Button>
          )
        )}
      />
    </div>
  );
}
