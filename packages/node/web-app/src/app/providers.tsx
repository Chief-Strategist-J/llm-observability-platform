'use client';

import React, { useMemo, useState, useEffect } from 'react';
import { Provider } from 'react-redux';
import { createApplicationStore } from '@observability/shared-infra';
import { QueryClientProvider } from '@tanstack/react-query';
import { httpBatchLink } from '@trpc/client';
import superjson from 'superjson';
import { ThemeProvider } from '../theme/ThemeProvider';
import { NotificationProvider } from '../components/primitives/NotificationProvider';
import { FeatureFlagProvider } from '../lib/feature-flags/feature-flags';
import { trpc } from '../lib/api/trpc-client';
import { createQueryClient } from '../lib/api/query-client';
import { initOpenTelemetryTracer } from '../core/tracing/tracer';
import '../features/auth';

function getBaseUrl(): string {
  if (typeof window !== 'undefined') return '';
  return `http://localhost:${process.env['PORT'] ?? 31400}`;
}

export function Providers({ children }: { readonly children: React.ReactNode }) {
  useEffect(() => {
    initOpenTelemetryTracer();
  }, []);

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
