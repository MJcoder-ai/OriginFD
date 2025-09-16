import { NextRequest, NextResponse } from 'next/server'
import { MediaAsset, MediaAssetType, MediaAssetStatus } from '@/lib/types'

// Mock media assets data for Phase 2 implementation
const mockMediaAssets: MediaAsset[] = [
  {
    id: 'asset_001',
    component_id: 'comp_001',
    asset_type: 'datasheet',
    file_name: 'JinkoSolar_Tiger_Neo_535W_Datasheet_v2.3.pdf',
    file_size: 2456789,
    mime_type: 'application/pdf',
    file_url: '/media/datasheets/jinko_tiger_neo_535w_v2.3.pdf',
    cdn_url: 'https://cdn.originfd.com/datasheets/jinko_tiger_neo_535w_v2.3.pdf',
    thumbnail_url: '/media/thumbnails/jinko_tiger_neo_535w_thumb.jpg',
    metadata: {
      page_count: 4,
      language: 'en',
      checksum_md5: 'a1b2c3d4e5f6789012345678',
      checksum_sha256: 'abc123def456ghi789jkl012mno345pqr678stu901vwx234yz567',
      original_filename: 'Tiger Neo 535W Datasheet v2.3.pdf',
      document_version: '2.3',
      revision_date: '2024-11-15',
      test_standard: 'IEC 61215, IEC 61730',
      extracted_text: 'JinkoSolar Tiger Neo 535W Monocrystalline Silicon Photovoltaic Module...',
      extracted_data: {
        power_rating: '535W',
        efficiency: '20.8%',
        warranty: '25 years',
        dimensions: '2274×1134×35mm'
      },
      confidence_score: 98.5,
      ai_processed_at: '2025-01-15T10:30:00Z'
    },
    tags: ['pv_module', 'monocrystalline', 'tier1', 'high_efficiency'],
    status: 'approved',
    visibility: 'public',
    version: 2,
    uploaded_by: 'user_technical_001',
    uploaded_at: '2025-01-15T09:00:00Z',
    updated_at: '2025-01-15T10:45:00Z',
    access_history: [
      {
        accessed_by: 'user_procurement_001',
        accessed_at: '2025-01-20T14:30:00Z',
        access_type: 'download'
      },
      {
        accessed_by: 'user_engineering_002',
        accessed_at: '2025-01-22T11:15:00Z',
        access_type: 'view'
      }
    ]
  },
  {
    id: 'asset_002',
    component_id: 'comp_001',
    asset_type: 'certificate',
    file_name: 'JinkoSolar_IEC61215_Certificate_2024.pdf',
    file_size: 856234,
    mime_type: 'application/pdf',
    file_url: '/media/certificates/jinko_iec61215_2024.pdf',
    cdn_url: 'https://cdn.originfd.com/certificates/jinko_iec61215_2024.pdf',
    thumbnail_url: '/media/thumbnails/jinko_iec61215_thumb.jpg',
    metadata: {
      page_count: 2,
      language: 'en',
      checksum_md5: 'b2c3d4e5f6789012345678a1',
      checksum_sha256: 'def456ghi789jkl012mno345pqr678stu901vwx234yz567abc123',
      original_filename: 'IEC61215 Certificate - Tiger Neo 535W.pdf',
      certification_number: 'IEC61215-2024-TN535',
      test_standard: 'IEC 61215:2016',
      expiration_date: '2027-01-15',
      confidence_score: 99.2,
      ai_processed_at: '2025-01-15T11:00:00Z'
    },
    tags: ['certificate', 'iec61215', 'safety', 'compliance'],
    status: 'approved',
    visibility: 'public',
    version: 1,
    uploaded_by: 'user_compliance_001',
    uploaded_at: '2025-01-15T10:30:00Z',
    updated_at: '2025-01-15T10:30:00Z',
    access_history: []
  },
  {
    id: 'asset_003',
    component_id: 'comp_001',
    asset_type: 'product_image',
    file_name: 'JinkoSolar_Tiger_Neo_535W_Product_Image.jpg',
    file_size: 1245678,
    mime_type: 'image/jpeg',
    file_url: '/media/images/jinko_tiger_neo_535w.jpg',
    cdn_url: 'https://cdn.originfd.com/images/jinko_tiger_neo_535w.jpg',
    thumbnail_url: '/media/thumbnails/jinko_tiger_neo_535w_img_thumb.jpg',
    metadata: {
      dimensions: {
        width: 2400,
        height: 1800,
        resolution_dpi: 300
      },
      checksum_md5: 'c3d4e5f6789012345678a1b2',
      checksum_sha256: 'ghi789jkl012mno345pqr678stu901vwx234yz567abc123def456',
      original_filename: 'Tiger Neo 535W Product Photo.jpg',
      compression_ratio: 85
    },
    tags: ['product_photo', 'marketing', 'high_res'],
    status: 'approved',
    visibility: 'public',
    version: 1,
    uploaded_by: 'user_marketing_001',
    uploaded_at: '2025-01-15T12:00:00Z',
    updated_at: '2025-01-15T12:00:00Z',
    access_history: []
  },
  {
    id: 'asset_004',
    component_id: 'comp_017',
    asset_type: 'installation_guide',
    file_name: 'ABB_TRIO_50kW_Installation_Manual_v4.1.pdf',
    file_size: 3567890,
    mime_type: 'application/pdf',
    file_url: '/media/manuals/abb_trio_50kw_install_v4.1.pdf',
    cdn_url: 'https://cdn.originfd.com/manuals/abb_trio_50kw_install_v4.1.pdf',
    thumbnail_url: '/media/thumbnails/abb_trio_install_thumb.jpg',
    metadata: {
      page_count: 28,
      language: 'en',
      checksum_md5: 'd4e5f6789012345678a1b2c3',
      checksum_sha256: 'jkl012mno345pqr678stu901vwx234yz567abc123def456ghi789',
      original_filename: 'TRIO-50.0-TL-OUTD Installation Manual v4.1.pdf',
      document_version: '4.1',
      revision_date: '2024-10-20',
      extracted_text: 'ABB TRIO-50.0-TL-OUTD String Inverter Installation Manual...',
      extracted_data: {
        power_rating: '50kW',
        input_voltage: '1000V DC',
        output_voltage: '400V AC',
        efficiency: '98.6%'
      },
      confidence_score: 97.8,
      ai_processed_at: '2025-01-16T09:15:00Z'
    },
    tags: ['inverter', 'installation', 'manual', '50kw'],
    status: 'processing',
    visibility: 'internal',
    version: 1,
    uploaded_by: 'user_technical_002',
    uploaded_at: '2025-01-16T08:45:00Z',
    updated_at: '2025-01-16T09:20:00Z',
    access_history: []
  }
]

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const componentId = searchParams.get('component_id')
    const assetType = searchParams.get('asset_type')
    const status = searchParams.get('status')
    const visibility = searchParams.get('visibility')
    const tags = searchParams.get('tags')?.split(',')

    let filteredAssets = mockMediaAssets

    // Apply filters
    if (componentId) {
      filteredAssets = filteredAssets.filter(asset => asset.component_id === componentId)
    }

    if (assetType) {
      filteredAssets = filteredAssets.filter(asset => asset.asset_type === assetType)
    }

    if (status) {
      filteredAssets = filteredAssets.filter(asset => asset.status === status)
    }

    if (visibility) {
      filteredAssets = filteredAssets.filter(asset => asset.visibility === visibility)
    }

    if (tags && tags.length > 0) {
      filteredAssets = filteredAssets.filter(asset =>
        tags.some(tag => asset.tags.includes(tag.trim()))
      )
    }

    console.log(`Fetching media assets: ${filteredAssets.length} found`)
    return NextResponse.json(filteredAssets)
  } catch (error) {
    console.error('Error fetching media assets:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

export async function POST(request: NextRequest) {
  try {
    const assetData = await request.json()

    // Validate required fields
    if (!assetData.component_id || !assetData.file_name || !assetData.asset_type) {
      return NextResponse.json(
        { error: 'Missing required fields: component_id, file_name, asset_type' },
        { status: 400 }
      )
    }

    // Generate mock checksums (in real implementation, calculate from actual file)
    const mockMd5 = Math.random().toString(36).substring(2, 15)
    const mockSha256 = Math.random().toString(36).substring(2, 15).repeat(4)

    const newAsset: MediaAsset = {
      id: `asset_${Date.now()}`,
      component_id: assetData.component_id,
      asset_type: assetData.asset_type,
      file_name: assetData.file_name,
      file_size: assetData.file_size || 0,
      mime_type: assetData.mime_type || 'application/octet-stream',
      file_url: `/media/uploads/${assetData.file_name}`,
      metadata: {
        checksum_md5: mockMd5,
        checksum_sha256: mockSha256,
        original_filename: assetData.file_name,
        ...assetData.metadata
      },
      tags: assetData.tags || [],
      status: 'uploaded',
      visibility: assetData.visibility || 'internal',
      version: 1,
      uploaded_by: assetData.uploaded_by || 'system',
      uploaded_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      access_history: []
    }

    // Mock saving to database
    mockMediaAssets.push(newAsset)

    // In real implementation:
    // 1. Save file to storage
    // 2. Generate thumbnails
    // 3. Schedule processing jobs
    // 4. Update component media references

    console.log('Created new media asset:', newAsset.id)
    return NextResponse.json(newAsset, { status: 201 })
  } catch (error) {
    console.error('Error creating media asset:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}