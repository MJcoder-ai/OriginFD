import { NextRequest, NextResponse } from "next/server";

export async function GET(
  _req: NextRequest,
  { params }: { params: { id: string } },
) {
  const { id } = params;
  // Minimal hierarchical buckets for sidebar tree; backend can later materialize full graph
  return NextResponse.json({
    project_id: id,
    nodes: [
      {
        id: "canvases",
        label: "Canvases",
        children: [
          { id: "sld-mv", label: "SLD (MV)" },
          { id: "sld-dc", label: "SLD (DC Strings)" },
          { id: "site-layout", label: "Site Layout" },
        ],
      },
      { id: "models", label: "Models" },
      { id: "documents", label: "Documents" },
      { id: "reviews", label: "Reviews & Approvals" },
    ],
  });
}
