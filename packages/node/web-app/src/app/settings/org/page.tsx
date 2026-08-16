'use client';

import React from 'react';
import { useSelector } from 'react-redux';
import { OrgSettingsForm } from '../../../features/auth';

export default function OrgSettingsPage() {
  const authUser = useSelector((state: any) => state?.auth?.user);

  return (
    <div className="flex flex-col gap-6 text-left">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Organization Settings</h1>
        <p className="text-sm text-[hsl(var(--muted-foreground))]">
          Manage workspace identity, API keys, webhook destinations, and billing.
        </p>
      </div>

      <OrgSettingsForm
        orgName={authUser?.org_name ?? 'Scaibu Corp'}
        orgSlug={(authUser?.org_name ?? 'scaibu-corp').toLowerCase().replace(/\s+/g, '-')}
      />
    </div>
  );
}
