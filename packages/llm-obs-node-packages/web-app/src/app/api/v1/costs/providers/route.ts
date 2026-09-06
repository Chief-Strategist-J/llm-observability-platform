import { NextResponse } from "next/server";
import { CostSummaryQuerySchema, costsClientService } from "@/features/costs";
import { withTracedValidation } from "@observability/shared-infra";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const rawParams = {
    time_range: searchParams.get("time_range") || undefined,
  };

  const result = await withTracedValidation(
    "GET /api/v1/costs/providers",
    CostSummaryQuerySchema,
    rawParams,
    async (params) => costsClientService.getCostProviders(params.time_range)
  );

  if (!result.success) {
    return NextResponse.json({ error: result.error, details: result.details }, { status: 400 });
  }

  return NextResponse.json(result.data);
}
