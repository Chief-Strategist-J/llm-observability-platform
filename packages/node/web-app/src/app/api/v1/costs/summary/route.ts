import { NextResponse } from "next/server";
import { CostSummaryQuerySchema, costsClientService } from "@/features/costs";

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const parseResult = CostSummaryQuerySchema.safeParse({
      time_range: searchParams.get("time_range") || undefined,
      provider: searchParams.get("provider") || undefined,
    });

    if (!parseResult.success) {
      return NextResponse.json(
        { error: "Invalid query parameters", details: parseResult.error.format() },
        { status: 400 }
      );
    }

    const { time_range } = parseResult.data;
    const data = await costsClientService.getCostSummary(time_range);
    return NextResponse.json(data);
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || "Failed to fetch cost summary" },
      { status: 500 }
    );
  }
}
