import { NextResponse } from "next/server";
import { HTTP_CONSTANTS } from "@observability/shared-infra";

export async function GET() {
  return NextResponse.json({
    status: HTTP_CONSTANTS.STATUS_SUCCESS,
    service: HTTP_CONSTANTS.SERVICE_NAME_WEB_APP,
    timestamp: new Date().toISOString(),
  });
}
