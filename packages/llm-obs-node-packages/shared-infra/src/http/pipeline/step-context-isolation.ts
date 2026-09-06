/**
 * @file step-context-isolation.ts
 * @description Pipeline Step 2: AsyncLocalStorage Request Context & Payload Size Guard.
 * 
 * ALGORITHM & REASONING:
 * 1. Safe AsyncLocalStorage Context Resolution:
 *    - Extracts `tenantId`, `requestId`, `correlationId`, `traceparent` from `RequestContextHolder`.
 *    - Fallbacks gracefully to explicit headers or default tenant if AsyncLocalStorage is inactive.
 *    - Records telemetry attributes on `ctx.span` (`tenant.id`, `request.id`, `correlation.id`, `context.fallback_used`) for full observability.
 * 2. Safe Payload Byte Calculation:
 *    - Safely measures payload byte length using Buffer/Uint8Array or safe JSON stringify with circular structure guards.
 *    - Enforces maximum payload boundary (`maxBodySizeBytes`, default 10MB) before network execution.
 * 3. Outbound Header Envelope Propagation:
 *    - Injects `x-tenant-id`, `x-request-id`, `x-correlation-id`, and `traceparent` onto `ctx.config.headers`.
 */

import type { PipelineStep, PipelineContext } from "./types";
import { RequestContextHolder } from "../../tracing/request-context";
import { HTTP_CONSTANTS } from "../constants";

function calculatePayloadSizeBytes(body: unknown): number {
  if (body === undefined || body === null) return 0;
  if (typeof body === "string") return Buffer.byteLength(body, "utf-8");
  if (Buffer.isBuffer(body)) return body.length;
  if (body instanceof Uint8Array) return body.byteLength;

  try {
    const jsonString = JSON.stringify(body);
    return Buffer.byteLength(jsonString, "utf-8");
  } catch (err: any) {
    throw new Error(`Invalid request payload: unable to serialize body to JSON (${err?.message || "circular structure"})`);
  }
}

export class StepContextIsolation implements PipelineStep {
  public readonly name = "ContextIsolation";
  public readonly description = "AsyncLocalStorage Context Isolation & Payload Size Guard";

  public async execute<T>(ctx: PipelineContext<T>): Promise<void> {
    ctx.stepIndex++;

    let requestId: string | undefined;
    let correlationId: string | undefined;
    let traceparent: string | undefined;
    let isFallback = false;

    try {
      const store = RequestContextHolder.get();
      ctx.tenantId = store.tenantId || ctx.config.headers?.[HTTP_CONSTANTS.HEADER_X_TENANT_ID] || HTTP_CONSTANTS.DEFAULT_TENANT_ID;
      requestId = store.requestId;
      correlationId = store.correlationId;
      traceparent = store.traceparent;
    } catch (err: any) {
      isFallback = true;
      ctx.tenantId = ctx.config.headers?.[HTTP_CONSTANTS.HEADER_X_TENANT_ID] || HTTP_CONSTANTS.DEFAULT_TENANT_ID;
      ctx.span?.addEvent("context_isolation_fallback", { error: err?.message || "RequestContextHolder resolution failed" });
    }

    // Header envelope injection
    const headers: Record<string, string> = { ...(ctx.config.headers || {}) };
    headers[HTTP_CONSTANTS.HEADER_X_TENANT_ID] = ctx.tenantId;

    if (requestId && !headers[HTTP_CONSTANTS.HEADER_X_REQUEST_ID]) {
      headers[HTTP_CONSTANTS.HEADER_X_REQUEST_ID] = requestId;
    }
    if (correlationId && !headers[HTTP_CONSTANTS.HEADER_X_CORRELATION_ID]) {
      headers[HTTP_CONSTANTS.HEADER_X_CORRELATION_ID] = correlationId;
    }
    if (traceparent && !headers["traceparent"]) {
      headers["traceparent"] = traceparent;
    }

    ctx.config.headers = headers;

    // Attach Telemetry Spans for zero-blind-spot debugging
    ctx.span?.setAttribute("tenant.id", ctx.tenantId);
    if (requestId) ctx.span?.setAttribute(HTTP_CONSTANTS.ATTR_REQUEST_ID, requestId);
    if (correlationId) ctx.span?.setAttribute(HTTP_CONSTANTS.ATTR_CORRELATION_ID, correlationId);
    ctx.span?.setAttribute("context.fallback_used", isFallback);

    // Payload size guard with circular JSON handling
    const bodySizeBytes = calculatePayloadSizeBytes(ctx.config.body);
    ctx.span?.setAttribute("http.request.body_size_bytes", bodySizeBytes);

    const maxBodyBytes = ctx.config.maxBodySizeBytes ?? 10 * 1024 * 1024;
    if (bodySizeBytes > maxBodyBytes) {
      throw new Error(`Request payload size (${bodySizeBytes} bytes) exceeds maximum limit of ${maxBodyBytes} bytes`);
    }
  }
}
