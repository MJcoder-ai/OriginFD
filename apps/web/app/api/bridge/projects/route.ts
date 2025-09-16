import { NextRequest, NextResponse } from 'next/server'
import { getAllProjects, addProject } from '../shared-data'

export async function GET() {
  const projects = getAllProjects()
  console.log('Fetching projects list:', projects.length, 'projects')
  return NextResponse.json(projects)
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()

    // Generate a new project ID using UUID format
    const newId = `proj_${crypto.randomUUID()}`
    const now = new Date().toISOString()

    const newProject = {
      id: newId,
      project_name: body.project_name,
      domain: body.domain,
      scale: body.scale,
      current_version: 1,
      content_hash: `sha256:${Math.random().toString(36).substring(2)}`,
      is_active: true,
      created_at: now,
      updated_at: now,
    }

    // Add to shared data store
    addProject(newProject)

    // Simulate successful creation
    return NextResponse.json(newProject, { status: 201 })
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to create project' },
      { status: 500 }
    )
  }
}