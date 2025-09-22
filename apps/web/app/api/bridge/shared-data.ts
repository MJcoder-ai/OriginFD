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

interface DocumentVersionSnapshot {
  version_number: number;
  content_hash: string;
  change_summary: string;
  created_by: string;
  created_at: string;
  patch_operations_count: number;
  document: any;
}

const createOdlDocumentSnapshot = ({
  documentId,
  projectName,
  domain,
  scale,
  createdAt,
  updatedAt,
  contentHash,
  versionNumber,
  capacityKw,
  annualGenerationKwh,
  modules,
  inverters,
  location,
}: {
  documentId: string;
  projectName: string;
  domain: string;
  scale: string;
  createdAt: string;
  updatedAt: string;
  contentHash: string;
  versionNumber: number;
  capacityKw: number;
  annualGenerationKwh: number;
  modules: number;
  inverters: number;
  location: string;
}) => ({
  id: documentId,
  $schema: "https://odl-sd.org/schemas/v4.1/document.json",
  schema_version: "4.1",
  meta: {
    project: projectName,
    domain,
    scale,
    units: {
      system: "SI",
      currency: "USD",
      coordinate_system: "EPSG:4326",
    },
    timestamps: {
      created_at: createdAt,
      updated_at: updatedAt,
    },
    versioning: {
      document_version: `4.1.${versionNumber}`,
      content_hash: contentHash,
    },
  },
  hierarchy: {
    type: "PORTFOLIO",
    id: `portfolio-${documentId}`,
    children: [],
    portfolio: {
      id: `portfolio-${documentId}`,
      name: projectName,
      total_capacity_gw: capacityKw / 1000,
      description: `${projectName} system document`,
      location,
      regions: {},
    },
  },
  requirements: {
    functional: {
      capacity_kw: capacityKw,
      annual_generation_kwh: annualGenerationKwh,
    },
    technical: {
      grid_connection: true,
    },
  },
  libraries: {
    components: [
      {
        id: `${documentId}-pv-array`,
        category: "pv_array",
        brand: "Origin Solar",
        part_number: "PV-400W",
        rating_w: 400,
        quantity: modules,
        status: "selected",
        placement: {
          location: "Array Block A1",
        },
      },
      {
        id: `${documentId}-inverter`,
        category: "inverter",
        brand: "Origin Power",
        part_number: "INV-250KW",
        rating_w: 250000,
        quantity: inverters,
        status: "selected",
        placement: {
          location: "Inverter Building",
        },
      },
    ],
  },
  instances: [],
  connections: [],
  analysis: [],
  audit: [],
  data_management: {
    partitioning_enabled: false,
    external_refs_enabled: false,
    streaming_enabled: false,
    max_document_size_mb: 100,
  },
});

const solarDocumentId = "proj_550e8400-e29b-41d4-a716-446655440001-main";
const bessDocumentId = "proj_550e8400-e29b-41d4-a716-446655440002-main";
const hybridDocumentId = "proj_550e8400-e29b-41d4-a716-446655440003-main";

export const mockDocumentVersionHistory: Record<
  string,
  DocumentVersionSnapshot[]
