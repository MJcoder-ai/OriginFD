import { NextRequest, NextResponse } from 'next/server'
import { findDocument } from '../../shared-data'

// Legacy static mock documents for backward compatibility
const legacyMockDocuments: { [key: string]: any } = {
  // New UUID-based project IDs
  'proj_550e8400-e29b-41d4-a716-446655440001': {
    $schema: 'https://odl-sd.org/schemas/v4.1/document.json',
    schema_version: '4.1',
    meta: {
      project: 'Solar Farm Arizona Phase 1',
      domain: 'PV',
      scale: 'UTILITY',
      units: {
        system: 'SI',
        currency: 'USD',
        coordinate_system: 'EPSG:4326',
      },
      timestamps: {
        created_at: '2024-01-15T10:30:00Z',
        updated_at: '2024-01-20T15:45:00Z',
      },
      versioning: {
        document_version: '4.1.0',
        content_hash: 'sha256:abc123',
      },
    },
    hierarchy: {
      type: 'PORTFOLIO',
      id: 'portfolio-1',
      children: [],
      portfolio: {
        id: 'portfolio-1',
        name: 'Solar Farm Arizona Phase 1',
        total_capacity_gw: 50.0,
        description: 'Large-scale utility solar installation in Arizona',
        location: 'Arizona, USA',
        regions: {},
      }
    },
    requirements: {
      functional: {
        capacity_kw: 50000,
        annual_generation_kwh: 125000000,
      },
      technical: {
        grid_connection: true,
      },
    },
    libraries: {
      components: [
        {
          id: 'pv-module-1',
          category: 'PV_MODULE',
          brand: 'Solar Tech',
          part_number: 'ST-400W-MONO',
          rating_w: 400,
          quantity: 125000,
          status: 'selected',
          placement: {
            location: 'Main Field Array',
          },
        },
        {
          id: 'inverter-1',
          category: 'INVERTER',
          brand: 'Power Systems Inc',
          part_number: 'PSI-2500-GRID',
          rating_w: 2500000,
          quantity: 20,
          status: 'selected',
          placement: {
            location: 'Inverter Building',
          },
        }
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
  },
  'proj_550e8400-e29b-41d4-a716-446655440002': {
    $schema: 'https://odl-sd.org/schemas/v4.1/document.json',
    schema_version: '4.1',
    meta: {
      project: 'Commercial BESS Installation',
      domain: 'BESS',
      scale: 'COMMERCIAL',
      units: {
        system: 'SI',
        currency: 'USD',
        coordinate_system: 'EPSG:4326',
      },
      timestamps: {
        created_at: '2024-01-18T09:15:00Z',
        updated_at: '2024-01-18T09:15:00Z',
      },
      versioning: {
        document_version: '4.1.0',
        content_hash: 'sha256:def456',
      },
    },
    hierarchy: {
      type: 'PORTFOLIO',
      id: 'portfolio-2',
      children: [],
      portfolio: {
        id: 'portfolio-2',
        name: 'Commercial BESS Installation',
        total_capacity_gw: 0.001,
        description: 'Commercial battery energy storage system',
        location: 'California, USA',
        regions: {},
      }
    },
    requirements: {
      functional: {
        capacity_kw: 1000,
        annual_generation_kwh: 0,
      },
      technical: {
        grid_connection: true,
      },
    },
    libraries: {
      components: [
        {
          id: 'battery-1',
          category: 'BATTERY',
          brand: 'Energy Storage Co',
          part_number: 'ESC-100kWh-LiFePO4',
          rating_w: 100000,
          quantity: 10,
          status: 'selected',
          placement: {
            location: 'Battery Container',
          },
        }
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
  },
  'proj_550e8400-e29b-41d4-a716-446655440003': {
    $schema: 'https://odl-sd.org/schemas/v4.1/document.json',
    schema_version: '4.1',
    meta: {
      project: 'Hybrid Microgrid Campus',
      domain: 'HYBRID',
      scale: 'INDUSTRIAL',
      units: {
        system: 'SI',
        currency: 'USD',
        coordinate_system: 'EPSG:4326',
      },
      timestamps: {
        created_at: '2024-01-22T14:20:00Z',
        updated_at: '2024-01-23T11:30:00Z',
      },
      versioning: {
        document_version: '4.1.0',
        content_hash: 'sha256:ghi789',
      },
    },
    hierarchy: {
      type: 'PORTFOLIO',
      id: 'portfolio-3',
      children: [],
      portfolio: {
        id: 'portfolio-3',
        name: 'Hybrid Microgrid Campus',
        total_capacity_gw: 0.005,
        description: 'Combined solar and battery system for industrial campus',
        location: 'Texas, USA',
        regions: {},
      }
    },
    requirements: {
      functional: {
        capacity_kw: 5000,
        annual_generation_kwh: 8000000,
      },
      technical: {
        grid_connection: true,
      },
    },
    libraries: {
      components: [
        {
          id: 'pv-module-hybrid-1',
          category: 'PV_MODULE',
          brand: 'Solar Tech',
          part_number: 'ST-400W-MONO',
          rating_w: 400,
          quantity: 12500,
          status: 'selected',
          placement: {
            location: 'Rooftop Array',
          },
        },
        {
          id: 'battery-hybrid-1',
          category: 'BATTERY',
          brand: 'Energy Storage Co',
          part_number: 'ESC-50kWh-LiFePO4',
          rating_w: 50000,
          quantity: 20,
          status: 'selected',
          placement: {
            location: 'Equipment Room',
          },
        }
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
  },
  // Legacy numeric ID documents for backward compatibility
  '1': {
    $schema: 'https://odl-sd.org/schemas/v4.1/document.json',
    schema_version: '4.1',
    meta: {
      project: 'Solar Farm Arizona Phase 1',
      domain: 'PV',
      scale: 'UTILITY',
      units: {
        system: 'SI',
        currency: 'USD',
        coordinate_system: 'EPSG:4326',
      },
      timestamps: {
        created_at: '2024-01-15T10:30:00Z',
        updated_at: '2024-01-20T15:45:00Z',
      },
      versioning: {
        document_version: '4.1.0',
        content_hash: 'sha256:abc123',
      },
    },
    hierarchy: {
      type: 'PORTFOLIO',
      id: 'portfolio-1',
      children: [],
      portfolio: {
        id: 'portfolio-1',
        name: 'Solar Farm Arizona Phase 1',
        total_capacity_gw: 50.0,
        description: 'Large-scale utility solar installation in Arizona',
        location: 'Arizona, USA',
        regions: {},
      }
    },
    requirements: {
      functional: {
        capacity_kw: 50000,
        annual_generation_kwh: 125000000,
      },
      technical: {
        grid_connection: true,
      },
    },
    libraries: {
      components: [
        {
          id: 'pv-module-1',
          category: 'PV_MODULE',
          brand: 'Solar Tech',
          part_number: 'ST-400W-MONO',
          rating_w: 400,
          quantity: 125000,
          status: 'selected',
          placement: {
            location: 'Main Field Array',
          },
        },
        {
          id: 'inverter-1',
          category: 'INVERTER',
          brand: 'Power Systems Inc',
          part_number: 'PSI-2500-GRID',
          rating_w: 2500000,
          quantity: 20,
          status: 'selected',
          placement: {
            location: 'Inverter Building',
          },
        }
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
  },
  '2': {
    $schema: 'https://odl-sd.org/schemas/v4.1/document.json',
    schema_version: '4.1',
    meta: {
      project: 'Commercial BESS Installation',
      domain: 'BESS',
      scale: 'COMMERCIAL',
      units: {
        system: 'SI',
        currency: 'USD',
        coordinate_system: 'EPSG:4326',
      },
      timestamps: {
        created_at: '2024-01-18T09:15:00Z',
        updated_at: '2024-01-18T09:15:00Z',
      },
      versioning: {
        document_version: '4.1.0',
        content_hash: 'sha256:def456',
      },
    },
    hierarchy: {
      type: 'PORTFOLIO',
      id: 'portfolio-2',
      children: [],
      portfolio: {
        id: 'portfolio-2',
        name: 'Commercial BESS Installation',
        total_capacity_gw: 0.001,
        description: 'Commercial battery energy storage system',
        location: 'California, USA',
        regions: {},
      }
    },
    requirements: {
      functional: {
        capacity_kw: 1000,
        annual_generation_kwh: 0, // BESS doesn't generate
      },
      technical: {
        grid_connection: true,
      },
    },
    libraries: {
      components: [
        {
          id: 'battery-1',
          category: 'BATTERY',
          brand: 'Energy Storage Co',
          part_number: 'ESC-100kWh-LiFePO4',
          rating_w: 100000,
          quantity: 10,
          status: 'selected',
          placement: {
            location: 'Battery Container',
          },
        }
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
  },
  '3': {
    $schema: 'https://odl-sd.org/schemas/v4.1/document.json',
    schema_version: '4.1',
    meta: {
      project: 'Hybrid Microgrid Campus',
      domain: 'HYBRID',
      scale: 'INDUSTRIAL',
      units: {
        system: 'SI',
        currency: 'USD',
        coordinate_system: 'EPSG:4326',
      },
      timestamps: {
        created_at: '2024-01-22T14:20:00Z',
        updated_at: '2024-01-23T11:30:00Z',
      },
      versioning: {
        document_version: '4.1.0',
        content_hash: 'sha256:ghi789',
      },
    },
    hierarchy: {
      type: 'PORTFOLIO',
      id: 'portfolio-3',
      children: [],
      portfolio: {
        id: 'portfolio-3',
        name: 'Hybrid Microgrid Campus',
        total_capacity_gw: 0.005,
        description: 'Combined solar and battery system for industrial campus',
        location: 'Texas, USA',
        regions: {},
      }
    },
    requirements: {
      functional: {
        capacity_kw: 5000,
        annual_generation_kwh: 8000000,
      },
      technical: {
        grid_connection: true,
      },
    },
    libraries: {
      components: [
        {
          id: 'pv-module-hybrid-1',
          category: 'PV_MODULE',
          brand: 'Solar Tech',
          part_number: 'ST-400W-MONO',
          rating_w: 400,
          quantity: 12500,
          status: 'selected',
          placement: {
            location: 'Rooftop Array',
          },
        },
        {
          id: 'battery-hybrid-1',
          category: 'BATTERY',
          brand: 'Energy Storage Co',
          part_number: 'ESC-50kWh-LiFePO4',
          rating_w: 50000,
          quantity: 20,
          status: 'selected',
          placement: {
            location: 'Equipment Room',
          },
        }
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
  }
}

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const { id } = params
  
  console.log('Fetching document with ID:', id)
  
  // First, try to find document in shared data store (includes newly created documents)
  let document = findDocument(id)
  
  if (document) {
    console.log('Found document in shared data:', document)
    // If it's a simple document from shared data, wrap in ODL format
    if (!document.$schema) {
      return NextResponse.json({
        $schema: 'https://odl-sd.org/schemas/v4.1/document.json',
        schema_version: '4.1',
        meta: {
          project: document.project_name,
          domain: document.domain,
          scale: document.scale,
          units: {
            system: 'SI',
            currency: 'USD',
            coordinate_system: 'EPSG:4326',
          },
          timestamps: {
            created_at: document.created_at,
            updated_at: document.updated_at,
          },
          versioning: {
            document_version: '4.1.0',
            content_hash: document.content_hash,
          },
        },
        hierarchy: {
          type: 'PORTFOLIO',
          id: `portfolio-${document.project_id}`,
          children: [],
          portfolio: {
            id: `portfolio-${document.project_id}`,
            name: document.project_name,
            total_capacity_gw: 0.001,
            description: document.document_data?.description || `${document.project_name} project document`,
            location: document.document_data?.location || 'TBD',
            regions: {},
          }
        },
        requirements: {
          functional: {
            capacity_kw: document.document_data?.capacity_kw || 1000,
            annual_generation_kwh: document.document_data?.annual_generation_kwh || 0,
          },
          technical: {
            grid_connection: true,
          },
        },
        libraries: {
          components: document.document_data?.components || [],
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
      })
    } else {
      // Already in ODL format
      return NextResponse.json(document)
    }
  }
  
  // Fall back to legacy mock documents for backward compatibility
  if (id.includes('-main')) {
    // New format: project-id-main (primary document)
    const projectId = id.replace('-main', '')
    document = legacyMockDocuments[projectId]
    console.log('Looking for primary document for project:', projectId)
  } else if (id.includes('-')) {
    // New format: project-id-document-uuid
    const projectId = id.split('-')[0]
    document = legacyMockDocuments[projectId]
    console.log('Looking for document for project:', projectId)
  } else {
    // Legacy format: project-id only
    document = legacyMockDocuments[id]
    console.log('Looking for legacy document:', id)
  }
  
  if (!document) {
    console.log('Document not found:', id)
    return NextResponse.json(
      { error: 'Document not found' },
      { status: 404 }
    )
  }
  
  console.log('Found legacy document for project:', document.meta?.project || 'unknown')
  return NextResponse.json(document)
}