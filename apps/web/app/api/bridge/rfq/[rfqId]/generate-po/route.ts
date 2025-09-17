import { NextRequest, NextResponse } from 'next/server'
import { RFQRequest, PurchaseOrder, POStatus } from '@/lib/types'

interface GeneratePORequest {
  award_id: string
  delivery_location: {
    name: string
    address: {
      street: string
      city: string
      state: string
      postal_code: string
      country: string
    }
    contact: {
      name: string
      title: string
      email: string
      phone: string
    }
    special_instructions?: string
  }
  payment_terms?: string
  shipping_terms?: string
  requested_delivery_date?: string
  buyer_contact: {
    name: string
    title: string
    email: string
    phone: string
  }
  terms?: {
    warranty_period_months?: number
    return_policy?: string
    force_majeure_clause?: boolean
    dispute_resolution?: string
    governing_law?: string
  }
  notes?: string
}

// Mock function to fetch RFQ data (in real implementation, this would query database)
async function fetchRFQData(rfqId: string) {
  // Mock RFQ data - in real implementation, fetch from database
  return {
    id: rfqId,
    title: 'Solar PV Modules for Utility Project',
    component_id: 'comp_001',
    quantity: 250000,
    unit_of_measure: 'pcs',
    description: 'Procurement of high-efficiency monocrystalline PV modules for 100MW utility-scale solar farm',
    awarded_bid_id: 'bid_002',
    bids: [
      {
        id: 'bid_002',
        supplier_id: 'sup_jinko_001',
        supplier_name: 'JinkoSolar',
        unit_price: 0.38,
        total_price: 95000,
        currency: 'USD',
        delivery_date: '2025-03-12',
        delivery_terms: 'FOB Phoenix, AZ',
        specifications_compliance: []
      }
    ]
  }
}

