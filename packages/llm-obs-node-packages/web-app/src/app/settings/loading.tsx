import React from 'react';
import { SkeletonState } from '../../components/states/SkeletonState';

export default function SettingsLoading() {
  return (
    <div className="flex flex-col gap-6 p-2">
      <SkeletonState lines={2} className="w-64" />
      <div className="h-48 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-6">
        <SkeletonState lines={4} />
      </div>
    </div>
  );
}
