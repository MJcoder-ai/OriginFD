import { NextRequest, NextResponse } from 'next/server'
import { addProject, addDocument } from '../shared-data'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()

    // Generate UUID-format project ID (to match new format)
    const projectUuid = `proj_${Date.now()}-${Math.random().toString(36).substring(2, 15)}`
    const now = new Date().toISOString()
    const contentHash = `sha256:${Math.random().toString(36).substring(2)}`

    const newProject = {
      id: projectUuid,
      project_name: body.project_name,
      domain: body.domain,
      scale: body.scale,
      current_version: 1,
      content_hash: contentHash,
      is_active: true,
      created_at: now,
      updated_at: now,
    }

    // Create corresponding document
    const newDocument = {
      id: `${projectUuid}-main`,
      project_id: projectUuid,
      project_name: body.project_name,
      domain: body.domain,
      scale: body.scale,
      current_version: 1,
      content_hash: contentHash,
      is_active: true,
      created_at: now,
      updated_at: now,
      document_data: body.document_data || {
        description: `${body.project_name} project document`,
        location: 'TBD',
        status: 'draft'
      }
    }

    // Persist in mock data
    addProject(newProject)
    addDocument(newDocument)

    console.log('Created and persisted new project:', newProject)
    console.log('Created and persisted new document:', newDocument)

    // Return project with document reference
    return NextResponse.json({
      ...newProject,
      document_id: newDocument.id
    }, { status: 201 })
  } catch (error) {
    console.error('Error creating project:', error)
    return NextResponse.json(
      { error: 'Failed to create project' },
      { status: 500 }
    )
  }
}