import { NextRequest, NextResponse } from 'next/server'

// Mock projects data
const mockProjects = [
  {
    id: '1',
    project_name: 'Solar Farm Arizona Phase 1',
    domain: 'PV',
    scale: 'UTILITY',
    current_version: 3,
    content_hash: 'sha256:abc123',
    is_active: true,
    created_at: '2024-01-15T10:30:00Z',
    updated_at: '2024-01-20T15:45:00Z',
  },
  {
    id: '2',
    project_name: 'Commercial BESS Installation',
    domain: 'BESS',
    scale: 'COMMERCIAL',
    current_version: 1,
    content_hash: 'sha256:def456',
    is_active: true,
    created_at: '2024-01-18T09:15:00Z',
    updated_at: '2024-01-18T09:15:00Z',
  },
  {
    id: '3',
    project_name: 'Hybrid Microgrid Campus',
    domain: 'HYBRID',
    scale: 'INDUSTRIAL',
    current_version: 2,
    content_hash: 'sha256:ghi789',
    is_active: true,
    created_at: '2024-01-22T14:20:00Z',
    updated_at: '2024-01-23T11:30:00Z',
  },
]

export async function GET() {
  console.log('Fetching projects list:', mockProjects.length, 'projects')
  return NextResponse.json(mockProjects)
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    // Generate a new project ID
    const newId = String(mockProjects.length + 1)
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
    
    // Add to mock data
    mockProjects.push(newProject)
    
    // Simulate successful creation
    return NextResponse.json(newProject, { status: 201 })
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to create project' },
      { status: 500 }
    )
  }
}