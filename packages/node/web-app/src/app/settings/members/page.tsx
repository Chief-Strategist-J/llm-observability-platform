import React from 'react';
import { EmptyState } from '../../../components/states/EmptyState';

export default function MembersSettingsPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Member Management</h1>
        <p className="text-sm text-[hsl(var(--muted-foreground))]">
          Invite team members, assign RBAC roles (owner, admin, member), and revoke access.
        </p>
      </div>

      <EmptyState
        title="Member Management"
        description="Active team members and pending invitations will be listed here."
      />
    </div>
  );
}
