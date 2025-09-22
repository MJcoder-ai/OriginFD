// Shared mock data store for all API endpoints
// Using UUID format to match database schema
export let mockProjects = [
  {
    id: "proj_550e8400-e29b-41d4-a716-446655440001",
    project_name: "Solar Farm Arizona Phase 1",
    domain: "PV",
    scale: "UTILITY",
    current_version: 3,
    content_hash: "sha256:abc123",
    is_active: true,
    created_at: "2024-01-15T10:30:00Z",
    updated_at: "2024-01-20T15:45:00Z",
  },
  {
    id: "proj_550e8400-e29b-41d4-a716-446655440002",
    project_name: "Commercial BESS Installation",
    domain: "BESS",
    scale: "COMMERCIAL",
    current_version: 1,
    content_hash: "sha256:def456",
    is_active: true,
    created_at: "2024-01-18T09:15:00Z",
    updated_at: "2024-01-18T09:15:00Z",
  },
  {
    id: "proj_550e8400-e29b-41d4-a716-446655440003",
    project_name: "Hybrid Microgrid Campus",
    domain: "HYBRID",
    scale: "INDUSTRIAL",
    current_version: 2,
    content_hash: "sha256:ghi789",
    is_active: true,
    created_at: "2024-01-22T14:20:00Z",
    updated_at: "2024-01-23T11:30:00Z",
  },
  // Legacy IDs for backward compatibility during transition
  {
    id: "1",
    project_name: "Solar Farm Arizona Phase 1 (Legacy)",
    domain: "PV",
    scale: "UTILITY",
    current_version: 3,
    content_hash: "sha256:abc123",
    is_active: true,
    created_at: "2024-01-15T10:30:00Z",
    updated_at: "2024-01-20T15:45:00Z",
  },
  {
    id: "2",
    project_name: "Commercial BESS Installation (Legacy)",
    domain: "BESS",
    scale: "COMMERCIAL",
    current_version: 1,
    content_hash: "sha256:def456",
    is_active: true,
    created_at: "2024-01-18T09:15:00Z",
    updated_at: "2024-01-18T09:15:00Z",
  },
  {
    id: "3",
    project_name: "Hybrid Microgrid Campus (Legacy)",
    domain: "HYBRID",
    scale: "INDUSTRIAL",
    current_version: 2,
    content_hash: "sha256:ghi789",
    is_active: true,
    created_at: "2024-01-22T14:20:00Z",
    updated_at: "2024-01-23T11:30:00Z",
  },
];

export function addProject(project: any) {
  mockProjects.push(project);
  return project;
}

export function findProject(id: string) {
  return mockProjects.find((p) => p.id === id);
}

export function getAllProjects() {
  return mockProjects;
}

