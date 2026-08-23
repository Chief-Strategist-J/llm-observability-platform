import { runWithHttpTracing as runWithCoreHttpTracing } from '@observability/core/tracing';
import type { IncomingMessage, ServerResponse } from 'http';
import { AUTH_CONSTANTS } from '../../shared/constants/auth.constants';

export async function runWithHttpTracing(
  req: IncomingMessage,
  res: ServerResponse,
  handler: (span: any) => Promise<void>
): Promise<void> {
  return runWithCoreHttpTracing(req, res, AUTH_CONSTANTS.SERVICE_NAME, handler);
}
