'use client';

import React from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../primitives/Dialog';
import { Button } from '../primitives/Button';
import { AlertTriangle } from 'lucide-react';

interface SessionExpiredModalProps {
  readonly open: boolean;
  readonly onOpenChange?: (open: boolean) => void;
}

export function SessionExpiredModal({ open, onOpenChange }: SessionExpiredModalProps) {
  const router = useRouter();
  const pathname = usePathname();

  function handleReauth() {
    const signInUrl = `/auth/sign-in?callbackUrl=${encodeURIComponent(pathname)}`;
    router.push(signInUrl);
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <div className="mx-auto mb-2 flex h-10 w-10 items-center justify-center rounded-full bg-[hsl(var(--severity-warn)/.1)] text-[hsl(var(--severity-warn))]">
            <AlertTriangle size={20} />
          </div>
          <DialogTitle className="text-center">Session Expired</DialogTitle>
          <DialogDescription className="text-center">
            Your organization session has timed out. Please sign in again to continue. Your current view filters and URL context will be preserved.
          </DialogDescription>
        </DialogHeader>
        <div className="mt-4 flex justify-end">
          <Button onClick={handleReauth} className="w-full">
            Sign In Again
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
