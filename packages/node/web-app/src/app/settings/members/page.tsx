'use client';

import React, { useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { MemberManagementTable, type Member } from '../../../features/auth';
import { authActions } from '../../../features/auth/auth.slice';
import { Users } from 'lucide-react';

export default function MembersSettingsPage() {
  const dispatch = useDispatch();
  const members = useSelector((state: any) => state?.auth?.members || []);
  const authUser = useSelector((state: any) => state?.auth?.user);

  useEffect(() => {
    dispatch(authActions.fetchMembersSubmitted());
  }, [dispatch]);

  const displayMembers: readonly Member[] = members.length > 0
    ? members.map((m: any) => ({
        id: m.id,
        name: m.name,
        email: m.email,
        role: m.role || 'member',
        blocked: m.blocked || false,
      }))
    : authUser
    ? [
        {
          id: authUser.id || 'usr-current',
          name: authUser.name || 'Admin User',
          email: authUser.email || 'user@observability.io',
          role: (authUser.role as any) || 'owner',
          blocked: authUser.blocked || false,
        },
      ]
    : [];

  return (
    <div className="space-y-6 w-full text-left max-w-7xl mx-auto">
      <div className="flex items-center gap-3 pb-4 border-b border-[hsl(var(--border))]">
        <div className="flex h-10 w-10 items-center justify-center rounded-[var(--radius-lg)] bg-[hsl(var(--primary)/.15)] text-[hsl(var(--primary))] shrink-0">
          <Users size={22} />
        </div>
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[hsl(var(--foreground))]">Member Management</h1>
          <p className="text-xs text-[hsl(var(--muted-foreground))] mt-0.5">
            Invite team members, assign RBAC roles (owner, admin, member, viewer), and manage organization permissions.
          </p>
        </div>
      </div>

      <MemberManagementTable members={displayMembers} />
    </div>
  );
}
