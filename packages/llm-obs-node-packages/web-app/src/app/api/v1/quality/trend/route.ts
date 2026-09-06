import { NextResponse } from "next/server";
import { QualityTrendQuerySchema, qualityClientService } from "@/features/quality";

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const parseResult = QualityTrendQuerySchema.safeParse({
      model: searchParams.get("model") || undefined,
      days: searchParams.get("days") || undefined,
    });

    if (!parseResult.success) {
      return NextResponse.json(
        { error: "Invalid query parameters", details: parseResult.error.format() },
        { status: 400 }
      );
    }

    const { model, days } = parseResult.data;
    const data = await qualityClientService.getQualityTrend(model, days);
    return NextResponse.json(data);
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || "Failed to fetch quality trend" },
      { status: 500 }
    );
  }
}
