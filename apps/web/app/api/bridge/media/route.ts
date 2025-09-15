import { NextRequest, NextResponse } from 'next/server'

interface MediaAsset {
  id: string
  component_id: string
  type: 'datasheet' | 'warranty' | 'installation' | 'faq' | 'certificate' | 'test_report' | 'image' | 'video' | 'other'
  name: string
  description?: string
  file_url: string
  file_size: number
  file_type: string
  checksum: string
  uploaded_by: string
  uploaded_at: string
  version: number
  is_active: boolean
  tags: string[]
  metadata: {
    pages?: number
    resolution?: string
    duration?: number
    language?: string
    [key: string]: any
  }
}

// Mock media assets for ODL-SD v4.1 components
const mockMediaAssets: MediaAsset[] = [
  {
    id: 'media_001',
    component_id: 'comp_001',
    type: 'datasheet',
    name: 'JinkoSolar_Tiger_Neo_535W_Datasheet.pdf',
    description: 'Technical datasheet for JinkoSolar Tiger Neo 535W PV Module',
    file_url: '/media/datasheets/JinkoSolar_Tiger_Neo_535W_Datasheet.pdf',
    file_size: 2456789,
    file_type: 'application/pdf',
    checksum: 'sha256:a1b2c3d4e5f6789012345678901234567890abcdef',
    uploaded_by: 'user_engineering_001',
    uploaded_at: '2025-01-15T10:30:00Z',
    version: 1,
    is_active: true,
    tags: ['datasheet', 'technical-specs', 'pv-module'],
    metadata: {
      pages: 4,
      language: 'en'
    }
  },
  {
    id: 'media_002',
    component_id: 'comp_001',
    type: 'certificate',
    name: 'JinkoSolar_IEC61215_Certificate.pdf',
    description: 'IEC 61215 Type Approval Certificate',
    file_url: '/media/certificates/JinkoSolar_IEC61215_Certificate.pdf',
    file_size: 1234567,
    file_type: 'application/pdf',
    checksum: 'sha256:b2c3d4e5f6789012345678901234567890abcdef1',
    uploaded_by: 'user_quality_001',
    uploaded_at: '2025-01-15T11:00:00Z',
    version: 1,
    is_active: true,
    tags: ['certificate', 'iec61215', 'compliance'],
    metadata: {
      pages: 6,
      language: 'en',
      expiry_date: '2028-01-15',
      issuing_body: 'TUV Rheinland'
    }
  },
  {
    id: 'media_003',
    component_id: 'comp_001',
    type: 'image',
    name: 'JinkoSolar_Module_Product_Photo.jpg',
    description: 'High-resolution product photograph',
    file_url: '/media/images/JinkoSolar_Module_Product_Photo.jpg',
    file_size: 856432,
    file_type: 'image/jpeg',
    checksum: 'sha256:c3d4e5f6789012345678901234567890abcdef12',
    uploaded_by: 'user_marketing_001',
    uploaded_at: '2025-01-15T12:15:00Z',
    version: 1,
    is_active: true,
    tags: ['product-photo', 'marketing', 'high-res'],
    metadata: {
      resolution: '3000x2000',
      color_profile: 'sRGB'
    }
  },
  {
    id: 'media_004',
    component_id: 'comp_001',
    type: 'installation',
    name: 'Installation_Guide_v2.1.pdf',
    description: 'Comprehensive installation guide and safety instructions',
    file_url: '/media/installation/Installation_Guide_v2.1.pdf',
    file_size: 3456789,
    file_type: 'application/pdf',
    checksum: 'sha256:d4e5f6789012345678901234567890abcdef123',
    uploaded_by: 'user_engineering_002',
    uploaded_at: '2025-01-20T09:45:00Z',
    version: 2,
    is_active: true,
    tags: ['installation', 'guide', 'safety'],
    metadata: {
      pages: 24,
      language: 'en',
      version_notes: 'Updated safety procedures and electrical diagrams'
    }
  },
  {
    id: 'media_005',
    component_id: 'comp_017',
    type: 'datasheet',
    name: 'ABB_TRIO_50kW_Datasheet.pdf',
    description: 'Technical datasheet for ABB TRIO-50.0-TL-OUTD String Inverter',
    file_url: '/media/datasheets/ABB_TRIO_50kW_Datasheet.pdf',
    file_size: 1876543,
    file_type: 'application/pdf',
    checksum: 'sha256:e5f6789012345678901234567890abcdef1234',
    uploaded_by: 'user_engineering_003',
    uploaded_at: '2025-01-18T14:20:00Z',
    version: 1,
    is_active: true,
    tags: ['datasheet', 'inverter', 'string-inverter'],
    metadata: {
      pages: 8,
      language: 'en'
    }
  },
  {
    id: 'media_006',
    component_id: 'comp_017',
    type: 'video',
    name: 'ABB_Installation_Video.mp4',
    description: 'Step-by-step installation demonstration video',
    file_url: '/media/videos/ABB_Installation_Video.mp4',
    file_size: 45678901,
    file_type: 'video/mp4',
    checksum: 'sha256:f6789012345678901234567890abcdef12345',
    uploaded_by: 'user_training_001',
    uploaded_at: '2025-01-22T16:30:00Z',
    version: 1,
    is_active: true,
    tags: ['installation', 'training', 'video-guide'],
    metadata: {
      duration: 1245, // seconds
      resolution: '1920x1080',
      codec: 'H.264'
    }
  }
]

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const componentId = searchParams.get('component_id')
    const type = searchParams.get('type')
    const activeOnly = searchParams.get('active_only') === 'true'

    let filteredAssets = mockMediaAssets

    if (componentId) {
      filteredAssets = filteredAssets.filter(asset => asset.component_id === componentId)
    }

    if (type) {
      filteredAssets = filteredAssets.filter(asset => asset.type === type)
    }

    if (activeOnly) {
      filteredAssets = filteredAssets.filter(asset => asset.is_active)
    }

    // Group by component for easier consumption
    const assetsByComponent = filteredAssets.reduce((acc, asset) => {
      if (!acc[asset.component_id]) {
        acc[asset.component_id] = []
      }
      acc[asset.component_id].push(asset)
      return acc
    }, {} as Record<string, MediaAsset[]>)

    const response = {
      total_assets: filteredAssets.length,
      assets: filteredAssets,
      assets_by_component: assetsByComponent,
      available_types: Array.from(new Set(mockMediaAssets.map(a => a.type))),
      statistics: {
        by_type: mockMediaAssets.reduce((acc, asset) => {
          acc[asset.type] = (acc[asset.type] || 0) + 1
          return acc
        }, {} as Record<string, number>),
        total_size: mockMediaAssets.reduce((sum, asset) => sum + asset.file_size, 0),
        active_assets: mockMediaAssets.filter(a => a.is_active).length,
        inactive_assets: mockMediaAssets.filter(a => !a.is_active).length
      }
    }

    console.log(`Fetching media assets: ${filteredAssets.length} found`)
    return NextResponse.json(response)
  } catch (error) {
    console.error('Error fetching media assets:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

export async function POST(request: NextRequest) {
  try {
    const assetData = await request.json()

    // In real implementation, this would:
    // 1. Upload file to cloud storage (AWS S3, Azure Blob, etc.)
    // 2. Calculate file checksum
    // 3. Extract metadata (page count, dimensions, etc.)
    // 4. Store asset record in database
    // 5. Create thumbnail/preview if applicable

    const newAsset: MediaAsset = {
      id: `media_${Date.now()}`,
      component_id: assetData.component_id,
      type: assetData.type,
      name: assetData.name,
      description: assetData.description,
      file_url: `/media/${assetData.type}s/${assetData.name}`, // Mock URL
      file_size: assetData.file_size || 1000000, // Mock size
      file_type: assetData.file_type || 'application/pdf',
      checksum: `sha256:${Date.now().toString(16)}`, // Mock checksum
      uploaded_by: assetData.uploaded_by || 'user_current',
      uploaded_at: new Date().toISOString(),
      version: 1,
      is_active: true,
      tags: assetData.tags || [],
      metadata: assetData.metadata || {}
    }

    mockMediaAssets.push(newAsset)
    console.log('Created new media asset:', newAsset.id, 'for component:', newAsset.component_id)

    return NextResponse.json({
      success: true,
      asset: newAsset,
      upload_info: {
        status: 'uploaded',
        processed: true,
        thumbnail_generated: newAsset.type === 'image' || newAsset.type === 'video',
        searchable: newAsset.type === 'datasheet' || newAsset.type === 'certificate'
      }
    }, { status: 201 })
  } catch (error) {
    console.error('Error creating media asset:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}