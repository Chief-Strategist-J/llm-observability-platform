'use client';

import React, { useState } from 'react';
import { useDispatch } from 'react-redux';
import { UserPlus, Shield, UserX, Ban, CheckCircle2 } from 'lucide-react';
import { authActions } from '../auth.slice';
import { authApiClient } from '../../../lib/auth-client';

export interface Member {
  readonly id: string;
  readonly name: string;
  readonly email: string;
  readonly role: 'owner' | 'admin' | 'member' | 'viewer';
  readonly blocked: boolean;
}

interface MemberManagementTableProps {
  readonly members?: readonly Member[];
  readonly onInviteMember?: (data: { email: string; name: string; role: string }) => void;
  readonly onBlockMember?: (userId: string) => void;
  readonly onDeleteMember?: (userId: string) => void;
}

function getCookieToken(): string | undefined {
  if (typeof document === 'undefined') return undefined;
  const match = document.cookie.match(new RegExp('(?:^|; )authjs\\.session-token=([^;]*)'));
  return match && match[1] ? decodeURIComponent(match[1]) : undefined;
}

export function MemberManagementTable({
  members = [],
  onInviteMember,
  onBlockMember,
  onDeleteMember,
}: MemberManagementTableProps) {
  const dispatch = useDispatch();
  const [showInviteForm, setShowInviteForm] = useState(false);
  const [newEmail, setNewEmail] = useState('');
  const [newName, setNewName] = useState('');
  const [newRole, setNewRole] = useState('member');

  const defaultInviteHandler = (data: { email: string; name: string; role: string }) => {
    dispatch(authActions.inviteUserSubmitted(data));
  };

  const defaultBlockHandler = async (userId: string) => {
    const token = getCookieToken();
    try {
      await authApiClient.blockUser(userId, token);
      dispatch(authActions.fetchMembersSubmitted());
    } catch (err) {
      console.error('Failed to block user:', err);
    }
  };

  const defaultDeleteHandler = async (userId: string) => {
    const token = getCookieToken();
    try {
      await authApiClient.deleteUser(userId, token);
      dispatch(authActions.fetchMembersSubmitted());
    } catch (err) {
      console.error('Failed to delete user:', err);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl text-left">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold text-[hsl(var(--foreground))]">Active Organization Members</h2>
          <p className="text-xs text-[hsl(var(--muted-foreground))]">Manage team seats, RBAC permissions, and access blocks.</p>
        </div>
        <button
          type="button"
          onClick={() => setShowInviteForm(!showInviteForm)}
          className="flex items-center gap-1.5 rounded-[var(--radius-md)] bg-[hsl(var(--primary))] px-3 py-2 text-xs font-semibold text-[hsl(var(--primary-foreground))]"
        >
          <UserPlus size={14} />
          Invite Team Member
        </button>
      </div>

      {showInviteForm && (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            const inviteFn = onInviteMember || defaultInviteHandler;
            inviteFn({ email: newEmail, name: newName, role: newRole });
            setNewEmail('');
            setNewName('');
            setShowInviteForm(false);
          }}
          className="rounded-[var(--radius-md)] border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-4 space-y-4 text-left"
        >
          <h3 className="text-xs font-bold text-[hsl(var(--foreground))]">New Member Invitation</h3>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <input
              type="text"
              placeholder="Full Name"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              required
              className="rounded-[var(--radius-md)] border border-[hsl(var(--input))] bg-[hsl(var(--background))] px-3 py-2 text-xs font-medium text-[hsl(var(--foreground))]"
            />
            <input
              type="email"
              placeholder="Email Address"
              value={newEmail}
              onChange={(e) => setNewEmail(e.target.value)}
              required
              className="rounded-[var(--radius-md)] border border-[hsl(var(--input))] bg-[hsl(var(--background))] px-3 py-2 text-xs font-medium text-[hsl(var(--foreground))]"
            />
            <select
              value={newRole}
              onChange={(e) => setNewRole(e.target.value)}
              className="rounded-[var(--radius-md)] border border-[hsl(var(--input))] bg-[hsl(var(--background))] px-3 py-2 text-xs font-medium text-[hsl(var(--foreground))]"
            >
              <option value="admin">Admin</option>
              <option value="member">Member</option>
              <option value="viewer">Viewer</option>
            </select>
          </div>
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setShowInviteForm(false)}
              className="rounded-[var(--radius-md)] border border-[hsl(var(--border))] px-3 py-1.5 text-xs font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="rounded-[var(--radius-md)] bg-[hsl(var(--primary))] px-3 py-1.5 text-xs font-semibold text-[hsl(var(--primary-foreground))]"
            >
              Send Invitation
            </button>
          </div>
        </form>
      )}

      <div className="rounded-[var(--radius-md)] border border-[hsl(var(--border))] bg-[hsl(var(--card))] overflow-hidden">
        {members.length === 0 ? (
          <div className="p-8 text-center text-xs text-[hsl(var(--muted-foreground))]">
            No team members found. Click &quot;Invite Team Member&quot; to add team members to this organization.
          </div>
        ) : (
          <table className="w-full text-left text-xs">
            <thead className="bg-[hsl(var(--muted)/.5)] border-b border-[hsl(var(--border))]">
              <tr>
                <th className="p-3 font-semibold text-[hsl(var(--muted-foreground))]">Member</th>
                <th className="p-3 font-semibold text-[hsl(var(--muted-foreground))]">Role</th>
                <th className="p-3 font-semibold text-[hsl(var(--muted-foreground))]">Status</th>
                <th className="p-3 text-right font-semibold text-[hsl(var(--muted-foreground))]">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[hsl(var(--border))]">
              {members.map((member) => (
                <tr key={member.id} className="hover:bg-[hsl(var(--muted)/.3)]">
                  <td className="p-3">
                    <div className="font-semibold text-[hsl(var(--foreground))]">{member.name}</div>
                    <div className="text-[10px] text-[hsl(var(--muted-foreground))]">{member.email}</div>
                  </td>
                  <td className="p-3">
                    <span className="inline-flex items-center gap-1 rounded bg-[hsl(var(--primary)/.1)] px-2 py-0.5 font-bold uppercase text-[10px] text-[hsl(var(--primary))]">
                      <Shield size={10} />
                      {member.role}
                    </span>
                  </td>
                  <td className="p-3">
                    {member.blocked ? (
                      <span className="inline-flex items-center gap-1 text-[hsl(var(--destructive))] font-semibold">
                        <Ban size={12} />
                        Blocked
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-[hsl(var(--success,green))] font-semibold">
                        <CheckCircle2 size={12} />
                        Active
                      </span>
                    )}
                  </td>
                  <td className="p-3 text-right">
                    <div className="flex justify-end gap-2">
                      <button
                        type="button"
                        onClick={() => (onBlockMember || defaultBlockHandler)(member.id)}
                        className="rounded p-1 text-[hsl(var(--muted-foreground))] hover:bg-[hsl(var(--muted))] hover:text-[hsl(var(--foreground))]"
                        title="Block Member"
                      >
                        <Ban size={14} />
                      </button>
                      <button
                        type="button"
                        onClick={() => (onDeleteMember || defaultDeleteHandler)(member.id)}
                        className="rounded p-1 text-[hsl(var(--destructive))] hover:bg-[hsl(var(--destructive)/.1)]"
                        title="Soft Delete Member"
                      >
                        <UserX size={14} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