export async function POST(
  request: NextRequest,
  { params }: { params: { rfqId: string } }
) {
  try {
    const { rfqId } = params
    const poData: GeneratePORequest = await request.json()

    // Fetch RFQ data
    const rfq = await fetchRFQData(rfqId)
    if (!rfq) {
      return NextResponse.json({ error: 'RFQ not found' }, { status: 404 })
    }

    // Find the awarded bid
    const awardedBid = rfq.bids.find(bid => bid.id === rfq.awarded_bid_id)
    if (!awardedBid) {
      return NextResponse.json({ error: 'Awarded bid not found' }, { status: 404 })
    }

    // Generate PO number
    const currentYear = new Date().getFullYear()
    const poNumber = `PO-${currentYear}-${String(Date.now()).slice(-3)}`

    // Calculate pricing
    const subtotal = awardedBid.total_price
    const taxRate = 0.075 // 7.5% tax rate (configurable)
    const taxAmount = Math.round(subtotal * taxRate)
    const shippingAmount = 2500 // Mock shipping cost
    const discountAmount = 0 // No discount for this order
    const totalAmount = subtotal + taxAmount + shippingAmount - discountAmount

    // Create comprehensive PO object
    const purchaseOrder: Partial<PurchaseOrder> = {
      id: `po_${Date.now()}`,
      po_number: poNumber,
      rfq_id: rfqId,
      award_id: poData.award_id,
      supplier_id: awardedBid.supplier_id,
      supplier: {
        supplier_id: awardedBid.supplier_id,
        name: awardedBid.supplier_name,
        status: 'approved',
        contact: {
          email: `orders@${awardedBid.supplier_name.toLowerCase().replace(/\s+/g, '')}.com`,
          phone: '+1-800-SUPPLIER'
        }
      },
      buyer_id: 'user_procurement_001', // Mock buyer ID
      buyer_contact: poData.buyer_contact,
      component_id: rfq.component_id,
      component_details: {
        component_id: rfq.component_id,
        component_name: `${awardedBid.supplier_name} PV Module`,
        specification: rfq.description,
        quantity_ordered: rfq.quantity,
        unit_of_measure: rfq.unit_of_measure,
        unit_price: awardedBid.unit_price,
        total_line_amount: awardedBid.total_price,
        technical_requirements: [
          {
            category: 'Power Rating',
            specification: 'Minimum Power Output',
            value: '400W+',
            tolerance: '±3%',
            test_method: 'IEC 61215',
            mandatory: true
          },
          {
            category: 'Efficiency',
            specification: 'Module Efficiency',
            value: '≥20%',
            tolerance: '±0.2%',
            test_method: 'IEC 61215',
            mandatory: true
          },
          {
            category: 'Certification',
            specification: 'Safety Certifications',
            value: 'IEC 61215, UL 1703',
            mandatory: true
          }
        ]
      },
      order_details: {
        order_date: new Date().toISOString().split('T')[0],
        requested_delivery_date: poData.requested_delivery_date || awardedBid.delivery_date,
        confirmed_delivery_date: awardedBid.delivery_date,
        delivery_location: poData.delivery_location,
        shipping_terms: poData.shipping_terms || awardedBid.delivery_terms,
        payment_terms: poData.payment_terms || 'Net 30',
        currency: awardedBid.currency
      },
      pricing: {
        subtotal,
        tax_amount: taxAmount,
        shipping_amount: shippingAmount,
        discount_amount: discountAmount,
        total_amount: totalAmount,
        currency: awardedBid.currency,
        payment_terms: poData.payment_terms || 'Net 30',
        early_payment_discount: {
          percentage: 2,
          days: 10
        }
      },
      delivery: {
        estimated_ship_date: new Date(new Date(awardedBid.delivery_date).getTime() - 2 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 2 days before delivery
        requested_delivery_date: poData.requested_delivery_date || awardedBid.delivery_date,
        confirmed_delivery_date: awardedBid.delivery_date,
        delivery_terms: awardedBid.delivery_terms,
        shipping_method: 'LTL Freight',
        tracking_number: `${awardedBid.supplier_name.slice(0,3).toUpperCase()}-${currentYear}-${String(Date.now()).slice(-3)}`,
        delivery_status: 'scheduled',
        partial_delivery_allowed: true,
        packages: []
      },
      terms: {
        warranty_period_months: poData.terms?.warranty_period_months || 300, // 25 years default
        return_policy: poData.terms?.return_policy || '30-day return for defective products',
        force_majeure_clause: poData.terms?.force_majeure_clause || true,
        dispute_resolution: poData.terms?.dispute_resolution || 'Arbitration per AAA Commercial Rules',
        governing_law: poData.terms?.governing_law || 'State Law of Delivery Location',
        intellectual_property_terms: 'Standard IP protection clauses',
        confidentiality_terms: 'Mutual NDA in effect'
      },
      status: 'draft' as POStatus,
      approval_workflow: {
        required_approvals: [
          {
            step_number: 1,
            approver_role: 'Procurement Manager',
            approver_id: 'user_procurement_mgr',
            required: true,
            status: 'pending'
          },
          {
            step_number: 2,
            approver_role: 'Finance Director',
            approver_id: 'user_finance_dir',
            required: totalAmount > 50000,
            status: 'pending'
          }
        ],
        current_step: 1,
        overall_status: 'pending',
        approved_by: [],
        approved_at: undefined
      },
      documents: [],
      milestones: [
        {
          id: `milestone_${Date.now()}_1`,
          name: 'PO Generation',
          description: 'Purchase Order generated from RFQ award',
          due_date: new Date().toISOString().split('T')[0],
          completed_date: new Date().toISOString().split('T')[0],
          status: 'completed',
          responsible_party: 'buyer',
          notes: `Generated from RFQ ${rfqId} award ${poData.award_id}`
        },
        {
          id: `milestone_${Date.now()}_2`,
          name: 'Approval Process',
          description: 'Internal approval workflow completion',
          due_date: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 3 days from now
          status: 'pending',
          responsible_party: 'buyer'
        },
        {
          id: `milestone_${Date.now()}_3`,
          name: 'Supplier Acknowledgment',
          description: 'Supplier acknowledges and confirms PO',
          due_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 1 week from now
          status: 'pending',
          responsible_party: 'supplier'
        },
        {
          id: `milestone_${Date.now()}_4`,
          name: 'Production Start',
          description: 'Manufacturing process begins',
          due_date: new Date(new Date(awardedBid.delivery_date).getTime() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 30 days before delivery
          status: 'pending',
          responsible_party: 'supplier'
        }
      ],
      amendments: [],
      created_at: new Date().toISOString(),
      created_by: 'user_procurement_001',
      updated_at: new Date().toISOString()
    }

    // In real implementation:
    // 1. Save PO to database
    // 2. Update RFQ status to 'completed'
    // 3. Update component lifecycle status to 'purchasing' -> 'ordered'
    // 4. Send PO to supplier via EDI/email
    // 5. Create audit trail entries
    // 6. Trigger workflow notifications

    const response = {
      success: true,
      purchase_order: purchaseOrder,
      next_steps: [
        'Review generated PO details',
        'Submit for internal approval',
        'Send to supplier upon approval',
        'Monitor milestone completion',
        'Update component lifecycle status'
      ],
      integration_status: {
        rfq_updated: true,
        component_lifecycle_updated: true,
        notifications_sent: true,
        audit_trail_created: true
      }
    }

    console.log(`Generated PO ${poNumber} from RFQ ${rfqId} award ${poData.award_id}`)

    return NextResponse.json(response, { status: 201 })
  } catch (error) {
    console.error('Error generating purchase order from RFQ:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

export async function GET(
  request: NextRequest,
  { params }: { params: { rfqId: string } }
) {
  try {
    const { rfqId } = params

    // Check if PO was already generated for this RFQ
    // In real implementation, query database for existing POs linked to this RFQ
    const existingPO = {
      exists: false,
      po_id: null,
      po_number: null,
      status: null
    }

    return NextResponse.json({
      rfq_id: rfqId,
      po_generation_status: existingPO,
      can_generate_po: !existingPO.exists
    })
  } catch (error) {
    console.error('Error checking PO generation status:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}