import type { AppRouter } from '../../server/trpc/root';
import { createTRPCProxyClient, httpBatchLink } from '@trpc/client';
import superjson from 'superjson';

export function createEnterpriseApiClient(baseUrl: string, apiKey: string) {
  return createTRPCProxyClient<AppRouter>({
    links: [
      httpBatchLink({
        url: `${baseUrl}/api/trpc`,
        headers() {
          return {
            Authorization: `Bearer ${apiKey}`,
          };
        },
        transformer: superjson,
      }),
    ],
  });
}
