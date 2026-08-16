'use client';

import React, { useState } from 'react';
import { Building2, ShieldCheck, CreditCard, Trash2 } from 'lucide-react';

interface OrgSettingsFormProps {
  readonly orgName?: string;
  readonly orgSlug?: string;
  readonly plan?: string;
  readonly complianceMode?: string;
  readonly onSave?: (data: { name: string; slug: string }) => void;
  readonly onDelete?: () => void;
}

export function OrgSettingsForm({
  orgName = 'Scaibu Corp',
  orgSlug = 'scaibu-corp',
  plan = 'ENTERPRISE',
  complianceMode = 'standard',
  onSave,
  onDelete,
}: OrgSettingsFormProps) {
  const [name, setName] = useState(orgName);
  const [slug, setSlug] = useState(orgSlug);

  return (
    <div className="space-y-6 max-w-4xl">
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
            onSave?.({ name, slug });
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
            <button
              type="submit"
              className="rounded-[var(--radius-md)] bg-[hsl(var(--primary))] px-4 py-2 text-xs font-semibold text-[hsl(var(--primary-foreground))] transition-opacity hover:opacity-90"
            >
              Save Organization Changes
            </button>
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
          <button
            type="button"
            onClick={onDelete}
            className="rounded-[var(--radius-md)] bg-[hsl(var(--destructive))] px-4 py-2 text-xs font-semibold text-[hsl(var(--destructive-foreground))] transition-opacity hover:opacity-90"
          >
            Delete Organization
          </button>
        </div>
      </div>
    </div>
  );
}
