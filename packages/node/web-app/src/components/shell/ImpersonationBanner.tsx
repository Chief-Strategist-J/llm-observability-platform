'use client';

import React from 'react';
import { ShieldAlert, X } from 'lucide-react';

interface ImpersonationBannerProps {
  readonly active: boolean;
  readonly targetOrgName?: string;
  readonly onExit?: () => void;
}

export function ImpersonationBanner({ active, targetOrgName = 'Target Org', onExit }: ImpersonationBannerProps) {
  if (!active) return null;

  return (
    <div
      role="banner"
      className="flex items-center justify-between bg-[hsl(var(--severity-warn))] px-4 py-2 text-xs font-semibold text-black shadow-md"
    >
      <div className="flex items-center gap-2">
        <ShieldAlert size={16} aria-hidden="true" />
        <span>
          SUPPORT IMPERSONATION MODE ACTIVE — Viewing workspace for <strong>{targetOrgName}</strong>. All admin mutations are audit-logged (F-16).
        </span>
      </div>
      {onExit && (
        <button
          onClick={onExit}
          className="flex items-center gap-1 rounded bg-black/20 px-2 py-0.5 text-xs font-bold text-black hover:bg-black/30"
        >
          Exit Support Mode
          <X size={12} />
        </button>
      )}
    </div>
  );
}
