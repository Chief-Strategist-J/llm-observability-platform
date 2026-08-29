import { NextResponse } from "next/server";
import { SLOQuerySchema, latencyClientService } from "@/features/latency";

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const parseResult = SLOQuerySchema.safeParse({
      model: searchParams.get("model"),
      endpoint: searchParams.get("endpoint"),
    });

    if (!parseResult.success) {
      return NextResponse.json(
        { error: "Invalid query parameters", details: parseResult.error.format() },
        { status: 400 }
      );
    }

    const { model, endpoint } = parseResult.data;
    const data = await latencyClientService.getSLO(model, endpoint);
    return NextResponse.json(data);
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || "Failed to fetch SLO burn rates" },
      { status: 500 }
    );
  }
}
