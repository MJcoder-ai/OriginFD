import { NextRequest, NextResponse } from "next/server";
import { findProject } from "../../shared-data";

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } },
) {
  const { id } = params;

  console.log("Fetching project with ID:", id);

  // Find project using shared data
  const project = findProject(id);

  if (!project) {
    console.log("Project not found:", id);
    return NextResponse.json({ error: "Project not found" }, { status: 404 });
  }

  console.log("Found project:", project);
  return NextResponse.json(project);
}
