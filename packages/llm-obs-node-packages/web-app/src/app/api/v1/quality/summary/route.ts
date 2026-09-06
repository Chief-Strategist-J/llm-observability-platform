import { NextResponse } from "next/server";
import { QualitySummaryQuerySchema, qualityClientService } from "@/features/quality";
import { withTracedValidation } from "@observability/shared-infra";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const rawParams = {
    model: searchParams.get("model") || undefined,
    time_range: searchParams.get("time_range") || undefined,
  };

  const result = await withTracedValidation(
    "GET /api/v1/quality/summary",
    QualitySummaryQuerySchema,
    rawParams,
    async (params) => qualityClientService.getQualitySummary(params.model, params.time_range)
  );

  if (!result.success) {
    return NextResponse.json({ error: result.error, details: result.details }, { status: 400 });
  }

  return NextResponse.json(result.data);
}
