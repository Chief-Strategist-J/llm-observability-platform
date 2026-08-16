'use client';

import React, { useState } from 'react';
import { useSelector } from 'react-redux';
import { Building2, ShieldCheck, Trash2 } from 'lucide-react';
import { authApiClient } from '../../../lib/auth-client';
import { Button } from '../../../components/primitives/Button';

interface OrgSettingsFormProps {
  readonly orgName?: string;
  readonly orgSlug?: string;
  readonly plan?: string;
  readonly complianceMode?: string;
  readonly onSave?: (data: { name: string; slug: string }) => void;
  readonly onDelete?: () => void;
}

function getCookieToken(): string | undefined {
  if (typeof document === 'undefined') return undefined;
  const match = document.cookie.match(new RegExp('(?:^|; )authjs\\.session-token=([^;]*)'));
  return match && match[1] ? decodeURIComponent(match[1]) : undefined;
}

export function OrgSettingsForm({
  orgName = 'Scaibu Corp',
  orgSlug = 'scaibu-corp',
  plan = 'ENTERPRISE',
  complianceMode = 'standard',
  onSave,
  onDelete,
}: OrgSettingsFormProps) {
  const authUser = useSelector((state: any) => state?.auth?.user);
  const [name, setName] = useState(orgName);
  const [slug, setSlug] = useState(orgSlug);
  const [status, setStatus] = useState<string | null>(null);

  const defaultSaveHandler = async (data: { name: string; slug: string }) => {
    const token = getCookieToken();
    const orgId = authUser?.org_id;
    if (!orgId) {
      setStatus('No active organization ID found');
      return;
    }
    try {
      await authApiClient.updateOrganization(orgId, data, token);
      setStatus('Organization details updated successfully.');
    } catch (err: any) {
      setStatus(`Failed to update organization: ${err.message}`);
    }
  };

  const defaultDeleteHandler = async () => {
    const token = getCookieToken();
    const orgId = authUser?.org_id;
    if (!orgId) return;
    try {
      await authApiClient.deleteOrganization(orgId, token);
      setStatus('Organization soft-deleted (30-day backup retention active).');
    } catch (err: any) {
      setStatus(`Failed to delete organization: ${err.message}`);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {status && (
        <div className="rounded-[var(--radius-md)] border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-3 text-xs text-[hsl(var(--foreground))] shadow">
          {status}
        </div>
      )}

      <div className="rounded-[var(--radius-lg)] border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-6 space-y-6">
        <div className="flex items-center justify-between border-b border-[hsl(var(--border))] pb-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-[var(--radius-md)] bg-[hsl(var(--primary)/.1)] text-[hsl(var(--primary))]">
              <Building2 size={20} />
            </div>
            <div>
              <h2 className="text-base font-bold text-[hsl(var(--foreground))]">{name}</h2>
              <p className="text-xs text-[hsl(var(--muted-foreground))]">Workspace ID: {slug}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="rounded-full bg-[hsl(var(--primary)/.15)] px-2.5 py-1 text-xs font-semibold text-[hsl(var(--primary))]">
              {plan}
            </span>
            <span className="flex items-center gap-1 rounded-full bg-[hsl(var(--muted))] px-2.5 py-1 text-xs font-semibold text-[hsl(var(--muted-foreground))]">
              <ShieldCheck size={12} />
              {complianceMode.toUpperCase()}
            </span>
          </div>
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            (onSave || defaultSaveHandler)({ name, slug });
          }}
          className="space-y-4 text-left"
        >
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="space-y-1.5 text-left">
              <label className="text-xs font-medium text-[hsl(var(--muted-foreground))]">Organization Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full rounded-[var(--radius-md)] border border-[hsl(var(--input))] bg-[hsl(var(--background))] px-3 py-2 text-xs font-medium text-[hsl(var(--foreground))] outline-none focus:border-[hsl(var(--ring))]"
              />
            </div>
            <div className="space-y-1.5 text-left">
              <label className="text-xs font-medium text-[hsl(var(--muted-foreground))]">Workspace Slug</label>
              <input
                type="text"
                value={slug}
                onChange={(e) => setSlug(e.target.value)}
                className="w-full rounded-[var(--radius-md)] border border-[hsl(var(--input))] bg-[hsl(var(--background))] px-3 py-2 text-xs font-medium text-[hsl(var(--foreground))] outline-none focus:border-[hsl(var(--ring))]"
              />
            </div>
          </div>

          <div className="flex justify-end pt-2">
            <Button
              variant="gradient"
              size="sm"
              type="submit"
            >
              Save Organization Changes
            </Button>
          </div>
        </form>
      </div>

      <div className="rounded-[var(--radius-lg)] border border-[hsl(var(--destructive)/.3)] bg-[hsl(var(--destructive)/.05)] p-6 space-y-3 text-left">
        <div className="flex items-center gap-2 text-[hsl(var(--destructive))]">
          <Trash2 size={18} />
          <h3 className="text-sm font-bold">Danger Zone: Delete Organization</h3>
        </div>
        <p className="text-xs text-[hsl(var(--muted-foreground))]">
          Soft-deletes this organization and revokes access for all team members with 30-day backup retention.
        </p>
        <div>
          <Button
            variant="destructive"
            size="sm"
            onClick={onDelete || defaultDeleteHandler}
          >
            Delete Organization
          </Button>
        </div>
      </div>
    </div>
  );
}
