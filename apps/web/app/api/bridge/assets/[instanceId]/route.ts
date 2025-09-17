import { NextRequest, NextResponse } from "next/server";
import { getProjectDoc } from "@/lib/project-doc";

export async function GET(
  req: NextRequest,
  { params }: { params: { instanceId: string } },
) {
  const projectId = new URL(req.url).searchParams.get("projectId") || "";
  const { instanceId } = params;
  const doc = await getProjectDoc(projectId);
  // Try instances first
  const hit =
    (doc?.instances || []).find((i: any) => i.id === instanceId) ||
    (doc?.libraries?.components || []).find(
      (c: any) => c.id === instanceId || c.part_number === instanceId,
    );
  if (!hit)
    return NextResponse.json(
      { id: instanceId, name: instanceId },
      { status: 200 },
    );
  return NextResponse.json(hit);
}
