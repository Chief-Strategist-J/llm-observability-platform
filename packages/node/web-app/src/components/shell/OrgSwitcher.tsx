'use client';

import React, { useState } from 'react';
import type { Org } from '@observability/api-types';
import { eventBus } from '@observability/core';
import { useQueryClient } from '@tanstack/react-query';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../primitives/Select';
import { Building2 } from 'lucide-react';

const DEMO_ORGS: readonly Org[] = [
  { id: 'org-001-default', name: 'Acme Corp', slug: 'acme-corp', compliance_mode: 'standard', plan: 'pro' },
  { id: 'org-002-hipaa', name: 'HealthCare Inc', slug: 'healthcare-inc', compliance_mode: 'hipaa', plan: 'enterprise' },
  { id: 'org-003-eu', name: 'EuroTech GmbH', slug: 'eurotech', compliance_mode: 'eu_only', plan: 'pro' },
];

export function OrgSwitcher() {
  const queryClient = useQueryClient();
  const defaultOrg = DEMO_ORGS[0];
  const [selectedOrgId, setSelectedOrgId] = useState(defaultOrg?.id ?? 'org-001-default');

  function handleValueChange(orgId: string) {
    setSelectedOrgId(orgId);
    eventBus.emit('org.switched', { orgId });
    void queryClient.invalidateQueries();
  }

  const selectedOrg = DEMO_ORGS.find((o) => o.id === selectedOrgId) ?? defaultOrg;
  const orgName = selectedOrg?.name ?? 'Acme Corp';

  return (
    <div className="flex items-center gap-2 px-2 py-1.5">
      <div className="flex h-7 w-7 items-center justify-center rounded-[var(--radius-md)] bg-[hsl(var(--primary)/.1)] text-[hsl(var(--primary))]">
        <Building2 size={16} />
      </div>
      <Select value={selectedOrgId} onValueChange={handleValueChange}>
        <SelectTrigger className="h-8 border-none bg-transparent p-0 text-xs font-semibold hover:bg-[hsl(var(--muted)/.5)]">
          <SelectValue placeholder="Select org">{orgName}</SelectValue>
        </SelectTrigger>
        <SelectContent>
          {DEMO_ORGS.map((org) => (
            <SelectItem key={org.id} value={org.id} className="text-xs">
              <div className="flex flex-col">
                <span className="font-semibold">{org.name}</span>
                <span className="text-[10px] text-[hsl(var(--muted-foreground))]">
                  {org.plan.toUpperCase()} • {org.compliance_mode}
                </span>
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
