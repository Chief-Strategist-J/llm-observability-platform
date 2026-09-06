'use client';

import React from 'react';
import { useSelector } from 'react-redux';
import { OrgSettingsForm } from '../../../features/auth';
import { Building2 } from 'lucide-react';
import { ThemeSwitcher } from '../../../components/ui/ThemeSwitcher';

export default function OrgSettingsPage() {
  const authUser = useSelector((state: any) => state?.auth?.user);

  return (
    <div className="space-y-6 w-full text-left max-w-7xl mx-auto">
      <div className="flex items-center gap-3 pb-4 border-b border-[hsl(var(--border))]">
        <div className="flex h-10 w-10 items-center justify-center rounded-[var(--radius-lg)] bg-[hsl(var(--primary)/.15)] text-[hsl(var(--primary))] shrink-0">
          <Building2 size={22} />
        </div>
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[hsl(var(--foreground))]">Organization Settings</h1>
          <p className="text-xs text-[hsl(var(--muted-foreground))] mt-0.5">
            Manage workspace identity, API keys, webhook destinations, and visual theme preferences.
          </p>
        </div>
      </div>

      <OrgSettingsForm
        orgName={authUser?.org_name ?? 'Scaibu Corp'}
        orgSlug={(authUser?.org_name ?? 'scaibu-corp').toLowerCase().replace(/\s+/g, '-')}
      />

      <ThemeSwitcher />
    </div>
  );
}
