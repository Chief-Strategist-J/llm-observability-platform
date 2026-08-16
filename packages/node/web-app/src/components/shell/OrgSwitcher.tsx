'use client';

import React from 'react';
import { useSelector } from 'react-redux';
import { Building2 } from 'lucide-react';

export function OrgSwitcher() {
  const authUser = useSelector((state: any) => state?.auth?.user);
  const orgName = authUser?.org_name || 'Organization';

  return (
    <div className="flex items-center gap-2 px-2 py-1.5 border rounded-[var(--radius-md)] bg-[hsl(var(--card))] border-[hsl(var(--border))]">
      <div className="flex h-7 w-7 items-center justify-center rounded-[var(--radius-md)] bg-[hsl(var(--primary)/.1)] text-[hsl(var(--primary))]">
        <Building2 size={16} />
      </div>
      <div className="flex flex-col text-left overflow-hidden">
        <span className="truncate text-xs font-semibold text-[hsl(var(--foreground))]">{orgName}</span>
        <span className="truncate text-[10px] text-[hsl(var(--muted-foreground))]">Active Workspace</span>
      </div>
    </div>
  );
}
