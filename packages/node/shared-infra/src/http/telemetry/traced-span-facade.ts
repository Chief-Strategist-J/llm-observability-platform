/**
 * @file traced-span-facade.ts
 * @description Sealed OpenTelemetry Span Facade implementing Default-Deny Attribute Filtering.
 * 
 * ALGORITHM & SPECIFICATION:
 * 1. Default-Deny Telemetry Filtering:
 *    - Wraps native OpenTelemetry `Span` instances.
 *    - Filters attribute assignment against `HTTP_CONSTANTS.ALLOWED_TELEMETRY_ATTRIBUTES`.
 *    - Automatically sanitizes primitives (string, number, boolean) and string arrays.
 *    - Prevents sensitive payload keys (e.g. Bearer tokens, cookies, request bodies) from leaking into tracing backends.
 * 2. Lifecycle Audit Tracing:
 *    - Exposes standard span operations (`setAttribute`, `addEvent`, `setStatus`, `recordException`, `end`).
 *    - Automatically strips non-whitelisted keys during `addEvent()` payload recording.
 */

import { type Span, SpanStatusCode } from "@opentelemetry/api";
import { HTTP_CONSTANTS } from "../constants";

const ALLOWED_TELEMETRY_SET = new Set<string>(HTTP_CONSTANTS.ALLOWED_TELEMETRY_ATTRIBUTES);

export class TracedSpanFacade {
  constructor(private readonly rawSpan: Span) {}

  public setAttribute(key: string, value: unknown): void {
    if (ALLOWED_TELEMETRY_SET.has(key)) {
      if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
        this.rawSpan.setAttribute(key, value);
      } else if (Array.isArray(value)) {
        this.rawSpan.setAttribute(key, value.map((item) => String(item)));
      } else if (value !== null && value !== undefined) {
        this.rawSpan.setAttribute(key, String(value));
      }
    }
  }

  public addEvent(name: string, attributes?: Record<string, unknown>): void {
    let filteredAttributes: Record<string, unknown> | undefined = undefined;
    if (attributes) {
      filteredAttributes = {};
      for (const [key, val] of Object.entries(attributes)) {
        if (ALLOWED_TELEMETRY_SET.has(key)) {
          filteredAttributes[key] = val;
        }
      }
    }
    this.rawSpan.addEvent(name, filteredAttributes as any);
  }

  public setStatus(status: { code: SpanStatusCode; message?: string }): void {
    this.rawSpan.setStatus(status);
  }

  public recordException(exception: unknown): void {
    this.rawSpan.recordException(exception as any);
  }

  public end(): void {
    this.rawSpan.end();
  }
}
