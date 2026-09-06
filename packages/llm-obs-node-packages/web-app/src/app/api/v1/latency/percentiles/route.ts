import { NextResponse } from "next/server";
import { PercentilesQuerySchema, latencyClientService } from "@/features/latency";

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const parseResult = PercentilesQuerySchema.safeParse({
      model: searchParams.get("model"),
      hour_of_day: searchParams.get("hour_of_day"),
      quantiles: searchParams.get("quantiles") || undefined,
    });

    if (!parseResult.success) {
      return NextResponse.json(
        { error: "Invalid query parameters", details: parseResult.error.format() },
        { status: 400 }
      );
    }

    const { model, hour_of_day, quantiles } = parseResult.data;
    const data = await latencyClientService.getPercentiles(model, hour_of_day, quantiles);
    return NextResponse.json(data);
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || "Failed to fetch percentiles" },
      { status: 500 }
    );
  }
}
