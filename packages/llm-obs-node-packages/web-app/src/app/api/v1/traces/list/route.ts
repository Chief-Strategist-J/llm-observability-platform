import { NextResponse } from "next/server";
import { TraceListQuerySchema, tracesClientService } from "@/features/traces";
import { withTracedValidation } from "@observability/shared-infra";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const rawParams = {
    model: searchParams.get("model") || undefined,
    status: searchParams.get("status") || undefined,
    service: searchParams.get("service") || undefined,
    limit: searchParams.get("limit") || undefined,
  };

  const result = await withTracedValidation(
    "GET /api/v1/traces/list",
    TraceListQuerySchema,
    rawParams,
    async (params) =>
      tracesClientService.listTraces(params.model, params.status, params.service, params.limit)
  );

  if (!result.success) {
    return NextResponse.json({ error: result.error, details: result.details }, { status: 400 });
  }

  return NextResponse.json(result.data);
}
