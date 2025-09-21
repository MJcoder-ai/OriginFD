import { NextRequest, NextResponse } from "next/server";
import { getAllProjects, addProject, addDocument } from "../shared-data";

export async function GET() {
  const projects = getAllProjects();
  console.log("Fetching projects list:", projects.length, "projects");
  return NextResponse.json(projects);
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    const projectName = body.name ?? body.project_name ?? "New Project";
    const domain = body.domain ?? "PV";
    const scale = body.scale ?? "UTILITY";
    const now = new Date().toISOString();
    const projectId = `proj_${crypto.randomUUID()}`;
    const documentId = `${projectId}-main`;
    const contentHash = `sha256:${Math.random().toString(36).substring(2)}`;

    const newProject = {
      id: projectId,
      name: projectName,
      project_name: projectName,
      description: body.description ?? null,
      domain,
      scale,
      status: "draft" as const,
      display_status: "draft",
      completion_percentage: 0,
      location_name: body.location_name ?? null,
      total_capacity_kw: body.total_capacity_kw ?? null,
      tags: Array.isArray(body.tags) ? body.tags : [],
      owner_id: body.owner_id ?? "mock-user",
      current_version: 1,
      content_hash: contentHash,
      is_active: true,
      created_at: now,
      updated_at: now,
      initialization_task_id: null,
      document_id: documentId,
      document_hash: contentHash,
    };

    addProject(newProject);

    const newDocument = {
      id: documentId,
      project_id: projectId,
      project_name: projectName,
      domain,
      scale,
      current_version: 1,
      content_hash: contentHash,
      is_active: true,
      created_at: now,
      updated_at: now,
      document_data: {
        description: body.description ?? `${projectName} project document`,
        location: body.location_name ?? "TBD",
        status: "draft",
      },
    };

    addDocument(newDocument);

    return NextResponse.json(newProject, { status: 201 });
  } catch (error) {
    return NextResponse.json(
      { error: "Failed to create project" },
      { status: 500 },
    );
  }
}
