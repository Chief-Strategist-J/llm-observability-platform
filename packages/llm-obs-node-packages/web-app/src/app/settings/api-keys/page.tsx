"use client";

import React, { useEffect, useState, useCallback, useMemo } from "react";
import { useSelector, useDispatch } from "react-redux";
import { DataForm, type SchemaConfig } from "../../../components/ui/data-driven/DataForm";
import { DataTable, type ColumnConfig } from "../../../components/ui/data-driven/DataTable";
import { Button } from "../../../components/primitives/Button";
import { authApiClient } from "../../../lib/api/auth-client";
import { authActions } from "../../../features/auth/auth.slice";
import { Key, Copy, Check, ShieldAlert, CheckCircle2, AlertCircle, Trash2, ShieldCheck, Sparkles } from "lucide-react";

export default function ApiKeysPage() {
  const dispatch = useDispatch();
  const authUser = useSelector((state: any) => state?.auth?.user);
  const userOrganizations = useSelector((state: any) => state?.auth?.userOrganizations || []);

  const [keys, setKeys] = useState<Array<{
    key_id: string;
    org_id: string;
    key_type: string;
    name: string;
    permissions: string[];
    rawKey?: string;
    revoked?: boolean;
    created_at_ms?: number;
  }>>([]);

  const [newlyCreatedKey, setNewlyCreatedKey] = useState<{ name: string; rawKey: string; key_id: string } | null>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [verificationResult, setVerificationResult] = useState<any | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
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
    dispatch(authActions.fetchOrganizationsSubmitted());
    loadData();
  }, [dispatch, loadData]);

  const orgOptions = useMemo(() => {
    if (userOrganizations.length > 0) {
      return userOrganizations.map((o: any) => ({
        label: `${o.name} (${o.id})`,
        value: o.id,
      }));
    }
    if (authUser?.org_id) {
      return [{
        label: `${authUser.org_name || 'Active Workspace'} (${authUser.org_id})`,
        value: authUser.org_id,
      }];
    }
    return [{ label: "Primary Organization (org_default)", value: "org_default" }];
  }, [userOrganizations, authUser]);

  const activeOrgId = authUser?.org_id || userOrganizations[0]?.id || "org_default";

  const createKeySchema: SchemaConfig = useMemo(() => ({
    name: "Generate 3-Tier API Key",
    fields: [
      { key: "name", label: "Key Description / Service Name", kind: "text", required: true },
      {
        key: "org_id",
        label: "Target Organization",
        kind: "select",
        required: true,
        defaultValue: activeOrgId,
        options: orgOptions,
      },
      {
        key: "key_type",
        label: "Key Tier / Security Type",
        kind: "select",
        required: true,
        defaultValue: "general",
        options: [
          { label: "General Telemetry Ingestion (ak_gen_)", value: "general" },
          { label: "Testing / Sandbox (ak_test_)", value: "testing" },
          { label: "Super Admin Secret (ak_sec_)", value: "super_secret" },
        ],
      },
      {
        key: "permissions",
        label: "Granted Permission Scopes",
        kind: "checkbox-group",
        options: [
          { label: "Traces Read (traces:read)", value: "traces:read" },
          { label: "Traces Write (traces:write)", value: "traces:write" },
          { label: "Metrics Read (metrics:read)", value: "metrics:read" },
          { label: "Metrics Write (metrics:write)", value: "metrics:write" },
          { label: "Logs Read (logs:read)", value: "logs:read" },
        ],
      },
    ],
  }), [orgOptions, activeOrgId]);

  const verifyKeySchema: SchemaConfig = {
    name: "Inspect & Verify API Key Entitlements",
    fields: [
      { key: "key", label: "API Key String", kind: "text", required: true },
      {
        key: "required_permission",
        label: "Required Permission Check (e.g. traces:read)",
        kind: "text",
        required: false,
      },
    ],
  };

  const handleCopyKey = (rawKey: string) => {
    if (typeof navigator !== "undefined" && navigator.clipboard) {
      navigator.clipboard.writeText(rawKey);
      setCopiedKey(rawKey);
      setTimeout(() => setCopiedKey(null), 2500);
    }
  };

  const handleCreateKey = async (values: any) => {
    setLoading(true);
    setStatusMessage(null);
    setErrorMessage(null);

    const targetOrgId = values.org_id || activeOrgId;
    const token = getCookieToken();

    try {
      const res = await authApiClient.createApiKey({
        name: values.name,
        org_id: targetOrgId,
        key_type: values.key_type || "general",
        permissions: values.permissions || [],
      }, token);

      const rawKey = res.rawKey;
      const keyId = res.keyRecord?.key_id || `key_${Date.now().toString(36)}`;

      const createdItem = {
        key_id: keyId,
        org_id: targetOrgId,
        key_type: values.key_type || "general",
        name: values.name,
        permissions: values.permissions || [],
        rawKey,
        revoked: false,
        created_at_ms: Date.now(),
      };

      setKeys((prev) => [createdItem, ...prev]);
      setNewlyCreatedKey({ name: values.name, rawKey, key_id: keyId });
      setStatusMessage(`API Key "${values.name}" generated successfully.`);
    } catch (err: any) {
      const cleanError = err?.message || "Failed to generate API Key. Please verify selected organization details.";
      setErrorMessage(cleanError.replace(/violates foreign key constraint.*/, "Target organization does not exist or has been deleted. Please select an active workspace from the dropdown."));
    } finally {
      setLoading(false);
      loadData();
    }
  };

  const handleVerifyKey = async (values: { key: string; required_permission?: string }) => {
    setLoading(true);
    setStatusMessage(null);
    setErrorMessage(null);

    try {
      const result = await authApiClient.verifyApiKey(values.key, values.required_permission);
      setVerificationResult({
        valid: result.valid,
        authorized: result.authorized,
        requiredPermission: values.required_permission || "None",
        record: result.record,
      });
      setStatusMessage("API key verification check completed.");
    } catch (err: any) {
      setErrorMessage(`Key verification failed: ${err.message}`);
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
      setErrorMessage(`Failed to revoke API key: ${err.message}`);
    }
  };

  const renderTierBadge = (keyType: string) => {
    switch (keyType) {
      case "super_secret":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wide bg-purple-950/80 text-purple-300 border border-purple-700 shadow-sm">
            <Sparkles size={10} />
            Super Secret
          </span>
        );
      case "testing":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wide bg-amber-950/80 text-amber-300 border border-amber-700 shadow-sm">
            Sandbox
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wide bg-cyan-950/80 text-cyan-300 border border-cyan-700 shadow-sm">
            General Ingestion
          </span>
        );
    }
  };

  const keyColumns: ColumnConfig<typeof keys[0]>[] = [
    {
      key: "name",
      label: "Key Name & ID",
      render: (r) => (
        <div>
          <div className="font-bold text-xs text-[hsl(var(--foreground))]">{r.name}</div>
          <div className="text-[10px] font-mono text-[hsl(var(--muted-foreground))]">{r.key_id}</div>
        </div>
      ),
    },
    { key: "org_id", label: "Organization ID" },
    {
      key: "key_type",
      label: "Security Tier",
      render: (r) => renderTierBadge(r.key_type),
    },
    {
      key: "permissions",
      label: "Bound Permissions",
      render: (r) => (
        <div className="flex flex-wrap gap-1">
          {(r.permissions || []).map((p) => (
            <span key={p} className="px-1.5 py-0.5 text-[10px] rounded bg-[hsl(var(--muted)/.4)] text-[hsl(var(--foreground))] border border-[hsl(var(--border))] font-mono">
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
          <span className="inline-flex items-center gap-1 text-[hsl(var(--destructive))] text-xs font-semibold">
            <Trash2 size={12} />
            Revoked
          </span>
        ) : r.rawKey ? (
          <div className="flex items-center gap-2">
            <code className="text-xs text-amber-300 bg-amber-950/60 px-2.5 py-1 rounded border border-amber-800/80 font-mono select-all">
              {r.rawKey}
            </code>
            <button
              onClick={() => handleCopyKey(r.rawKey!)}
              className="p-1 rounded hover:bg-[hsl(var(--muted))] text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] transition-colors"
              title="Copy to Clipboard"
            >
              {copiedKey === r.rawKey ? <Check size={14} className="text-emerald-400" /> : <Copy size={14} />}
            </button>
          </div>
        ) : (
          <span className="inline-flex items-center gap-1 text-emerald-400 text-xs font-semibold">
            <CheckCircle2 size={12} />
            Active
          </span>
        ),
    },
  ];

  return (
    <div className="space-y-6 w-full text-left max-w-7xl mx-auto">
      {/* Header Banner */}
      <div className="flex items-center justify-between border-b border-[hsl(var(--border))] pb-4">
        <div>
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-[var(--radius-lg)] bg-[hsl(var(--primary)/.15)] text-[hsl(var(--primary))]">
              <Key size={22} />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-[hsl(var(--foreground))]">
                API Key Management
              </h1>
              <p className="text-[hsl(var(--muted-foreground))] text-xs mt-0.5">
                Provision 3-tier API tokens bound to specific organization permission tables, verify entitlements, and revoke credentials.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Newly Created Key Prominent Secret Display Card */}
      {newlyCreatedKey && (
        <div className="rounded-[var(--radius-lg)] border-2 border-emerald-500/60 bg-emerald-950/40 p-6 shadow-xl space-y-4 animate-in fade-in duration-300">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm">
              <CheckCircle2 size={18} />
              <span>API Key Successfully Provisioned: {newlyCreatedKey.name}</span>
            </div>
            <button
              onClick={() => setNewlyCreatedKey(null)}
              className="text-xs text-emerald-400/80 hover:text-emerald-300 underline cursor-pointer"
            >
              Dismiss Secret Box
            </button>
          </div>

          <div className="bg-[hsl(var(--background))/0.8] rounded-[var(--radius-md)] border border-emerald-800/80 p-4 space-y-2">
            <label className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider">
              Secret API Key (Copy Now)
            </label>
            <div className="flex items-center justify-between gap-3">
              <code className="text-sm md:text-base font-mono text-emerald-300 tracking-wide break-all select-all font-semibold">
                {newlyCreatedKey.rawKey}
              </code>
              <button
                onClick={() => handleCopyKey(newlyCreatedKey.rawKey)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-[var(--radius-md)] bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold transition-all shadow cursor-pointer shrink-0"
              >
                {copiedKey === newlyCreatedKey.rawKey ? (
                  <>
                    <Check size={14} />
                    <span>Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy size={14} />
                    <span>Copy Key</span>
                  </>
                )}
              </button>
            </div>
          </div>

          <div className="flex items-center gap-2 text-xs text-amber-300/90 font-medium">
            <ShieldAlert size={14} className="shrink-0 text-amber-400" />
            <span>Store this key securely. For security reasons, this raw secret key will not be displayed again after leaving this page.</span>
          </div>
        </div>
      )}

      {/* Toast Feedback Alerts */}
      {statusMessage && !newlyCreatedKey && (
        <div className="rounded-[var(--radius-md)] border border-emerald-800 bg-emerald-950/60 p-4 text-sm text-emerald-300 shadow flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 size={16} />
            <span>{statusMessage}</span>
          </div>
          <button onClick={() => setStatusMessage(null)} className="text-xs text-emerald-400 hover:underline cursor-pointer">Dismiss</button>
        </div>
      )}

      {errorMessage && (
        <div className="rounded-[var(--radius-md)] border border-[hsl(var(--destructive)/.5)] bg-[hsl(var(--destructive)/.15)] p-4 text-sm text-[hsl(var(--destructive))] shadow flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle size={16} />
            <span>{errorMessage}</span>
          </div>
          <button onClick={() => setErrorMessage(null)} className="text-xs text-[hsl(var(--destructive))] hover:underline cursor-pointer">Dismiss</button>
        </div>
      )}

      {/* Forms Grid */}
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
            submitLabel="Verify Key Entitlements"
            loading={loading}
          />

          {verificationResult && (
            <div className="rounded-[var(--radius-xl)] border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-6 shadow-md space-y-3 text-left">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold uppercase tracking-wider text-[hsl(var(--foreground))] flex items-center gap-2">
                  <ShieldCheck size={16} className="text-[hsl(var(--primary))]" />
                  Inspection Result
                </h4>
                <button
                  onClick={() => setVerificationResult(null)}
                  className="text-[10px] text-[hsl(var(--muted-foreground))] hover:underline"
                >
                  Clear Result
                </button>
              </div>

              <div className="flex items-center space-x-3 text-xs">
                <span className={`px-2.5 py-1 rounded-full font-bold border ${verificationResult.valid ? "bg-emerald-950/80 text-emerald-300 border-emerald-700" : "bg-[hsl(var(--destructive)/.2)] text-[hsl(var(--destructive))] border border-[hsl(var(--destructive)/.4)]"}`}>
                  Valid Key: {verificationResult.valid ? "YES" : "NO"}
                </span>
                <span className={`px-2.5 py-1 rounded-full font-bold border ${verificationResult.authorized ? "bg-cyan-950/80 text-cyan-300 border-cyan-700" : "bg-amber-950/80 text-amber-300 border-amber-700"}`}>
                  Authorized: {verificationResult.authorized ? "YES" : "NO"}
                </span>
              </div>

              <p className="text-xs text-[hsl(var(--muted-foreground))]">
                Required Permission Checked: <code className="text-[hsl(var(--primary))] font-mono font-bold">{verificationResult.requiredPermission}</code>
              </p>

              {verificationResult.record && (
                <div className="pt-2 border-t border-[hsl(var(--border))] text-[11px] space-y-1 text-[hsl(var(--muted-foreground))] font-mono">
                  <div>Key ID: {verificationResult.record.key_id}</div>
                  <div>Org ID: {verificationResult.record.org_id}</div>
                  <div>Tier: {verificationResult.record.key_type}</div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Directory Table */}
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
