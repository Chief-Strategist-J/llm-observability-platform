import { NextResponse } from "next/server";
import { AttributionQuerySchema, latencyClientService } from "@/features/latency";

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const parseResult = AttributionQuerySchema.safeParse({
      model: searchParams.get("model"),
      hour: searchParams.get("hour"),
    });

    if (!parseResult.success) {
      return NextResponse.json(
        { error: "Invalid query parameters", details: parseResult.error.format() },
        { status: 400 }
      );
    }

    const { model, hour } = parseResult.data;
    const data = await latencyClientService.getAttribution(model, hour);
    return NextResponse.json(data);
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || "Failed to fetch latency attribution" },
      { status: 500 }
    );
  }
}
