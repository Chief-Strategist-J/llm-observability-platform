import { describe, it, expect } from "vitest";
import { QUALITY_RULES } from "../rules";
import { QualitySummaryQuerySchema, QualitySummaryFromApiOps } from "../schema";
import { mapJson } from "../../../core/data-driven/json-map";

describe("Quality Feature Slice", () => {
  it("defines rules with categories and priorities", () => {
    expect(QUALITY_RULES.length).toBeGreaterThan(0);
    const criticalRule = QUALITY_RULES.find((r) => r.effect === "deny");
    expect(criticalRule).toBeDefined();
    expect(criticalRule?.priority).toBeGreaterThanOrEqual(90);
  });

  it("validates summary query parameters with default fallbacks", () => {
    const valid = QualitySummaryQuerySchema.parse({});
    expect(valid.model).toBe("gpt-4o");
    expect(valid.time_range).toBe("24h");
  });

  it("applies JsonMapOp transform to coerce raw API data to typed numbers", () => {
    const raw = {
      avg_quality_score: "0.95",
      score_delta_pct: "4.2",
      below_slo_count: "12",
      total_evaluated_prompts: "15000",
    };

    const transformed: any = mapJson(raw, QualitySummaryFromApiOps);
    expect(transformed.avg_quality_score).toBe(0.95);
    expect(transformed.score_delta_pct).toBe(4.2);
    expect(transformed.below_slo_count).toBe(12);
    expect(transformed.total_evaluated_prompts).toBe(15000);
  });
});
