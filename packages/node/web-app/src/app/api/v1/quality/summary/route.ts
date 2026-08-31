import { NextResponse } from "next/server";
import { QualitySummaryQuerySchema, qualityClientService } from "@/features/quality";

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const parseResult = QualitySummaryQuerySchema.safeParse({
      model: searchParams.get("model") || undefined,
      time_range: searchParams.get("time_range") || undefined,
      service: searchParams.get("service") || undefined,
    });

    if (!parseResult.success) {
      return NextResponse.json(
        { error: "Invalid query parameters", details: parseResult.error.format() },
        { status: 400 }
      );
    }

    const { model, time_range, service } = parseResult.data;
    const data = await qualityClientService.getQualitySummary(model, time_range, service);
    return NextResponse.json(data);
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || "Failed to fetch quality summary" },
      { status: 500 }
    );
  }
}
