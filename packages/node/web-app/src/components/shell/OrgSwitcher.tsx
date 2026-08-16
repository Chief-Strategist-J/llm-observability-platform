'use client';

import React, { useEffect, useState, useRef } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { Building2, Check, ChevronDown, Plus } from 'lucide-react';
import { authActions } from '../../features/auth/auth.slice';

export function OrgSwitcher() {
  const dispatch = useDispatch();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const authUser = useSelector((state: any) => state?.auth?.user);
  const userOrganizations = useSelector((state: any) => state?.auth?.userOrganizations || []);
  const activeOrgName = authUser?.org_name || 'Organization';
  const activeOrgId = authUser?.org_id;

  useEffect(() => {
    dispatch(authActions.fetchOrganizationsSubmitted());
  }, [dispatch]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSwitch = (orgId: string) => {
    if (orgId !== activeOrgId) {
      dispatch(authActions.switchOrganizationSubmitted({ orgId }));
    }
    setIsOpen(false);
  };

  return (
    <div className="relative inline-block text-left" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        type="button"
        className="flex items-center gap-2.5 px-3 py-1.5 border rounded-[var(--radius-md)] bg-[hsl(var(--card))] border-[hsl(var(--border))] hover:bg-[hsl(var(--accent)/0.5)] transition-colors cursor-pointer"
      >
        <div className="flex h-7 w-7 items-center justify-center rounded-[var(--radius-md)] bg-[hsl(var(--primary)/.1)] text-[hsl(var(--primary))] shrink-0">
          <Building2 size={16} />
        </div>
        <div className="flex flex-col text-left overflow-hidden min-w-[120px]">
          <span className="truncate text-xs font-semibold text-[hsl(var(--foreground))]">{activeOrgName}</span>
          <span className="truncate text-[10px] text-[hsl(var(--muted-foreground))]">Active Workspace</span>
        </div>
        <ChevronDown size={14} className="text-[hsl(var(--muted-foreground))] ml-1" />
      </button>

      {isOpen && (
        <div className="absolute left-0 mt-2 w-64 rounded-md shadow-lg bg-[hsl(var(--card))] border border-[hsl(var(--border))] z-50 py-1">
          <div className="px-3 py-2 border-b border-[hsl(var(--border))]">
            <p className="text-[11px] font-semibold text-[hsl(var(--muted-foreground))] uppercase tracking-wider">
              Organizations
            </p>
          </div>
          <div className="max-h-60 overflow-y-auto">
            {userOrganizations.length > 0 ? (
              userOrganizations.map((org: any) => {
                const isSelected = org.id === activeOrgId;
                return (
                  <button
                    key={org.id}
                    onClick={() => handleSwitch(org.id)}
                    className="w-full flex items-center justify-between px-3 py-2 text-xs text-left hover:bg-[hsl(var(--accent)/0.5)] text-[hsl(var(--foreground))] transition-colors"
                  >
                    <span className="truncate font-medium">{org.name}</span>
                    {isSelected && <Check size={14} className="text-[hsl(var(--primary))]" />}
                  </button>
                );
              })
            ) : (
              <div className="px-3 py-2 text-xs text-[hsl(var(--muted-foreground))]">{activeOrgName}</div>
            )}
          </div>
          <div className="border-t border-[hsl(var(--border))] pt-1 mt-1">
            <a
              href="/admin/organizations"
              className="flex items-center gap-2 px-3 py-2 text-xs text-[hsl(var(--primary))] font-medium hover:bg-[hsl(var(--accent)/0.5)]"
            >
              <Plus size={14} />
              Manage / Add Organization
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
