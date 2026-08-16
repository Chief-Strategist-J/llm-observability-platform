'use client';

import React from 'react';
import { Eye, ShieldAlert } from 'lucide-react';
import { Button } from '../primitives/Button';

interface ImpersonationBannerProps {
  readonly impersonatedUser: string;
  readonly onEndImpersonation: () => void;
}

export function ImpersonationBanner({ impersonatedUser, onEndImpersonation }: ImpersonationBannerProps) {
  return (
    <div className="sticky top-0 z-40 flex items-center justify-between border-b border-[hsl(var(--severity-warn)/.3)] bg-[hsl(var(--severity-warn)/.15)] px-4 py-2 text-xs font-medium text-[hsl(var(--foreground))] backdrop-blur-md">
      <div className="flex items-center gap-2">
        <ShieldAlert size={16} className="text-[hsl(var(--severity-warn))]" />
        <span>
          <strong>Support Mode Active:</strong> Impersonating <code className="rounded bg-[hsl(var(--muted))] px-1 py-0.5 font-mono">{impersonatedUser}</code> (Read-Only Audit Logging Enforced)
        </span>
      </div>
      <Button size="sm" variant="outline" onClick={onEndImpersonation} className="h-6 gap-1 px-2 text-xs">
        <Eye size={12} />
        Exit Impersonation
      </Button>
    </div>
  );
}
