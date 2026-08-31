import { describe, it, expect } from "vitest";
import { OVERVIEW_RULES } from "../rules";
import { OverviewQuerySchema } from "../schema";

describe("Overview Feature Slice", () => {
  it("defines overview system health rules", () => {
    expect(OVERVIEW_RULES.length).toBeGreaterThan(0);
  });

  it("validates overview query parameters with default fallbacks", () => {
    const valid = OverviewQuerySchema.parse({});
    expect(valid.time_range).toBe("24h");
  });
});
