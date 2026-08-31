import { NextResponse } from "next/server";
import { TraceListQuerySchema, tracesClientService } from "@/features/traces";

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const parseResult = TraceListQuerySchema.safeParse({
      model: searchParams.get("model") || undefined,
      status: searchParams.get("status") || undefined,
      service: searchParams.get("service") || undefined,
      limit: searchParams.get("limit") || undefined,
    });

    if (!parseResult.success) {
      return NextResponse.json(
        { error: "Invalid query parameters", details: parseResult.error.format() },
        { status: 400 }
      );
    }

    const { model, status, service, limit } = parseResult.data;
    const data = await tracesClientService.listTraces(model, status, service, limit);
    return NextResponse.json(data);
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || "Failed to list trace summaries" },
      { status: 500 }
    );
  }
}
