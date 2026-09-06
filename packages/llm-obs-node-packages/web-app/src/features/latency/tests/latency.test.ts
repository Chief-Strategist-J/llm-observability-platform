import { describe, it, expect } from "vitest";
import { PercentilesQuerySchema, SLOQuerySchema, BaselineQuerySchema, AttributionQuerySchema } from "../schema";
import { LATENCY_QUERIES } from "../queries";
import { LATENCY_RULES } from "../rules";

describe("Latency Feature Data Schemas", () => {
  it("validates valid percentiles query parameters", () => {
    const res = PercentilesQuerySchema.safeParse({ model: "gpt-4", hour_of_day: "14" });
    expect(res.success).toBe(true);
    if (res.success) {
      expect(res.data.model).toBe("gpt-4");
      expect(res.data.hour_of_day).toBe(14);
      expect(res.data.quantiles).toBe("0.50,0.95,0.99");
    }
  });

  it("validates valid SLO query parameters", () => {
    const res = SLOQuerySchema.safeParse({ model: "gpt-4", endpoint: "/v1/chat/completions" });
    expect(res.success).toBe(true);
  });

  it("validates valid baseline query parameters", () => {
    const res = BaselineQuerySchema.safeParse({ model: "gpt-4", hour_of_day: 12, days: 7 });
    expect(res.success).toBe(true);
  });

  it("validates valid attribution query parameters", () => {
    const res = AttributionQuerySchema.safeParse({ model: "gpt-4", hour: "2026-08-29" });
    expect(res.success).toBe(true);
  });

  it("contains named flow query constants", () => {
    expect(LATENCY_QUERIES.FLOW_QUERY_PERCENTILES.endpoint).toBe("/v1/latency/percentiles");
    expect(LATENCY_QUERIES.FLOW_QUERY_SLO.endpoint).toBe("/v1/latency/slo");
    expect(LATENCY_QUERIES.FLOW_QUERY_BASELINE.endpoint).toBe("/v1/latency/baseline");
    expect(LATENCY_QUERIES.FLOW_QUERY_ATTRIBUTION.endpoint).toBe("/v1/latency/attribution");
  });

  it("contains declarative latency anomaly rules AS DATA", () => {
    expect(LATENCY_RULES.length).toBeGreaterThan(0);
    expect(LATENCY_RULES[0]?.id).toBe("RULE_SLO_BURN_CRITICAL");
  });
});
