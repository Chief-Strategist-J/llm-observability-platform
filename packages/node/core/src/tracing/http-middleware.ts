import { propagation, ROOT_CONTEXT, defaultTextMapGetter, context, SpanKind, SpanStatusCode, type Span } from '@opentelemetry/api';
import type { IncomingMessage, ServerResponse } from 'http';
import { getTracer } from './tracer';

export async function runWithHttpTracing(
  req: IncomingMessage,
  res: ServerResponse,
  serviceName: string,
  handler: (span: Span) => Promise<void>
): Promise<void> {
  const tracer = getTracer(serviceName);
  const route = req.url ?? '/';
  const method = req.method ?? 'GET';

  const headerRecord: Record<string, string> = {};
  for (const [k, v] of Object.entries(req.headers)) {
    if (typeof v === 'string') {
      headerRecord[k.toLowerCase()] = v;
    } else if (Array.isArray(v) && v.length > 0) {
      headerRecord[k.toLowerCase()] = v[0]!;
    }
  }

  const extractedContext = propagation.extract(ROOT_CONTEXT, headerRecord, defaultTextMapGetter);

  return context.with(extractedContext, async () => {
    return tracer.startActiveSpan(
      `HTTP ${method} ${route}`,
      {
        kind: SpanKind.SERVER,
        attributes: {
          'http.method': method,
          'http.target': route,
          'x-request-id': headerRecord['x-request-id'] ?? '',
          'request_id': headerRecord['x-request-id'] ?? '',
          'x-correlation-id': headerRecord['x-correlation-id'] ?? '',
          'correlation_id': headerRecord['x-correlation-id'] ?? '',
        },
      },
      async (span) => {
        try {
          await handler(span);
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
        } catch (err: unknown) {
          span.setStatus({
            code: SpanStatusCode.ERROR,
            message: err instanceof Error ? err.message : String(err),
          });
          span.recordException(err instanceof Error ? err : new Error(String(err)));
          span.setAttribute('error', true);
          throw err;
        } finally {
          span.end();
        }
      }
    );
  });
}
