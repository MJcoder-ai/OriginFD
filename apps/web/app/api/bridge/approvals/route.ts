import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  const body = await request.json();
  const status = body.approved ? "approved" : "rejected";
  return NextResponse.json({ project_id: body.project_id, status });
}
