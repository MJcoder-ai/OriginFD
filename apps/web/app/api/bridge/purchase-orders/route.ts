import { NextRequest, NextResponse } from 'next/server'
import { PurchaseOrder, POStatus } from '@/lib/types'

// Mock Purchase Order data for Phase 2 implementation
const mockPurchaseOrders: PurchaseOrder[] = [
  {
    id: 'po_001',
    po_number: 'PO-2025-001',
    rfq_id: 'rfq_001',
    award_id: 'award_001',
    supplier_id: 'sup_jinko_001',
    supplier: {
      supplier_id: 'sup_jinko_001',
      name: 'JinkoSolar',
      gln: '1234567890123',
      status: 'approved',
      contact: {
        email: 'sales@jinkosolar.com',
        phone: '+1-415-555-0123'
      }
    },
    buyer_id: 'user_procurement_001',
    buyer_contact: {
      name: 'Sarah Johnson',
      title: 'Senior Procurement Manager',
      email: 'sarah.johnson@originfd.com',
      phone: '+1-602-555-0189'
    },
    component_id: 'comp_001',
    component_details: {
      component_id: 'comp_001',
      component_name: 'JinkoSolar Tiger Neo 535W Monocrystalline PV Module',
      specification: 'Tiger Neo series, 535W nominal power, 20.8% efficiency',
      quantity_ordered: 250000,
      unit_of_measure: 'pcs',
      unit_price: 0.38,
      total_line_amount: 95000,
      technical_requirements: [
        {
          category: 'Power Rating',
          specification: 'Nominal Power Output',
          value: '535W',
          tolerance: '±3%',
          test_method: 'IEC 61215',
          mandatory: true
        },
        {
          category: 'Efficiency',
          specification: 'Module Efficiency',
          value: '20.8%',
          tolerance: '±0.2%',
          test_method: 'IEC 61215',
          mandatory: true
        },
        {
          category: 'Certification',
          specification: 'Safety Certification',
          value: 'IEC 61215, UL 1703',
          mandatory: true
        }
      ]
    },
    order_details: {
      order_date: '2025-01-28',
      requested_delivery_date: '2025-03-12',
      confirmed_delivery_date: '2025-03-10',
      delivery_location: {
        name: 'Phoenix Distribution Center',
        address: {
          street: '1234 Industrial Blvd',
          city: 'Phoenix',
          state: 'AZ',
          postal_code: '85001',
          country: 'USA'
        },
        contact: {
          name: 'Mike Rodriguez',
          title: 'Warehouse Manager',
          email: 'mike.rodriguez@originfd.com',
          phone: '+1-602-555-0156'
        },
        special_instructions: 'Delivery between 8AM-4PM weekdays only. Call 30 minutes before arrival.'
      },
      shipping_terms: 'FOB Phoenix, AZ',
      payment_terms: 'Net 30',
      currency: 'USD'
    },
    pricing: {
      subtotal: 95000,
      tax_amount: 7125, // 7.5% AZ tax
      shipping_amount: 2500,
      discount_amount: 1000,
      total_amount: 103625,
      currency: 'USD',
      payment_terms: 'Net 30',
      early_payment_discount: {
        percentage: 2,
        days: 10
      }
    },
    delivery: {
      estimated_ship_date: '2025-03-08',
      requested_delivery_date: '2025-03-12',
      confirmed_delivery_date: '2025-03-10',
      delivery_terms: 'FOB Phoenix, AZ',
      shipping_method: 'LTL Freight',
      tracking_number: 'JKS-2025-001',
      delivery_status: 'scheduled',
      partial_delivery_allowed: true,
      packages: [
        {
          package_id: 'pkg_001',
          tracking_number: 'JKS-2025-001-A',
          weight: 25000,
          dimensions: {
            length: 12,
            width: 8,
            height: 6,
            unit: 'ft'
          },
          shipped_date: '2025-03-08',
          status: 'shipped'
        }
      ]
    },
    terms: {
      warranty_period_months: 300, // 25 years
      return_policy: '30-day return for defective products',
      force_majeure_clause: true,
      dispute_resolution: 'Arbitration per AAA Commercial Rules',
      governing_law: 'Arizona State Law',
      intellectual_property_terms: 'Standard IP protection clauses',
      confidentiality_terms: 'Mutual NDA in effect'
    },
    status: 'acknowledged',
    approval_workflow: {
      required_approvals: [
        {
          step_number: 1,
          approver_role: 'Procurement Manager',
          approver_id: 'user_procurement_mgr',
          required: true,
          status: 'approved',
          approved_at: '2025-01-28T10:30:00Z',
          notes: 'Approved - good pricing and delivery terms'
        },
        {
          step_number: 2,
          approver_role: 'Finance Director',
          approver_id: 'user_finance_dir',
          required: true,
          status: 'approved',
          approved_at: '2025-01-28T14:15:00Z',
          notes: 'Budget approved'
        }
      ],
      current_step: 2,
      overall_status: 'approved',
      approved_by: ['user_procurement_mgr', 'user_finance_dir'],
      approved_at: '2025-01-28T14:15:00Z'
    },
    documents: [
      {
        id: 'doc_001',
        type: 'purchase_order',
        name: 'PO-2025-001.pdf',
        file_url: '/documents/po/PO-2025-001.pdf',
        file_size: 156789,
        uploaded_by: 'user_procurement_001',
        uploaded_at: '2025-01-28T16:00:00Z',
        version: 1,
        description: 'Signed purchase order'
      },
      {
        id: 'doc_002',
        type: 'technical_specification',
        name: 'JinkoSolar_Tiger_Neo_535W_Specs.pdf',
        file_url: '/documents/specs/JinkoSolar_Tiger_Neo_535W_Specs.pdf',
        file_size: 2456789,
        uploaded_by: 'user_engineering_001',
        uploaded_at: '2025-01-28T16:30:00Z',
        version: 1,
        description: 'Technical specifications and test certificates'
      }
    ],
    milestones: [
      {
        id: 'milestone_001',
        name: 'Order Acknowledgment',
        description: 'Supplier acknowledges receipt and confirms order details',
        due_date: '2025-01-30',
        completed_date: '2025-01-29',
        status: 'completed',
        responsible_party: 'supplier',
        notes: 'Acknowledged via EDI on 2025-01-29'
      },
      {
        id: 'milestone_002',
        name: 'Production Start',
        description: 'Manufacturing process begins',
        due_date: '2025-02-05',
        status: 'completed',
        completed_date: '2025-02-03',
        responsible_party: 'supplier',
        notes: 'Production started ahead of schedule'
      },
      {
        id: 'milestone_003',
        name: 'Quality Inspection',
        description: 'Final quality control and certification',
        due_date: '2025-03-05',
        status: 'in_progress',
        responsible_party: 'supplier'
      },
      {
        id: 'milestone_004',
        name: 'Shipment',
        description: 'Products shipped to delivery location',
        due_date: '2025-03-08',
        status: 'pending',
        responsible_party: 'supplier'
      }
    ],
    amendments: [],
    created_at: '2025-01-28T09:00:00Z',
    created_by: 'user_procurement_001',
    updated_at: '2025-01-29T08:15:00Z'
  },
  {
    id: 'po_002',
    po_number: 'PO-2025-002',
    supplier_id: 'sup_abb_001',
    supplier: {
      supplier_id: 'sup_abb_001',
      name: 'ABB Power Systems',
      status: 'approved',
      contact: {
        email: 'orders@abb.com',
        phone: '+1-800-ABB-HELP'
      }
    },
    buyer_id: 'user_procurement_002',
    buyer_contact: {
      name: 'Tom Wilson',
      title: 'Procurement Specialist',
      email: 'tom.wilson@originfd.com',
      phone: '+1-602-555-0167'
    },
    component_id: 'comp_017',
    component_details: {
      component_id: 'comp_017',
      component_name: 'ABB TRIO-50.0-TL-OUTD String Inverter',
      specification: 'Three-phase 50kW string inverter, outdoor installation',
      quantity_ordered: 50,
      unit_of_measure: 'pcs',
      unit_price: 3200,
      total_line_amount: 160000,
      technical_requirements: [
        {
          category: 'Power Rating',
          specification: 'AC Nominal Power',
          value: '50kW',
          tolerance: '±2%',
          mandatory: true
        },
        {
          category: 'Efficiency',
          specification: 'Peak Efficiency',
          value: '98.6%',
          tolerance: '±0.2%',
          mandatory: true
        }
      ]
    },
    order_details: {
      order_date: '2025-01-30',
      requested_delivery_date: '2025-04-01',
      delivery_location: {
        name: 'Denver Warehouse',
        address: {
          street: '5678 Commerce Way',
          city: 'Denver',
          state: 'CO',
          postal_code: '80202',
          country: 'USA'
        },
        contact: {
          name: 'Lisa Chang',
          title: 'Site Manager',
          email: 'lisa.chang@originfd.com',
          phone: '+1-303-555-0134'
        }
      },
      shipping_terms: 'FOB Denver, CO',
      payment_terms: 'Net 45',
      currency: 'USD'
    },
    pricing: {
      subtotal: 160000,
      tax_amount: 12800, // 8% CO tax
      shipping_amount: 3500,
      discount_amount: 5000,
      total_amount: 171300,
      currency: 'USD',
      payment_terms: 'Net 45'
    },
    delivery: {
      estimated_ship_date: '2025-03-28',
      requested_delivery_date: '2025-04-01',
      delivery_terms: 'FOB Denver, CO',
      shipping_method: 'LTL Freight',
      delivery_status: 'pending',
      partial_delivery_allowed: false
    },
    terms: {
      warranty_period_months: 120, // 10 years
      return_policy: '14-day return for unopened items',
      force_majeure_clause: true,
      dispute_resolution: 'Colorado State Courts',
      governing_law: 'Colorado State Law'
    },
    status: 'pending_approval',
    approval_workflow: {
      required_approvals: [
        {
          step_number: 1,
          approver_role: 'Procurement Manager',
          required: true,
          status: 'pending'
        },
        {
          step_number: 2,
          approver_role: 'Finance Director',
          required: true,
          status: 'pending'
        }
      ],
      current_step: 1,
      overall_status: 'pending'
    },
    documents: [],
    milestones: [],
    amendments: [],
    created_at: '2025-01-30T11:00:00Z',
    created_by: 'user_procurement_002',
    updated_at: '2025-01-30T11:00:00Z'
  }
]

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const status = searchParams.get('status')
    const supplierId = searchParams.get('supplier_id')
    const componentId = searchParams.get('component_id')

    let filteredPOs = mockPurchaseOrders

    if (status) {
      filteredPOs = filteredPOs.filter(po => po.status === status)
    }

    if (supplierId) {
      filteredPOs = filteredPOs.filter(po => po.supplier_id === supplierId)
    }

    if (componentId) {
      filteredPOs = filteredPOs.filter(po => po.component_id === componentId)
    }

    console.log(`Fetching Purchase Orders: ${filteredPOs.length} found`)
    return NextResponse.json(filteredPOs)
  } catch (error) {
    console.error('Error fetching purchase orders:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

export async function POST(request: NextRequest) {
  try {
    const poData = await request.json()
    
    // Generate PO number
    const poNumber = `PO-${new Date().getFullYear()}-${String(mockPurchaseOrders.length + 1).padStart(3, '0')}`
    
    const newPO: Partial<PurchaseOrder> = {
      id: `po_${Date.now()}`,
      po_number: poNumber,
      ...poData,
      status: poData.status || 'draft',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      documents: [],
      milestones: [],
      amendments: []
    }

    // Mock saving to database
    mockPurchaseOrders.push(newPO as PurchaseOrder)
    console.log('Created new Purchase Order:', newPO.po_number)
    
    return NextResponse.json(newPO, { status: 201 })
  } catch (error) {
    console.error('Error creating purchase order:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}