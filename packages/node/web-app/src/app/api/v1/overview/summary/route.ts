import { NextResponse } from "next/server";
import { OverviewQuerySchema, overviewClientService } from "@/features/overview";

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const parseResult = OverviewQuerySchema.safeParse({
      time_range: searchParams.get("time_range") || undefined,
      environment: searchParams.get("environment") || undefined,
    });

    if (!parseResult.success) {
      return NextResponse.json(
        { error: "Invalid query parameters", details: parseResult.error.format() },
        { status: 400 }
      );
    }

    const { time_range } = parseResult.data;
    const data = await overviewClientService.getKPISummary(time_range);
    return NextResponse.json(data);
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || "Failed to fetch overview KPI summary" },
      { status: 500 }
    );
  }
}
