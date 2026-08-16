'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import type { Rule } from '@observability/core';
import { resolveFlag } from '@observability/core';

interface FeatureFlagContextValue {
  readonly flags: Record<string, boolean>;
  readonly isEnabled: (flagName: string) => boolean;
}

const FeatureFlagContext = createContext<FeatureFlagContextValue>({
  flags: {},
  isEnabled: () => false,
});

const DEMO_FLAG_RULES: Rule[] = [
  {
    id: 'experimental-dashboard',
    name: 'Enable experimental real-time streaming dashboard',
    category: 'experimental-dashboard',
    effect: 'allow',
    priority: 10,
    conditions: [],
  },
  {
    id: 'hipaa-redaction',
    name: 'Enforce HIPAA prompt text redaction',
    category: 'hipaa-redaction',
    effect: 'allow',
    priority: 10,
    conditions: [{ field: 'compliance_mode', op: 'equals', value: 'hipaa' }],
  },
];

export function FeatureFlagProvider({ children }: { readonly children: React.ReactNode }) {
  const [flags, setFlags] = useState<Record<string, boolean>>({});

  useEffect(() => {
    async function updateFlags() {
      const ctx = { userId: 'usr-001', compliance_mode: 'standard' };
      const exp = await resolveFlag('experimental-dashboard', ctx, DEMO_FLAG_RULES, 100);
      const hipaa = await resolveFlag('hipaa-redaction', ctx, DEMO_FLAG_RULES);
      setFlags({
        'experimental-dashboard': exp,
        'hipaa-redaction': hipaa,
      });
    }

    void updateFlags();
    const interval = setInterval(() => {
      void updateFlags();
    }, 60000);
    return () => clearInterval(interval);
  }, []);

  function isEnabled(flagName: string): boolean {
    return flags[flagName] ?? false;
  }

  const value: FeatureFlagContextValue = { flags, isEnabled };

  return (
    <FeatureFlagContext.Provider value={value}>
      {children}
    </FeatureFlagContext.Provider>
  );
}

export function useFeatureFlag(flagName: string): boolean {
  const context = useContext(FeatureFlagContext);
  return context.isEnabled(flagName);
}

export function FeatureFlagGate({
  flag,
  children,
  fallback = null,
}: {
  readonly flag: string;
  readonly children: React.ReactNode;
  readonly fallback?: React.ReactNode;
}) {
  const enabled = useFeatureFlag(flag);
  return enabled ? <>{children}</> : <>{fallback}</>;
}
