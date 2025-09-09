import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    // Generate a new project ID
    const newId = String(Math.floor(Math.random() * 10000))
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
    
    console.log('Created new project:', newProject)
    
    // Simulate successful creation
    return NextResponse.json(newProject, { status: 201 })
  } catch (error) {
    console.error('Error creating project:', error)
    return NextResponse.json(
      { error: 'Failed to create project' },
      { status: 500 }
    )
  }
}