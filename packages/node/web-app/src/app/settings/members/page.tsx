'use client';

import React, { useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { MemberManagementTable, type Member } from '../../../features/auth';
import { authActions } from '../../../features/auth/auth.slice';

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
    <div className="flex flex-col gap-6 text-left">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Member Management</h1>
        <p className="text-sm text-[hsl(var(--muted-foreground))]">
          Invite team members, assign RBAC roles (owner, admin, member, viewer), and revoke access.
        </p>
      </div>

      <MemberManagementTable members={displayMembers} />
    </div>
  );
}
