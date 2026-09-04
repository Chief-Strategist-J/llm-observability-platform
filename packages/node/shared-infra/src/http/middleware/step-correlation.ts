/**
 * @file step-correlation.ts
 * @description Middleware Step: Request & Correlation ID Ingestion and Header Propagation.
 * 
 * ALGORITHM & SPECIFICATION:
 * 1. Distributed Context Ingestion:
 *    - Extracts `x-request-id`, `x-correlation-id`, `traceparent`, and `tracestate` from request headers.
 *    - Generates W3C compliant fallback traceparent and request identifiers if absent.
 * 2. Downstream Header Propagation:
 *    - Attaches identifiers to `customHeaders` map for seamless downstream microservice propagation.
 */

import { RequestContextHolder } from "../../tracing/request-context";
import { HTTP_CONSTANTS } from "../constants";
import type { HttpMiddleware, HttpMiddlewareCtx } from "./types";

export const withCorrelationId: HttpMiddleware<HttpMiddlewareCtx, unknown> = (next) => async (ctx) => {
  const requestId =
    ctx.headers[HTTP_CONSTANTS.HEADER_X_REQUEST_ID] ||
    `req-${Date.now()}-${Math.random().toString(36).substring(2, 8)}`;
  const correlationId = ctx.headers[HTTP_CONSTANTS.HEADER_X_CORRELATION_ID] || requestId;
  const traceparent = ctx.headers[HTTP_CONSTANTS.HEADER_TRACEPARENT] || RequestContextHolder.generateW3CTraceparent();
  const tracestate = ctx.headers[HTTP_CONSTANTS.HEADER_TRACESTATE] || HTTP_CONSTANTS.DEFAULT_TRACESTATE;

  try {
    const updatedCtx: HttpMiddlewareCtx = {
      ...ctx,
      requestId,
      correlationId,
      traceparent,
      tracestate,
      customHeaders: {
        ...ctx.customHeaders,
        [HTTP_CONSTANTS.HEADER_X_REQUEST_ID]: requestId,
        [HTTP_CONSTANTS.HEADER_X_CORRELATION_ID]: correlationId,
        [HTTP_CONSTANTS.HEADER_TRACEPARENT]: traceparent,
        [HTTP_CONSTANTS.HEADER_TRACESTATE]: tracestate,
      },
    };

    const res = await next(updatedCtx);
    console.log(`Middleware Step - 2 - [StepCorrelation] - Distributed Request ID & Correlation Ingestion - [DONE]`);
    return res;
  } catch (err: any) {
    console.error(`Middleware Step - 2 - [StepCorrelation] - Distributed Request ID & Correlation Ingestion - [FAILED]`);
    throw err;
  }
};
