import { describe, it, expect } from "vitest";
import { TRACE_RULES } from "../rules";
import { TraceListQuerySchema } from "../schema";

describe("Traces Feature Slice", () => {
  it("defines trace anomaly rules", () => {
    expect(TRACE_RULES.length).toBeGreaterThan(0);
  });

  it("validates trace list query parameters with default fallbacks", () => {
    const valid = TraceListQuerySchema.parse({});
    expect(valid.limit).toBe(20);
  });
});