// Mock documents store - documents associated with projects
export let mockDocuments = [
  {
    id: "proj_550e8400-e29b-41d4-a716-446655440001-main",
    project_id: "proj_550e8400-e29b-41d4-a716-446655440001",
    project_name: "Solar Farm Arizona Phase 1",
    domain: "PV",
    scale: "UTILITY",
    current_version: 3,
    content_hash: "sha256:abc123",
    is_active: true,
    created_at: "2024-01-15T10:30:00Z",
    updated_at: "2024-01-20T15:45:00Z",
    document_data: {
      system_capacity: 100,
      location: "Arizona",
      modules: 4000,
      inverters: 100,
    },
    libraries: {
      components: [
        {
          id: "comp_001",
          part_number: "SPR-X22-370",
          brand: "SunPower",
          category: "pv_module",
          rating_w: 370,
          status: "selected",
          placement: { location: "Array Block A1" },
        },
        {
          id: "comp_002",
          part_number: "STP-25000TL-30",
          brand: "SMA",
          category: "inverter",
          rating_w: 25000,
          status: "selected",
          placement: { location: "Inverter Skid 1" },
        },
        {
          id: "comp_003",
          part_number: "SE-MTR240-0",
          brand: "SolarEdge",
          category: "monitoring",
          rating_w: 50,
          status: "selected",
          placement: { location: "Main Control Panel" },
        },
        {
          id: "comp_004",
          part_number: "OVR-PV-40-1000-P",
          brand: "ABB",
          category: "protection",
          rating_w: 1000,
          status: "selected",
          placement: { location: "DC Combiner Box" },
        },
        {
          id: "comp_005",
          part_number: "LG-NeON-2-385",
          brand: "LG",
          category: "pv_module",
          rating_w: 385,
          status: "candidate",
          placement: { location: "Array Block A2" },
        },
        {
          id: "comp_006",
          part_number: "SYMO-15000TL-10",
          brand: "Fronius",
          category: "inverter",
          rating_w: 15000,
          status: "candidate",
          placement: { location: "Inverter Skid 2" },
        },
      ],
    },
  },
  {
    id: "proj_550e8400-e29b-41d4-a716-446655440002-main",
    project_id: "proj_550e8400-e29b-41d4-a716-446655440002",
    project_name: "Commercial BESS Installation",
    domain: "BESS",
    scale: "COMMERCIAL",
    current_version: 1,
    content_hash: "sha256:def456",
    is_active: true,
    created_at: "2024-01-18T09:15:00Z",
    updated_at: "2024-01-18T09:15:00Z",
    document_data: {
      battery_capacity: 500,
      location: "California",
      batteries: 50,
      inverters: 10,
    },
  },
  {
    id: "proj_550e8400-e29b-41d4-a716-446655440003-main",
    project_id: "proj_550e8400-e29b-41d4-a716-446655440003",
    project_name: "Hybrid Microgrid Campus",
    domain: "HYBRID",
    scale: "INDUSTRIAL",
    current_version: 2,
    content_hash: "sha256:ghi789",
    is_active: true,
    created_at: "2024-01-22T14:20:00Z",
    updated_at: "2024-01-23T11:30:00Z",
    document_data: {
      pv_capacity: 50,
      battery_capacity: 200,
      location: "Texas",
      modules: 2000,
      batteries: 25,
    },
  },
  // Legacy documents for backward compatibility
  {
    id: "1",
    project_id: "1",
    project_name: "Solar Farm Arizona Phase 1 (Legacy)",
    domain: "PV",
    scale: "UTILITY",
    current_version: 3,
    content_hash: "sha256:abc123",
    is_active: true,
    created_at: "2024-01-15T10:30:00Z",
    updated_at: "2024-01-20T15:45:00Z",
    document_data: {
      system_capacity: 100,
      location: "Arizona",
      modules: 4000,
      inverters: 100,
    },
  },
  {
    id: "2",
    project_id: "2",
    project_name: "Commercial BESS Installation (Legacy)",
    domain: "BESS",
    scale: "COMMERCIAL",
    current_version: 1,
    content_hash: "sha256:def456",
    is_active: true,
    created_at: "2024-01-18T09:15:00Z",
    updated_at: "2024-01-18T09:15:00Z",
    document_data: {
      battery_capacity: 500,
      location: "California",
      batteries: 50,
      inverters: 10,
    },
  },
  {
    id: "3",
    project_id: "3",
    project_name: "Hybrid Microgrid Campus (Legacy)",
    domain: "HYBRID",
    scale: "INDUSTRIAL",
    current_version: 2,
    content_hash: "sha256:ghi789",
    is_active: true,
    created_at: "2024-01-22T14:20:00Z",
    updated_at: "2024-01-23T11:30:00Z",
    document_data: {
      pv_capacity: 50,
      battery_capacity: 200,
      location: "Texas",
      modules: 2000,
      batteries: 25,
    },
  },
];

export function addDocument(document: any) {
  mockDocuments.push(document);
  return document;
}

export function findDocument(id: string) {
  return mockDocuments.find((d) => d.id === id);
}

export function findDocumentsByProject(projectId: string) {
  return mockDocuments.filter((d) => d.project_id === projectId);
}

export function getAllDocuments() {
  return mockDocuments;
}

export function findPrimaryDocumentForProject(projectId: string) {
  const direct = mockDocuments.find((doc) => doc.project_id === projectId);
  if (direct) {
    return direct;
  }

  const candidates = [
    `${projectId}-main`,
    `${projectId}_main`,
    projectId,
  ];

  for (const candidate of candidates) {
    const match = mockDocuments.find((doc) => doc.id === candidate);
    if (match) {
      return match;
    }
  }

  return undefined;
}

export function addComponentsToProjectDocument(
  projectId: string,
  components: any[],
) {
  const document = findPrimaryDocumentForProject(projectId);
  if (!document) {
    return null;
  }

  if (!document.document_data) {
    document.document_data = {};
  }

  const docData = document.document_data as any;
  if (!Array.isArray(docData.components)) {
    docData.components = [];
  }

  docData.components.push(...components);

  document.libraries = {
    ...(document.libraries || {}),
    components: docData.components,
  };

  document.updated_at = new Date().toISOString();

  return {
    document,
    components: docData.components,
  };
}

// Simple notification store used by API routes
export let mockNotifications: any[] = [];

export function addNotification(notification: any) {
  mockNotifications.push(notification);
  return notification;
}

export function getNotifications() {
  return mockNotifications;
}
