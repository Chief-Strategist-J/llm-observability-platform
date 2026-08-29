import { NextResponse } from "next/server";
import { BaselineQuerySchema, latencyClientService } from "@/features/latency";

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const parseResult = BaselineQuerySchema.safeParse({
      model: searchParams.get("model"),
      hour_of_day: searchParams.get("hour_of_day"),
      days: searchParams.get("days") || undefined,
    });

    if (!parseResult.success) {
      return NextResponse.json(
        { error: "Invalid query parameters", details: parseResult.error.format() },
        { status: 400 }
      );
    }

    const { model, hour_of_day, days } = parseResult.data;
    const data = await latencyClientService.getBaseline(model, hour_of_day, days);
    return NextResponse.json(data);
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || "Failed to fetch latency baseline" },
      { status: 500 }
    );
  }
}
