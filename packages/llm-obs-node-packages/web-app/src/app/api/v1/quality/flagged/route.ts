import { NextResponse } from "next/server";
import { FlaggedContentQuerySchema, qualityClientService } from "@/features/quality";

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const parseResult = FlaggedContentQuerySchema.safeParse({
      severity: searchParams.get("severity") || undefined,
      limit: searchParams.get("limit") || undefined,
    });

    if (!parseResult.success) {
      return NextResponse.json(
        { error: "Invalid query parameters", details: parseResult.error.format() },
        { status: 400 }
      );
    }

    const { severity, limit } = parseResult.data;
    const data = await qualityClientService.getFlaggedContent(severity, limit);
    return NextResponse.json(data);
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || "Failed to fetch flagged content alerts" },
      { status: 500 }
    );
  }
}
