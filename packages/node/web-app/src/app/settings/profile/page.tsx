'use client';

import React from 'react';
import { useSelector } from 'react-redux';
import { User, Mail, Shield, Building2, CheckCircle2 } from 'lucide-react';
import { ThemeSwitcher } from '../../../components/ui/ThemeSwitcher';

export default function UserProfilePage() {
  const authUser = useSelector((state: any) => state?.auth?.user);
  const userOrganizations = useSelector((state: any) => state?.auth?.userOrganizations || []);

  const name = authUser?.name || 'Jaydeep Scaibu';
  const email = authUser?.email || 'jaydeep@scaibu.com';
  const role = authUser?.role || 'owner';
  const orgName = authUser?.org_name || userOrganizations[0]?.name || 'Scaibu Enterprise';
  const orgId = authUser?.org_id || userOrganizations[0]?.id || 'org_default';

  return (
    <div className="space-y-6 w-full text-left max-w-7xl mx-auto">
      {/* Header Banner */}
      <div className="flex items-center gap-4 pb-4 border-b border-[hsl(var(--border))]">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-r from-purple-600 via-indigo-600 to-cyan-500 text-white font-bold text-lg shadow-lg">
          {name.charAt(0).toUpperCase()}
        </div>
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[hsl(var(--foreground))]">{name}</h1>
          <p className="text-xs text-[hsl(var(--muted-foreground))] mt-0.5 flex items-center gap-2">
            <Mail size={12} />
            {email}
          </p>
        </div>
      </div>

      {/* Grid details */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* User Identity Card */}
        <div className="rounded-[var(--radius-lg)] border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-6 space-y-4 shadow-sm text-left">
          <h3 className="text-sm font-bold text-[hsl(var(--foreground))] uppercase tracking-wider flex items-center gap-2 border-b border-[hsl(var(--border))] pb-3">
            <User size={16} className="text-purple-400" />
            Account Overview & Entitlements
          </h3>

          <div className="space-y-3 text-xs">
            <div className="flex justify-between items-center py-1.5 border-b border-[hsl(var(--border))/0.5]">
              <span className="text-[hsl(var(--muted-foreground))] flex items-center gap-1.5">
                <User size={14} /> Full Name
              </span>
              <span className="font-bold text-[hsl(var(--foreground))]">{name}</span>
            </div>

            <div className="flex justify-between items-center py-1.5 border-b border-[hsl(var(--border))/0.5]">
              <span className="text-[hsl(var(--muted-foreground))] flex items-center gap-1.5">
                <Mail size={14} /> Email Address
              </span>
              <span className="font-mono text-[hsl(var(--foreground))]">{email}</span>
            </div>

            <div className="flex justify-between items-center py-1.5 border-b border-[hsl(var(--border))/0.5]">
              <span className="text-[hsl(var(--muted-foreground))] flex items-center gap-1.5">
                <Shield size={14} /> Assigned RBAC Role
              </span>
              <span className="font-bold uppercase text-[10px] px-2.5 py-0.5 rounded-full bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-sm">
                {role}
              </span>
            </div>

            <div className="flex justify-between items-center py-1.5 border-b border-[hsl(var(--border))/0.5]">
              <span className="text-[hsl(var(--muted-foreground))] flex items-center gap-1.5">
                <Building2 size={14} /> Primary Organization
              </span>
              <span className="font-semibold text-[hsl(var(--foreground))]">{orgName} ({orgId})</span>
            </div>

            <div className="flex justify-between items-center py-1.5">
              <span className="text-[hsl(var(--muted-foreground))] flex items-center gap-1.5">
                <CheckCircle2 size={14} className="text-emerald-400" /> Security Status
              </span>
              <span className="text-emerald-400 font-bold">Active & Verified</span>
            </div>
          </div>
        </div>

        {/* Theme Settings Component */}
        <ThemeSwitcher />
      </div>
    </div>
  );
}
