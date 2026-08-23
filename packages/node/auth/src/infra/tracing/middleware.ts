import { propagation, ROOT_CONTEXT, defaultTextMapGetter, context, SpanKind, SpanStatusCode } from '@opentelemetry/api';
import type { IncomingMessage, ServerResponse } from 'http';
import { getTracer } from './tracer';
import { HTTP_METHODS } from '../../shared/constants/endpoints';

export function traceHttpMiddleware(
  req: IncomingMessage,
  res: ServerResponse,
  next: (err?: unknown) => void
): void {
  const tracer = getTracer();
  const route = req.url ?? '/';
  const method = req.method ?? HTTP_METHODS.GET;

  const headerRecord: Record<string, string> = {};
  for (const [k, v] of Object.entries(req.headers)) {
    if (typeof v === 'string') {
      headerRecord[k.toLowerCase()] = v;
    } else if (Array.isArray(v) && v.length > 0) {
      headerRecord[k.toLowerCase()] = v[0]!;
    }
  }

  const extractedContext = propagation.extract(ROOT_CONTEXT, headerRecord, defaultTextMapGetter);

  context.with(extractedContext, () => {
    tracer.startActiveSpan(
      `HTTP ${method} ${route}`,
      {
        kind: SpanKind.SERVER,
        attributes: {
          'http.method': method,
          'http.target': route,
          'x-request-id': headerRecord['x-request-id'] ?? '',
          'x-correlation-id': headerRecord['x-correlation-id'] ?? '',
        },
      },
      (span) => {
        const originalEnd = res.end.bind(res);
        res.end = function (...args: unknown[]) {
          span.setAttribute('http.status_code', res.statusCode);
          if (res.statusCode >= 400) {
            span.setStatus({
              code: SpanStatusCode.ERROR,
              message: `HTTP Error ${res.statusCode}`,
            });
            span.setAttribute('error', true);
          } else {
            span.setStatus({ code: SpanStatusCode.OK });
          }
          span.end();
          return (originalEnd as Function).apply(res, args);
        } as typeof res.end;

        next();
      }
    );
  });
}
