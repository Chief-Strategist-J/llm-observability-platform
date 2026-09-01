import { NextResponse } from "next/server";
import { tracesClientService } from "@/features/traces";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ traceId: string }> }
) {
  try {
    const { traceId } = await params;
    const data = await tracesClientService.getTraceDetail(traceId);
    if (!data) {
      return NextResponse.json({ error: "Trace detail not found" }, { status: 404 });
    }
    return NextResponse.json(data);
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || "Failed to fetch trace detail" },
      { status: 500 }
    );
  }
}
