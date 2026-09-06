import { NextResponse } from "next/server";
import { ModelQualityQuerySchema, qualityClientService } from "@/features/quality";

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const parseResult = ModelQualityQuerySchema.safeParse({
      time_range: searchParams.get("time_range") || undefined,
    });

    if (!parseResult.success) {
      return NextResponse.json(
        { error: "Invalid query parameters", details: parseResult.error.format() },
        { status: 400 }
      );
    }

    const { time_range } = parseResult.data;
    const data = await qualityClientService.getModelBreakdown(time_range);
    return NextResponse.json(data);
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || "Failed to fetch model quality breakdown" },
      { status: 500 }
    );
  }
}
