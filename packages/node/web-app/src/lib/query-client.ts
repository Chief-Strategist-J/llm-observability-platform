import { QueryClient } from '@tanstack/react-query';

const STALE_TIME_MS = 30_000;
const RETRY_DELAY_BASE_MS = 1000;
const MAX_RETRIES = 3;

function parseRetryAfter(error: unknown): number | undefined {
  if (
    typeof error === 'object' &&
    error !== null &&
    'headers' in error &&
    typeof (error as Record<string, unknown>).headers === 'object'
  ) {
    const headers = (error as { headers: Record<string, string> }).headers;
    const retryAfter = headers['retry-after'];
    if (retryAfter) {
      const seconds = Number(retryAfter);
      if (!Number.isNaN(seconds)) {
        return seconds * 1000;
      }
    }
  }
  return undefined;
}

export function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: STALE_TIME_MS,
        retry: MAX_RETRIES,
        retryDelay: (attemptIndex, error) => {
          const retryAfterMs = parseRetryAfter(error);
          if (retryAfterMs !== undefined) {
            return retryAfterMs;
          }
          return Math.min(RETRY_DELAY_BASE_MS * 2 ** attemptIndex, 30_000);
        },
        refetchOnWindowFocus: false,
      },
      mutations: {
        retry: 1,
      },
    },
  });
}
