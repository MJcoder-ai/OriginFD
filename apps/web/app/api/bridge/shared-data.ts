// Shared mock data store for all API endpoints
// Using UUID format to match database schema
export let mockProjects = [
  {
    id: 'proj_550e8400-e29b-41d4-a716-446655440001',
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
    id: 'proj_550e8400-e29b-41d4-a716-446655440002',
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
    id: 'proj_550e8400-e29b-41d4-a716-446655440003',
    project_name: 'Hybrid Microgrid Campus',
    domain: 'HYBRID',
    scale: 'INDUSTRIAL',
    current_version: 2,
    content_hash: 'sha256:ghi789',
    is_active: true,
    created_at: '2024-01-22T14:20:00Z',
    updated_at: '2024-01-23T11:30:00Z',
  },
  // Legacy IDs for backward compatibility during transition
  {
    id: '1',
    project_name: 'Solar Farm Arizona Phase 1 (Legacy)',
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
    project_name: 'Commercial BESS Installation (Legacy)',
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
    project_name: 'Hybrid Microgrid Campus (Legacy)',
    domain: 'HYBRID',
    scale: 'INDUSTRIAL',
    current_version: 2,
    content_hash: 'sha256:ghi789',
    is_active: true,
    created_at: '2024-01-22T14:20:00Z',
    updated_at: '2024-01-23T11:30:00Z',
  },
]

export function addProject(project: any) {
  mockProjects.push(project)
  return project
}

export function findProject(id: string) {
  return mockProjects.find(p => p.id === id)
}

export function getAllProjects() {
  return mockProjects
}

// Simple notification store used by API routes
export let mockNotifications: any[] = []

export function addNotification(notification: any) {
  mockNotifications.push(notification)
  return notification
}

export function getNotifications() {
  return mockNotifications
}