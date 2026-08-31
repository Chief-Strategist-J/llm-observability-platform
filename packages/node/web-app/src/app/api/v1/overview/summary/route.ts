import { NextResponse } from "next/server";
import { OverviewQuerySchema, overviewClientService } from "@/features/overview";
import { withTracedValidation } from "@observability/shared-infra";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const rawParams = {
    time_range: searchParams.get("time_range") || undefined,
    environment: searchParams.get("environment") || undefined,
  };

  const result = await withTracedValidation(
    "GET /api/v1/overview/summary",
    OverviewQuerySchema,
    rawParams,
    async (params) => overviewClientService.getKPISummary(params.time_range)
  );

  if (!result.success) {
    return NextResponse.json({ error: result.error, details: result.details }, { status: 400 });
  }

  return NextResponse.json(result.data);
}
