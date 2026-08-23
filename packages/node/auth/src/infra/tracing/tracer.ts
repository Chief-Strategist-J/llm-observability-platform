import { initNodeTracing, getTracer as getCoreTracer, withSpan as withCoreSpan } from '@observability/core';
import { AUTH_CONSTANTS } from '../../shared/constants/auth.constants';

export function initAuthTracing(): void {
  initNodeTracing(AUTH_CONSTANTS.SERVICE_NAME, AUTH_CONSTANTS.SERVICE_VERSION);
}

export function getTracer() {
  return getCoreTracer(AUTH_CONSTANTS.SERVICE_NAME, AUTH_CONSTANTS.SERVICE_VERSION);
}

export function withSpan<T>(
  name: string,
  fn: (span: any) => Promise<T>,
  options: any = {}
): Promise<T> {
  return withCoreSpan(name, fn, { ...options, serviceName: AUTH_CONSTANTS.SERVICE_NAME });
}
