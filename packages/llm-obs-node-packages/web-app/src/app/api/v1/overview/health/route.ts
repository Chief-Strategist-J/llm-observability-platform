import { NextResponse } from "next/server";
import { overviewClientService } from "@/features/overview";

export async function GET() {
  try {
    const data = await overviewClientService.getSystemHealth();
    return NextResponse.json(data);
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || "Failed to fetch system health status" },
      { status: 500 }
    );
  }
}
