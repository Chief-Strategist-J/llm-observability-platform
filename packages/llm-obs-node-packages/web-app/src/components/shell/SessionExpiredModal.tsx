'use client';

import React from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { Button } from '../primitives/Button';

interface SessionExpiredModalProps {
  readonly isOpen: boolean;
  readonly onReauth?: () => void;
}

export function SessionExpiredModal({ isOpen, onReauth }: SessionExpiredModalProps) {
  const router = useRouter();
  const pathname = usePathname();

  if (!isOpen) return null;

  function handleSignIn() {
    if (onReauth) {
      onReauth();
    }
    const signInUrl = `/auth/sign-in?callbackUrl=${encodeURIComponent(pathname)}`;
    router.push(signInUrl);
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-[var(--radius-xl)] border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-6 shadow-2xl">
        <h2 className="text-lg font-bold tracking-tight text-[hsl(var(--foreground))]">
          Session Expired
        </h2>
        <p className="mt-2 text-sm text-[hsl(var(--muted-foreground))]">
          Your session has timed out due to inactivity. Please sign in again to preserve your current work and continue.
        </p>
        <div className="mt-6 flex justify-end">
          <Button onClick={handleSignIn}>
            Sign in again
          </Button>
        </div>
      </div>
    </div>
  );
}
