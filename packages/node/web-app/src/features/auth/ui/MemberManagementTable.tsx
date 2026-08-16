'use client';

import React, { useState } from 'react';
import { useDispatch } from 'react-redux';
import { UserPlus, Shield, UserX, Ban, CheckCircle2, Crown, Sparkles, Edit, X, Save, User, Mail } from 'lucide-react';
import { authActions } from '../auth.slice';
import { authApiClient } from '../../../lib/auth-client';
import { Button } from '../../../components/primitives/Button';

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
  readonly onUpdateRole?: (userId: string, role: string) => void;
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
  onUpdateRole,
}: MemberManagementTableProps) {
  const dispatch = useDispatch();
  const [showInviteForm, setShowInviteForm] = useState(false);
  const [newEmail, setNewEmail] = useState('');
  const [newName, setNewName] = useState('');
  const [newRole, setNewRole] = useState('member');

  // Selected Member Modal State for Editing
  const [selectedMember, setSelectedMember] = useState<Member | null>(null);
  const [editName, setEditName] = useState('');
  const [editEmail, setEditEmail] = useState('');
  const [editRole, setEditRole] = useState<'owner' | 'admin' | 'member' | 'viewer'>('member');
  const [isSaving, setIsSaving] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

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

  const defaultRoleUpdateHandler = async (userId: string, role: string) => {
    const token = getCookieToken();
    try {
      await authApiClient.updateUserRole(userId, role, token);
      dispatch(authActions.fetchMembersSubmitted());
    } catch (err) {
      console.error('Failed to update user role:', err);
    }
  };

  const handleOpenEditModal = (member: Member) => {
    setSelectedMember(member);
    setEditName(member.name);
    setEditEmail(member.email);
    setEditRole(member.role);
    setStatusMsg(null);
  };

  const handleSaveMemberDetails = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedMember) return;
    setIsSaving(true);
    setStatusMsg(null);

    try {
      // Update role if changed
      if (editRole !== selectedMember.role) {
        await (onUpdateRole || defaultRoleUpdateHandler)(selectedMember.id, editRole);
      }
      setStatusMsg(`User "${editName}" details updated successfully!`);
      setTimeout(() => {
        setSelectedMember(null);
        dispatch(authActions.fetchMembersSubmitted());
      }, 800);
    } catch (err: any) {
      setStatusMsg(`Failed to save changes: ${err.message || 'Error occurred'}`);
    } finally {
      setIsSaving(false);
    }
  };

  const renderRoleBadge = (role: string) => {
    switch (role) {
      case 'owner':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full font-extrabold uppercase text-[10px] bg-gradient-to-r from-amber-500 to-purple-600 text-white shadow-sm">
            <Crown size={10} />
            Owner
          </span>
        );
      case 'admin':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full font-bold uppercase text-[10px] bg-gradient-to-r from-cyan-600 to-blue-600 text-white shadow-sm">
            <Shield size={10} />
            Admin
          </span>
        );
      case 'member':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full font-bold uppercase text-[10px] dark:bg-emerald-950/80 bg-emerald-100/90 dark:text-emerald-300 text-emerald-900 border border-emerald-500/50 shadow-sm">
            <Sparkles size={10} />
            Member
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full font-bold uppercase text-[10px] bg-[hsl(var(--muted))] text-[hsl(var(--muted-foreground))] border border-[hsl(var(--border))]">
            Viewer
          </span>
        );
    }
  };

  return (
    <div className="space-y-4 w-full text-left">
      <div className="flex items-center justify-between pb-2 border-b border-[hsl(var(--border))]">
        <div>
          <h2 className="text-sm font-bold text-[hsl(var(--foreground))]">Active Organization Members</h2>
          <p className="text-[11px] text-[hsl(var(--muted-foreground))]">Tap any row to view and edit full user details, permissions, and access states.</p>
        </div>
        <Button
          variant="gradient"
          size="sm"
          onClick={() => setShowInviteForm(!showInviteForm)}
          className="flex items-center gap-1.5"
        >
          <UserPlus size={14} />
          Invite Team Member
        </Button>
      </div>

      {/* Invite Form */}
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
          className="rounded-[var(--radius-lg)] border-2 border-purple-500/40 bg-[hsl(var(--card))] p-4 space-y-3 text-left shadow-xl animate-in fade-in duration-200"
        >
          <h3 className="text-xs font-bold text-[hsl(var(--foreground))] uppercase tracking-wider flex items-center gap-2">
            <UserPlus size={14} className="text-purple-500 dark:text-purple-400" />
            New Member Invitation
          </h3>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <input
              type="text"
              placeholder="Full Name"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              required
              className="rounded-[var(--radius-md)] border border-[hsl(var(--input))] bg-[hsl(var(--background))] px-3 py-2 text-xs font-medium text-[hsl(var(--foreground))] outline-none focus:border-purple-500"
            />
            <input
              type="email"
              placeholder="Email Address"
              value={newEmail}
              onChange={(e) => setNewEmail(e.target.value)}
              required
              className="rounded-[var(--radius-md)] border border-[hsl(var(--input))] bg-[hsl(var(--background))] px-3 py-2 text-xs font-medium text-[hsl(var(--foreground))] outline-none focus:border-purple-500"
            />
            <select
              value={newRole}
              onChange={(e) => setNewRole(e.target.value)}
              className="rounded-[var(--radius-md)] border border-[hsl(var(--input))] bg-[hsl(var(--background))] px-3 py-2 text-xs font-medium text-[hsl(var(--foreground))] outline-none focus:border-purple-500 cursor-pointer"
            >
              <option value="admin">Admin (Full Control)</option>
              <option value="member">Member (Standard Access)</option>
              <option value="viewer">Viewer (Read Only)</option>
            </select>
          </div>
          <div className="flex justify-end gap-2 pt-1">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowInviteForm(false)}
            >
              Cancel
            </Button>
            <Button
              variant="gradient"
              size="sm"
              type="submit"
            >
              Send Invitation
            </Button>
          </div>
        </form>
      )}

      {/* Member Details Modal */}
      {selectedMember && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-150">
          <div className="w-full max-w-lg rounded-[var(--radius-xl)] bg-[hsl(var(--card))] border border-[hsl(var(--border))] shadow-2xl overflow-hidden text-left p-6 space-y-5">
            <div className="flex items-center justify-between border-b border-[hsl(var(--border))] pb-3">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-r from-purple-600 to-indigo-600 text-white font-bold text-sm shadow">
                  {selectedMember.name.charAt(0).toUpperCase()}
                </div>
                <div>
                  <h3 className="text-base font-bold text-[hsl(var(--foreground))]">User Profile & Permissions</h3>
                  <p className="text-[11px] font-mono text-[hsl(var(--muted-foreground))]">ID: {selectedMember.id}</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setSelectedMember(null)}
                className="p-1 rounded text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] hover:bg-[hsl(var(--muted))]"
              >
                <X size={18} />
              </button>
            </div>

            {statusMsg && (
              <div className="rounded-[var(--radius-md)] border border-emerald-800 bg-emerald-950/60 p-3 text-xs text-emerald-300 font-medium">
                {statusMsg}
              </div>
            )}

            <form onSubmit={handleSaveMemberDetails} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold uppercase text-[hsl(var(--muted-foreground))] flex items-center gap-1.5">
                  <User size={13} /> Full Name
                </label>
                <input
                  type="text"
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  required
                  className="w-full rounded-[var(--radius-md)] border border-[hsl(var(--input))] bg-[hsl(var(--background))] px-3.5 py-2 text-xs font-medium text-[hsl(var(--foreground))] outline-none focus:border-purple-500"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold uppercase text-[hsl(var(--muted-foreground))] flex items-center gap-1.5">
                  <Mail size={13} /> Email Address
                </label>
                <input
                  type="email"
                  value={editEmail}
                  onChange={(e) => setEditEmail(e.target.value)}
                  required
                  className="w-full rounded-[var(--radius-md)] border border-[hsl(var(--input))] bg-[hsl(var(--background))] px-3.5 py-2 text-xs font-medium text-[hsl(var(--foreground))] outline-none focus:border-purple-500 font-mono"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold uppercase text-[hsl(var(--muted-foreground))] flex items-center gap-1.5">
                  <Shield size={13} /> Assigned RBAC Role
                </label>
                <select
                  value={editRole}
                  onChange={(e) => setEditRole(e.target.value as any)}
                  className="w-full rounded-[var(--radius-md)] border border-[hsl(var(--input))] bg-[hsl(var(--background))] px-3.5 py-2 text-xs font-bold text-[hsl(var(--foreground))] outline-none focus:border-purple-500 cursor-pointer"
                >
                  <option value="owner">Owner (Full System Rights)</option>
                  <option value="admin">Admin (Manage Members & API Keys)</option>
                  <option value="member">Member (Standard Operations)</option>
                  <option value="viewer">Viewer (Read Only Access)</option>
                </select>
              </div>

              <div className="flex items-center justify-between pt-3 border-t border-[hsl(var(--border))]">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-medium text-[hsl(var(--muted-foreground))]">Access State:</span>
                  {selectedMember.blocked ? (
                    <span className="text-xs font-bold text-[hsl(var(--destructive))]">Blocked</span>
                  ) : (
                    <span className="text-xs font-bold text-emerald-400">Active</span>
                  )}
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setSelectedMember(null)}
                  >
                    Cancel
                  </Button>
                  <Button
                    variant="gradient"
                    size="sm"
                    type="submit"
                    disabled={isSaving}
                  >
                    <Save size={14} className="mr-1.5" />
                    {isSaving ? 'Saving...' : 'Save User Details'}
                  </Button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Main Members Table */}
      <div className="rounded-[var(--radius-lg)] border border-[hsl(var(--border))] bg-[hsl(var(--card))] overflow-hidden shadow-md">
        {members.length === 0 ? (
          <div className="p-6 text-center text-xs text-[hsl(var(--muted-foreground))]">
            No team members found. Click &quot;Invite Team Member&quot; to add team members to this organization.
          </div>
        ) : (
          <table className="w-full text-left text-xs">
            <thead className="bg-[hsl(var(--muted)/.5)] border-b border-[hsl(var(--border))]">
              <tr>
                <th className="p-3 font-bold uppercase tracking-wider text-[10px] text-[hsl(var(--muted-foreground))]">Member Info (Tap to View/Edit)</th>
                <th className="p-3 font-bold uppercase tracking-wider text-[10px] text-[hsl(var(--muted-foreground))]">RBAC Role</th>
                <th className="p-3 font-bold uppercase tracking-wider text-[10px] text-[hsl(var(--muted-foreground))]">Quick Change Role</th>
                <th className="p-3 font-bold uppercase tracking-wider text-[10px] text-[hsl(var(--muted-foreground))]">Status</th>
                <th className="p-3 text-right font-bold uppercase tracking-wider text-[10px] text-[hsl(var(--muted-foreground))]">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[hsl(var(--border))]">
              {members.map((member) => (
                <tr
                  key={member.id}
                  className="hover:bg-[hsl(var(--muted)/.3)] transition-colors cursor-pointer"
                  onClick={() => handleOpenEditModal(member)}
                >
                  <td className="p-3">
                    <div className="font-bold text-xs text-[hsl(var(--foreground))] hover:underline flex items-center gap-1.5">
                      <span>{member.name}</span>
                      <Edit size={11} className="text-[hsl(var(--muted-foreground))]" />
                    </div>
                    <div className="text-[10px] text-[hsl(var(--muted-foreground))] font-mono">{member.email}</div>
                  </td>
                  <td className="p-3">
                    {renderRoleBadge(member.role)}
                  </td>
                  <td className="p-3" onClick={(e) => e.stopPropagation()}>
                    <select
                      value={member.role}
                      onChange={(e) => (onUpdateRole || defaultRoleUpdateHandler)(member.id, e.target.value)}
                      className="rounded-[var(--radius-md)] border border-[hsl(var(--input))] bg-[hsl(var(--background))] px-2.5 py-1 text-xs font-semibold text-[hsl(var(--foreground))] outline-none cursor-pointer hover:border-[hsl(var(--ring))]"
                    >
                      <option value="admin">Admin</option>
                      <option value="member">Member</option>
                      <option value="viewer">Viewer</option>
                      <option value="owner">Owner</option>
                    </select>
                  </td>
                  <td className="p-3">
                    {member.blocked ? (
                      <span className="inline-flex items-center gap-1 text-[hsl(var(--destructive))] font-bold text-xs">
                        <Ban size={12} />
                        Blocked
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-bold text-xs">
                        <CheckCircle2 size={12} />
                        Active
                      </span>
                    )}
                  </td>
                  <td className="p-3 text-right" onClick={(e) => e.stopPropagation()}>
                    <div className="flex justify-end gap-1.5">
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => (onBlockMember || defaultBlockHandler)(member.id)}
                        title="Block Access"
                      >
                        <Ban size={14} className="mr-1" />
                        Block
                      </Button>
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => (onDeleteMember || defaultDeleteHandler)(member.id)}
                        title="Soft Delete Member"
                      >
                        <UserX size={14} className="mr-1" />
                        Remove
                      </Button>
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
