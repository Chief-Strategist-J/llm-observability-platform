import React from 'react';
import { SkeletonState } from '../../components/states/SkeletonState';

export default function DashboardLoading() {
  return (
    <div className="flex flex-col gap-6 p-2">
      <div className="flex flex-col gap-2">
        <SkeletonState lines={1} className="h-8 w-48" />
        <SkeletonState lines={1} className="h-4 w-96" />
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="h-32 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-4">
          <SkeletonState lines={3} />
        </div>
        <div className="h-32 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-4">
          <SkeletonState lines={3} />
        </div>
        <div className="h-32 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-4">
          <SkeletonState lines={3} />
        </div>
      </div>
    </div>
  );
}
