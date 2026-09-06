import * as Sentry from '@sentry/nextjs';

export function captureExceptionWithTrace(error: unknown, traceId?: string): void {
  Sentry.withScope((scope) => {
    if (traceId) {
      scope.setTag('trace_id', traceId);
    }
    Sentry.captureException(error);
  });
}
