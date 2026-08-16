import { SpanKind, SpanStatusCode } from '@opentelemetry/api';
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

  const span = tracer.startSpan(`HTTP ${method} ${route}`, {
    kind: SpanKind.SERVER,
    attributes: {
      'http.method': method,
      'http.target': route,
    },
  });

  const originalEnd = res.end.bind(res);
  res.end = function (...args: unknown[]) {
    span.setAttribute('http.status_code', res.statusCode);
    if (res.statusCode >= 400) {
      span.setStatus({
        code: SpanStatusCode.ERROR,
        message: `HTTP Error ${res.statusCode}`,
      });
    } else {
      span.setStatus({ code: SpanStatusCode.OK });
    }
    span.end();
    return (originalEnd as Function).apply(res, args);
  } as typeof res.end;

  next();
}
