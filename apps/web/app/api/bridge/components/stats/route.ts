import { NextRequest, NextResponse } from 'next/server'

// ODL-SD v4.1 compliant component statistics
const odlStats = {
  total_components: 26, // 3 PV brands × 4-5 wattages + 2 inverter brands × 3-4 ratings + 2 battery brands × 2 models
  active_components: 21, // ~80% available
  draft_components: 5,   // ~20% draft
  categories: {
    pv_modules: 16,    // 3 brands with various wattages
    inverters: 7,      // 2 brands with multiple ratings
    batteries: 3       // 2 brands with multiple models
  },
  lifecycle_stages: {
    draft: 5,
    parsed: 0,
    enriched: 0,
    approved: 21,
    available: 21,
    operational: 0,
    archived: 0
  },
  compliance_status: {
    certificates_valid: 26,
    certificates_expiring: 0,
    non_compliant: 0,
    sustainability_tracked: 26
  },
  inventory_status: {
    in_stock: 26,
    low_stock: 2,
    out_of_stock: 0,
    reserved: 0
  },
  supplier_status: {
    approved_suppliers: 7,
    pending_approval: 0,
    active_rfqs: 0,
    active_orders: 0
  }
}

export async function GET(request: NextRequest) {
  try {
    console.log('Fetching ODL-SD v4.1 component stats:', odlStats.total_components, 'components')
    return NextResponse.json(odlStats)
  } catch (error) {
    console.error('Error fetching component stats:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}