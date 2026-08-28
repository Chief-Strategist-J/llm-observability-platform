'use client';

import React, { useEffect } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { Sidebar } from './Sidebar';
import { HeaderBar } from './HeaderBar';

function getClientCookieToken(): string | undefined {
  if (typeof document === 'undefined') return undefined;
  const match = document.cookie.match(new RegExp('(?:^|; )authjs\\.session-token=([^;]*)'));
  const token = match && match[1] ? decodeURIComponent(match[1]) : undefined;
  if (!token || token.trim() === '' || token === 'null' || token === 'undefined') return undefined;
  return token;
}

export function AppShell({ children }: { readonly children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const isAuthRoute = pathname.startsWith('/auth');

  useEffect(() => {
    if (!isAuthRoute) {
      const token = getClientCookieToken();
      if (!token) {
        router.push(`/auth/sign-in?callbackUrl=${encodeURIComponent(pathname)}`);
      }
    }
  }, [isAuthRoute, pathname, router]);

  if (isAuthRoute) {
    return <main className="w-full min-h-screen">{children}</main>;
  }

  return (
    <div className="flex w-full min-h-screen">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <HeaderBar />
        <main className="flex-1 overflow-y-auto p-6">{children}</main>
      </div>
    </div>
  );
}
