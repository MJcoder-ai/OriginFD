import { NextRequest, NextResponse } from 'next/server'
import { RFQRequest, RFQStatus, BidStatus } from '@/lib/types'

// Mock RFQ data for Phase 2 implementation
const mockRFQs: RFQRequest[] = [
  {
    id: 'rfq_001',
    component_id: 'comp_001',
    requester_id: 'user_procurement_001',
    title: 'Solar PV Modules for Utility Project',
    description: 'Procurement of high-efficiency monocrystalline PV modules for 100MW utility-scale solar farm',
    quantity: 250000,
    unit_of_measure: 'pcs',
    delivery_location: 'Phoenix, AZ Distribution Center',
    required_delivery_date: '2025-03-15',
    budget_range: {
      min: 0.35,
      max: 0.45,
      currency: 'USD'
    },
    specifications: [
      {
        category: 'Power Rating',
        requirement: 'Minimum 400W per module',
        mandatory: true,
        measurement_unit: 'W',
        min_value: 400,
        max_value: 600
      },
      {
        category: 'Efficiency',
        requirement: 'Module efficiency ≥ 20%',
        mandatory: true,
        measurement_unit: '%',
        min_value: 20,
        max_value: 25
      },
      {
        category: 'Certification',
        requirement: 'IEC 61215, UL 1703 certified',
        mandatory: true
      },
      {
        category: 'Warranty',
        requirement: '25-year performance warranty',
        mandatory: true,
        min_value: 25,
        measurement_unit: 'years'
      }
    ],
    evaluation_criteria: {
      price_weight: 40,
      delivery_weight: 20,
      quality_weight: 25,
      experience_weight: 10,
      sustainability_weight: 5,
      total_weight: 100
    },
    status: 'receiving_bids',
    created_at: '2025-01-15T09:00:00Z',
    response_deadline: '2025-02-15T17:00:00Z',
    bids: [
      {
        id: 'bid_001',
        rfq_id: 'rfq_001',
        supplier_id: 'sup_longi_001',
        supplier_name: 'LONGi Solar',
        unit_price: 0.42,
        total_price: 105000,
        currency: 'USD',
        delivery_date: '2025-03-10',
        delivery_terms: 'FOB Phoenix, AZ',
        validity_period_days: 30,
        specifications_compliance: [
          {
            specification_id: 'spec_power',
            compliant: true,
            value: '540W',
            notes: 'Hi-MO 5m series'
          },
          {
            specification_id: 'spec_efficiency',
            compliant: true,
            value: '21.2%',
            notes: 'Independently verified'
          }
        ],
        sustainability_score: 85,
        certifications: ['IEC 61215', 'UL 1703', 'ISO 14001'],
        notes: 'Bulk pricing available, expedited delivery possible',
        status: 'submitted',
        submitted_at: '2025-01-20T14:30:00Z',
        evaluation_score: 88.5
      },
      {
        id: 'bid_002',
        rfq_id: 'rfq_001',
        supplier_id: 'sup_jinko_001',
        supplier_name: 'JinkoSolar',
        unit_price: 0.38,
        total_price: 95000,
        currency: 'USD',
        delivery_date: '2025-03-12',
        delivery_terms: 'FOB Phoenix, AZ',
        validity_period_days: 45,
        specifications_compliance: [
          {
            specification_id: 'spec_power',
            compliant: true,
            value: '535W',
            notes: 'Tiger Neo series'
          },
          {
            specification_id: 'spec_efficiency',
            compliant: true,
            value: '20.8%',
            notes: 'Third-party tested'
          }
        ],
        sustainability_score: 82,
        certifications: ['IEC 61215', 'UL 1703', 'OHSAS 18001'],
        notes: 'Extended warranty available',
        status: 'shortlisted',
        submitted_at: '2025-01-22T11:15:00Z',
        evaluation_score: 91.2
      }
    ]
  },
  {
    id: 'rfq_002',
    component_id: 'comp_017',
    requester_id: 'user_procurement_002',
    title: 'String Inverters for Commercial Installation',
    description: 'Procurement of three-phase string inverters for 2MW commercial solar installation',
    quantity: 50,
    unit_of_measure: 'pcs',
    delivery_location: 'Denver, CO Warehouse',
    required_delivery_date: '2025-04-01',
    budget_range: {
      min: 2500,
      max: 3500,
      currency: 'USD'
    },
    specifications: [
      {
        category: 'Power Rating',
        requirement: 'Three-phase 50kW nominal power',
        mandatory: true,
        measurement_unit: 'kW',
        min_value: 45,
        max_value: 55
      },
      {
        category: 'Efficiency',
        requirement: 'Peak efficiency ≥ 98%',
        mandatory: true,
        measurement_unit: '%',
        min_value: 98,
        max_value: 99
      },
      {
        category: 'Monitoring',
        requirement: 'Built-in monitoring and communication',
        mandatory: true
      }
    ],
    evaluation_criteria: {
      price_weight: 35,
      delivery_weight: 15,
      quality_weight: 30,
      experience_weight: 15,
      sustainability_weight: 5,
      total_weight: 100
    },
    status: 'draft',
    created_at: '2025-01-12T10:30:00Z',
    response_deadline: '2025-02-28T17:00:00Z',
    bids: []
  }
]

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const status = searchParams.get('status')
    const componentId = searchParams.get('component_id')

    let filteredRFQs = mockRFQs

    if (status) {
      filteredRFQs = filteredRFQs.filter(rfq => rfq.status === status)
    }

    if (componentId) {
      filteredRFQs = filteredRFQs.filter(rfq => rfq.component_id === componentId)
    }

    console.log(`Fetching RFQs: ${filteredRFQs.length} found`)
    return NextResponse.json(filteredRFQs)
  } catch (error) {
    console.error('Error fetching RFQs:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

export async function POST(request: NextRequest) {
  try {
    const rfqData = await request.json()
    
    const newRFQ: RFQRequest = {
      id: `rfq_${Date.now()}`,
      ...rfqData,
      status: rfqData.status || 'draft',
      created_at: new Date().toISOString(),
      bids: []
    }

    mockRFQs.push(newRFQ)
    console.log('Created new RFQ:', newRFQ.id)
    
    return NextResponse.json(newRFQ, { status: 201 })
  } catch (error) {
    console.error('Error creating RFQ:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}