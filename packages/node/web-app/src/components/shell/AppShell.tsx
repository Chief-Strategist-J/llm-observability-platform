'use client';

import React from 'react';
import { usePathname } from 'next/navigation';
import { Sidebar } from './Sidebar';

export function AppShell({ children }: { readonly children: React.ReactNode }) {
  const pathname = usePathname();
  const isAuthRoute = pathname.startsWith('/auth');

  if (isAuthRoute) {
    return <main className="w-full min-h-screen">{children}</main>;
  }

  return (
    <div className="flex w-full min-h-screen">
      <Sidebar />
      <main className="flex-1 overflow-y-auto p-6">{children}</main>
    </div>
  );
}
