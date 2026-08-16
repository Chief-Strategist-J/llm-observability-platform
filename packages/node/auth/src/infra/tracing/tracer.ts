import { trace, type Tracer, SpanKind, SpanStatusCode, type Span } from '@opentelemetry/api';
import { AUTH_CONSTANTS } from '../../shared/constants/auth.constants';

let activeTracer: Tracer | null = null;

export function getTracer(): Tracer {
  if (!activeTracer) {
    activeTracer = trace.getTracer(AUTH_CONSTANTS.SERVICE_NAME, AUTH_CONSTANTS.SERVICE_VERSION);
  }
  return activeTracer;
}

export async function withSpan<T>(
  name: string,
  fn: (span: Span) => Promise<T>,
  options: { kind?: SpanKind; attributes?: Record<string, string | number | boolean> } = {}
): Promise<T> {
  const tracer = getTracer();
  return tracer.startActiveSpan(
    name,
    { kind: options.kind ?? SpanKind.INTERNAL, attributes: options.attributes },
    async (span) => {
      try {
        const result = await fn(span);
        span.setStatus({ code: SpanStatusCode.OK });
        return result;
      } catch (error) {
        span.setStatus({
          code: SpanStatusCode.ERROR,
          message: error instanceof Error ? error.message : String(error),
        });
        if (error instanceof Error) {
          span.recordException(error);
        }
        throw error;
      } finally {
        span.end();
      }
    }
  );
}
