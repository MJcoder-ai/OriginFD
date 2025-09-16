import { NextRequest, NextResponse } from 'next/server'

interface AwardRequest {
  winning_bid_id: string
  award_amount: number
  award_quantity: number
  delivery_date: string
  terms_conditions: string
  contract_duration_days?: number
  payment_terms?: string
  notes?: string
}

interface AwardResponse {
  award_id: string
  rfq_id: string
  winning_bid_id: string
  supplier_id: string
  supplier_name: string
  award_amount: number
  award_quantity: number
  unit_price: number
  delivery_date: string
  terms_conditions: string
  contract_duration_days: number
  payment_terms: string
  status: 'pending_acceptance' | 'accepted' | 'rejected' | 'completed'
  awarded_at: string
  awarded_by: string
  notes?: string
  next_steps: string[]
}

export async function POST(
  request: NextRequest,
  { params }: { params: { rfqId: string } }
) {
  try {
    const { rfqId } = params
    const awardData: AwardRequest = await request.json()

    // Validate required fields
    if (!awardData.winning_bid_id || !awardData.award_amount || !awardData.award_quantity) {
      return NextResponse.json(
        { error: 'Missing required fields: winning_bid_id, award_amount, award_quantity' },
        { status: 400 }
      )
    }

    // Mock bid lookup (in real implementation, query database)
    const mockBid = {
      id: awardData.winning_bid_id,
      supplier_id: 'sup_jinko_001',
      supplier_name: 'JinkoSolar',
      unit_price: awardData.award_amount / awardData.award_quantity
    }

    const award: AwardResponse = {
      award_id: `award_${Date.now()}`,
      rfq_id: rfqId,
      winning_bid_id: awardData.winning_bid_id,
      supplier_id: mockBid.supplier_id,
      supplier_name: mockBid.supplier_name,
      award_amount: awardData.award_amount,
      award_quantity: awardData.award_quantity,
      unit_price: mockBid.unit_price,
      delivery_date: awardData.delivery_date,
      terms_conditions: awardData.terms_conditions,
      contract_duration_days: awardData.contract_duration_days || 90,
      payment_terms: awardData.payment_terms || 'Net 30',
      status: 'pending_acceptance',
      awarded_at: new Date().toISOString(),
      awarded_by: 'user_procurement_001', // Mock user
      notes: awardData.notes,
      next_steps: [
        'Send award notification to supplier',
        'Generate purchase order',
        'Await supplier acceptance',
        'Execute contract',
        'Schedule delivery'
      ]
    }

    // In real implementation:
    // 1. Update RFQ status to 'awarded'
    // 2. Update winning bid status to 'awarded'
    // 3. Update other bids status to 'rejected'
    // 4. Create award record in database
    // 5. Send notifications to suppliers
    // 6. Trigger component lifecycle status update

    console.log('RFQ awarded:', rfqId, 'to supplier:', mockBid.supplier_name)

    return NextResponse.json(award, { status: 201 })
  } catch (error) {
    console.error('Error awarding RFQ:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

export async function GET(
  request: NextRequest,
  { params }: { params: { rfqId: string } }
) {
  try {
    const { rfqId } = params

    // Mock award data (in real implementation, query database)
    const award: AwardResponse = {
      award_id: 'award_001',
      rfq_id: rfqId,
      winning_bid_id: 'bid_002',
      supplier_id: 'sup_jinko_001',
      supplier_name: 'JinkoSolar',
      award_amount: 95000,
      award_quantity: 250000,
      unit_price: 0.38,
      delivery_date: '2025-03-12',
      terms_conditions: 'Standard supply agreement, FOB Phoenix AZ',
      contract_duration_days: 120,
      payment_terms: 'Net 30',
      status: 'accepted',
      awarded_at: '2025-01-25T16:00:00Z',
      awarded_by: 'user_procurement_001',
      notes: 'Best overall value proposition',
      next_steps: [
        'Generate purchase order - Completed',
        'Supplier acceptance - Completed',
        'Contract execution - In Progress',
        'Schedule delivery - Pending'
      ]
    }

    return NextResponse.json(award)
  } catch (error) {
    console.error('Error fetching award:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}