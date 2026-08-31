import { describe, it, expect } from "vitest";
import { COST_RULES } from "../rules";
import { CostSummaryQuerySchema } from "../schema";

describe("Costs Feature Slice", () => {
  it("defines cost budget rules", () => {
    expect(COST_RULES.length).toBeGreaterThan(0);
  });

  it("validates cost summary query parameters with default fallbacks", () => {
    const valid = CostSummaryQuerySchema.parse({});
    expect(valid.time_range).toBe("30d");
  });
});
