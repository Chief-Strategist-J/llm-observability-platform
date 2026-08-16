'use client';

import React, { useMemo, useState } from 'react';
import { Provider } from 'react-redux';
import { createApplicationStore } from '@observability/core';
import { QueryClientProvider } from '@tanstack/react-query';
import { httpBatchLink } from '@trpc/client';
import superjson from 'superjson';
import { ThemeProvider } from '../theme/ThemeProvider';
import { NotificationProvider } from '../components/primitives/NotificationProvider';
import { FeatureFlagProvider } from '../lib/feature-flags';
import { trpc } from '../lib/trpc-client';
import { createQueryClient } from '../lib/query-client';
import '../features/auth';

function getBaseUrl(): string {
  if (typeof window !== 'undefined') return '';
  return `http://localhost:${process.env['PORT'] ?? 31400}`;
}

export function Providers({ children }: { readonly children: React.ReactNode }) {
  const store = useMemo(() => createApplicationStore(), []);
  const [queryClient] = useState(() => createQueryClient());
  const [trpcClient] = useState(() =>
    trpc.createClient({
      links: [
        httpBatchLink({
          url: `${getBaseUrl()}/api/trpc`,
          transformer: superjson,
        }),
      ],
    }),
  );

  return (
    <trpc.Provider client={trpcClient} queryClient={queryClient}>
      <QueryClientProvider client={queryClient}>
        <Provider store={store}>
          <ThemeProvider defaultTheme="dark">
            <NotificationProvider>
              <FeatureFlagProvider>
                {children}
              </FeatureFlagProvider>
            </NotificationProvider>
          </ThemeProvider>
        </Provider>
      </QueryClientProvider>
    </trpc.Provider>
  );
}