> = {
  [solarDocumentId]: [
    {
      version_number: 1,
      content_hash: "sha256:solar-v1",
      change_summary: "Initial baseline imported from EPC planning tool",
      created_by: "alex.johnson",
      created_at: "2024-01-10T09:00:00Z",
      patch_operations_count: 0,
      document: createOdlDocumentSnapshot({
        documentId: solarDocumentId,
        projectName: "Solar Farm Arizona Phase 1",
        domain: "PV",
        scale: "UTILITY",
        createdAt: "2024-01-10T09:00:00Z",
        updatedAt: "2024-01-10T09:00:00Z",
        contentHash: "sha256:solar-v1",
        versionNumber: 1,
        capacityKw: 95000,
        annualGenerationKwh: 118000000,
        modules: 3800,
        inverters: 90,
        location: "Arizona, USA",
      }),
    },
    {
      version_number: 2,
      content_hash: "sha256:solar-v2",
      change_summary: "Updated DC design after geotechnical survey",
      created_by: "maria.lopez",
      created_at: "2024-01-14T16:30:00Z",
      patch_operations_count: 12,
      document: createOdlDocumentSnapshot({
        documentId: solarDocumentId,
        projectName: "Solar Farm Arizona Phase 1",
        domain: "PV",
        scale: "UTILITY",
        createdAt: "2024-01-10T09:00:00Z",
        updatedAt: "2024-01-14T16:30:00Z",
        contentHash: "sha256:solar-v2",
        versionNumber: 2,
        capacityKw: 98000,
        annualGenerationKwh: 121500000,
        modules: 3900,
        inverters: 95,
        location: "Arizona, USA",
      }),
    },
    {
      version_number: 3,
      content_hash: "sha256:solar-v3",
      change_summary: "Incorporated utility feedback and interconnection limits",
      created_by: "alex.johnson",
      created_at: "2024-01-20T15:45:00Z",
      patch_operations_count: 8,
      document: createOdlDocumentSnapshot({
        documentId: solarDocumentId,
        projectName: "Solar Farm Arizona Phase 1",
        domain: "PV",
        scale: "UTILITY",
        createdAt: "2024-01-10T09:00:00Z",
        updatedAt: "2024-01-20T15:45:00Z",
        contentHash: "sha256:solar-v3",
        versionNumber: 3,
        capacityKw: 100000,
        annualGenerationKwh: 125000000,
        modules: 4000,
        inverters: 100,
        location: "Arizona, USA",
      }),
    },
  ],
  [bessDocumentId]: [
    {
      version_number: 1,
      content_hash: "sha256:bess-v1",
      change_summary: "Initial BESS sizing and site layout",
      created_by: "dave.smith",
      created_at: "2024-01-18T09:15:00Z",
      patch_operations_count: 0,
      document: createOdlDocumentSnapshot({
        documentId: bessDocumentId,
        projectName: "Commercial BESS Installation",
        domain: "BESS",
        scale: "COMMERCIAL",
        createdAt: "2024-01-18T09:15:00Z",
        updatedAt: "2024-01-18T09:15:00Z",
        contentHash: "sha256:bess-v1",
        versionNumber: 1,
        capacityKw: 900,
        annualGenerationKwh: 0,
        modules: 120,
        inverters: 6,
        location: "California, USA",
      }),
    },
    {
      version_number: 2,
      content_hash: "sha256:bess-v2",
      change_summary: "Adjusted inverter selection for improved round-trip efficiency",
      created_by: "dave.smith",
      created_at: "2024-01-19T11:45:00Z",
      patch_operations_count: 6,
      document: createOdlDocumentSnapshot({
        documentId: bessDocumentId,
        projectName: "Commercial BESS Installation",
        domain: "BESS",
        scale: "COMMERCIAL",
        createdAt: "2024-01-18T09:15:00Z",
        updatedAt: "2024-01-19T11:45:00Z",
        contentHash: "sha256:bess-v2",
        versionNumber: 2,
        capacityKw: 1000,
        annualGenerationKwh: 0,
        modules: 130,
        inverters: 8,
        location: "California, USA",
      }),
    },
  ],
  [hybridDocumentId]: [
    {
      version_number: 1,
      content_hash: "sha256:hybrid-v1",
      change_summary: "Baseline hybrid layout for campus microgrid",
      created_by: "sarah.lee",
      created_at: "2024-01-22T14:20:00Z",
      patch_operations_count: 0,
      document: createOdlDocumentSnapshot({
        documentId: hybridDocumentId,
        projectName: "Hybrid Microgrid Campus",
        domain: "HYBRID",
        scale: "INDUSTRIAL",
        createdAt: "2024-01-22T14:20:00Z",
        updatedAt: "2024-01-22T14:20:00Z",
        contentHash: "sha256:hybrid-v1",
        versionNumber: 1,
        capacityKw: 4200,
        annualGenerationKwh: 7200000,
        modules: 1600,
        inverters: 40,
        location: "Texas, USA",
      }),
    },
    {
      version_number: 2,
      content_hash: "sha256:hybrid-v2",
      change_summary: "Integrated new battery blocks for peak shaving",
      created_by: "sarah.lee",
      created_at: "2024-01-23T11:30:00Z",
      patch_operations_count: 9,
      document: createOdlDocumentSnapshot({
        documentId: hybridDocumentId,
        projectName: "Hybrid Microgrid Campus",
        domain: "HYBRID",
        scale: "INDUSTRIAL",
        createdAt: "2024-01-22T14:20:00Z",
        updatedAt: "2024-01-23T11:30:00Z",
        contentHash: "sha256:hybrid-v2",
        versionNumber: 2,
        capacityKw: 5000,
        annualGenerationKwh: 8000000,
        modules: 1750,
        inverters: 45,
        location: "Texas, USA",
      }),
    },
  ],
};

export function getDocumentVersionHistory(documentId: string) {
  return mockDocumentVersionHistory[documentId] || [];
}

export function getDocumentVersionSnapshot(
  documentId: string,
  versionNumber: number,
) {
  const history = getDocumentVersionHistory(documentId);
  return history.find((snapshot) => snapshot.version_number === versionNumber);
}

export function getLatestDocumentSnapshot(documentId: string) {
  const history = getDocumentVersionHistory(documentId);
  if (history.length === 0) {
    return undefined;
  }
  return history[history.length - 1];
}

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

// Simple notification store used by API routes
export let mockNotifications: any[] = [];

export function addNotification(notification: any) {
  mockNotifications.push(notification);
  return notification;
}

export function getNotifications() {
  return mockNotifications;
}
