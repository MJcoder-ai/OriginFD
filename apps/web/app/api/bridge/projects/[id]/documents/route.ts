import { NextRequest, NextResponse } from 'next/server'

// Mock documents associated with specific projects
// Document ID format: {project-id}-{document-uuid}
const projectDocuments: { [projectId: string]: any[] } = {
  // New UUID-based project documents
  'proj_550e8400-e29b-41d4-a716-446655440001': [
    {
      id: 'proj_550e8400-e29b-41d4-a716-446655440001-main',
      project_id: 'proj_550e8400-e29b-41d4-a716-446655440001',
      document_type: 'ODL_SD',
      is_primary: true,
      name: 'Main System Document',
      created_at: '2024-01-15T10:30:00Z',
      updated_at: '2024-01-20T15:45:00Z'
    }
  ],
  'proj_550e8400-e29b-41d4-a716-446655440002': [
    {
      id: 'proj_550e8400-e29b-41d4-a716-446655440002-main',
      project_id: 'proj_550e8400-e29b-41d4-a716-446655440002',
      document_type: 'ODL_SD',
      is_primary: true,
      name: 'Main System Document',
      created_at: '2024-01-18T09:15:00Z',
      updated_at: '2024-01-18T09:15:00Z'
    }
  ],
  'proj_550e8400-e29b-41d4-a716-446655440003': [
    {
      id: 'proj_550e8400-e29b-41d4-a716-446655440003-main',
      project_id: 'proj_550e8400-e29b-41d4-a716-446655440003',
      document_type: 'ODL_SD',
      is_primary: true,
      name: 'Main System Document',
      created_at: '2024-01-22T14:20:00Z',
      updated_at: '2024-01-23T11:30:00Z'
    }
  ],
  // Legacy project documents for backward compatibility
  '1': [
    {
      id: '1-main',
      project_id: '1',
      document_type: 'ODL_SD',
      is_primary: true,
      name: 'Main System Document (Legacy)',
      created_at: '2024-01-15T10:30:00Z',
      updated_at: '2024-01-20T15:45:00Z'
    }
  ],
  '2': [
    {
      id: '2-main',
      project_id: '2',
      document_type: 'ODL_SD',
      is_primary: true,
      name: 'Main System Document (Legacy)',
      created_at: '2024-01-18T09:15:00Z',
      updated_at: '2024-01-18T09:15:00Z'
    }
  ],
  '3': [
    {
      id: '3-main',
      project_id: '3',
      document_type: 'ODL_SD',
      is_primary: true,
      name: 'Main System Document (Legacy)',
      created_at: '2024-01-22T14:20:00Z',
      updated_at: '2024-01-23T11:30:00Z'
    }
  ]
}

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const { id: projectId } = params

  console.log('Fetching documents for project:', projectId)

  // Find documents for this project
  const documents = projectDocuments[projectId] || []

  console.log('Found', documents.length, 'documents for project', projectId)
  return NextResponse.json(documents)
}