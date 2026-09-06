/**
 * @file step-tracing.ts
 * @description Middleware Step: Server-Side OpenTelemetry Trace Span Generation.
 * 
 * ALGORITHM & SPECIFICATION:
 * 1. OpenTelemetry Server Span Creation:
 *    - Creates an active `SERVER` span (`HTTP <method> <pathname>`).
 *    - Records standard HTTP attributes (`http.method`, `http.target`, `request_id`, `correlation_id`).
 */

import { SpanKind } from "@opentelemetry/api";
import { withSpan } from "../../tracing/tracer";
import { HTTP_CONSTANTS } from "../constants";
import type { HttpMiddleware, HttpMiddlewareCtx } from "./types";

export const withHttpTracing = (
  serviceName: string = HTTP_CONSTANTS.DEFAULT_HTTP_SERVICE_NAME
): HttpMiddleware<HttpMiddlewareCtx, unknown> => {
  return (next) => async (ctx) => {
    return withSpan(
      `HTTP ${ctx.method} ${ctx.pathname}`,
      async (span) => {
        span.setAttribute(HTTP_CONSTANTS.ATTR_HTTP_METHOD, ctx.method);
        span.setAttribute(HTTP_CONSTANTS.ATTR_HTTP_TARGET, ctx.pathname);
        span.setAttribute(HTTP_CONSTANTS.HEADER_X_REQUEST_ID, ctx.requestId);
        span.setAttribute(HTTP_CONSTANTS.ATTR_REQUEST_ID, ctx.requestId);
        span.setAttribute(HTTP_CONSTANTS.HEADER_X_CORRELATION_ID, ctx.correlationId);
        span.setAttribute(HTTP_CONSTANTS.ATTR_CORRELATION_ID, ctx.correlationId);

        try {
          const response = await next(ctx);
          console.log(`Middleware Step - 1 - [StepTracing] - OpenTelemetry SERVER Span Context Initialization - [DONE]`);
          return response;
        } catch (err: any) {
          console.error(`Middleware Step - 1 - [StepTracing] - OpenTelemetry SERVER Span Context Initialization - [FAILED]`);
          throw err;
        }
      },
      { kind: SpanKind.SERVER, serviceName }
    );
  };
};
