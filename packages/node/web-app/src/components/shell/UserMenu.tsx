'use client';

import React from 'react';
import Link from 'next/link';
import { useSelector, useDispatch } from 'react-redux';
import { authActions } from '../../features/auth/auth.slice';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from '../primitives/DropdownMenu';
import { User, Settings, LogOut, ShieldAlert } from 'lucide-react';

interface UserMenuProps {
  readonly user?: {
    readonly name?: string | null;
    readonly email?: string | null;
  };
  readonly impersonating?: boolean;
}

export function UserMenu({ user: propUser, impersonating = false }: UserMenuProps) {
  const authUser = useSelector((state: any) => state?.auth?.user);
  const name = propUser?.name ?? authUser?.name ?? 'Admin User';
  const email = propUser?.email ?? authUser?.email ?? 'admin@observability.io';

  const dispatch = useDispatch();

  function handleSignOut() {
    dispatch(authActions.signOutSubmitted());
    if (typeof window !== 'undefined') {
      window.location.href = '/auth/sign-in';
    }
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button className="flex w-full items-center gap-3 rounded-[var(--radius-md)] p-2 text-left transition-colors hover:bg-[hsl(var(--muted)/.5)]">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[hsl(var(--primary))] text-xs font-semibold text-[hsl(var(--primary-foreground))]">
            {name.charAt(0).toUpperCase()}
          </div>
          <div className="flex flex-1 flex-col overflow-hidden">
            <span className="truncate text-xs font-semibold text-[hsl(var(--foreground))]">{name}</span>
            <span className="truncate text-[10px] text-[hsl(var(--muted-foreground))]">{email}</span>
          </div>
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <div className="px-2 py-1.5 text-xs">
          <p className="font-semibold">{name}</p>
          <p className="text-[10px] text-[hsl(var(--muted-foreground))]">{email}</p>
        </div>
        {impersonating && (
          <div className="my-1 flex items-center gap-1.5 rounded bg-[hsl(var(--severity-warn)/.15)] px-2 py-1 text-[10px] font-semibold text-[hsl(var(--severity-warn))]">
            <ShieldAlert size={12} />
            Support Impersonation Active
          </div>
        )}
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild>
          <Link href="/settings/org" className="flex w-full items-center gap-2">
            <Settings size={14} />
            Org Settings
          </Link>
        </DropdownMenuItem>
        <DropdownMenuItem asChild>
          <Link href="/settings/members" className="flex w-full items-center gap-2">
            <User size={14} />
            Member Management
          </Link>
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={handleSignOut} className="text-[hsl(var(--destructive))]">
          <LogOut size={14} className="mr-2" />
          Sign out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
