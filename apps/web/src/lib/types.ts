export * from '@originfd/types-odl'

export interface ComponentResponse {
  id: string
  component_id: string
  name?: string
  brand: string
  part_number: string
  category: string
  status: ComponentStatus
  domain: string
  rating_w: number
  voltage_v: number
  current_a: number
  efficiency?: number
  energy_kwh?: number
  dimensions?: {
    width_mm: number
    height_mm: number
    depth_mm: number
  }
  weight_kg?: number
  certification?: string[]
  warranty_years?: number
  lifecycle_stage?: LifecycleStage
  inventory_managed?: boolean
  compliance_status?: ComplianceStatus
  warranty_details?: WarrantyDetails
  created_at: string
  updated_at: string
  [key: string]: any
}

export type ComponentStatus =
  | 'draft'
  | 'parsed'
  | 'enriched'
  | 'approved'
  | 'available'
  | 'operational'
  | 'archived'
  | 'active'
  | 'deprecated'
  | 'obsolete'
  | 'discontinued'

export type ComponentCategory =
  | 'generation'
  | 'transmission'
  | 'distribution'
  | 'storage'
  | 'monitoring'
  | 'control'

export type ComponentDomain =
  | 'electrical'
  | 'mechanical'
  | 'thermal'
  | 'software'
  | 'data'

export type Domain = 'PV' | 'BESS' | 'HYBRID' | 'GRID' | 'MICROGRID'
export type Scale = 'RESIDENTIAL' | 'COMMERCIAL' | 'INDUSTRIAL' | 'UTILITY' | 'HYPERSCALE'

// Enhanced Phase 1 Types for ODL-SD v4.1 Compliance
export type LifecycleStage = 
  | 'development'
  | 'active'
  | 'mature'
  | 'deprecated'
  | 'obsolete'
  | 'discontinued'

export type ComplianceStatus = 
  | 'compliant'
  | 'non_compliant' 
  | 'pending_review'
  | 'expired'
  | 'not_applicable'

export interface WarrantyDetails {
  start_date?: string
  end_date?: string
  coverage_type?: 'full' | 'limited' | 'extended'
  warranty_provider?: string
  terms_conditions?: string
  contact_info?: string
}

export interface ComponentInventory {
  component_id: string
  warehouse_location: string
  quantity_available: number
  quantity_reserved: number
  quantity_on_order: number
  reorder_level: number
  reorder_quantity: number
  unit_cost: number
  last_updated: string
  location_details?: {
    building?: string
    room?: string
    shelf?: string
    bin?: string
  }
}

export interface InventoryTransaction {
  id: string
  component_id: string
  transaction_type: 'receipt' | 'issue' | 'transfer' | 'adjustment' | 'return'
  quantity: number
  unit_cost?: number
  from_location?: string
  to_location?: string
  reference_number?: string
  notes?: string
  created_by: string
  created_at: string
}

export interface DocumentResponse {
  id: string
  project_name: string
  domain: Domain
  scale: Scale
  current_version: number
  content_hash: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface OdlDocument {
  id: string
  project_name: string
  domain: Domain
  scale: Scale
  content: any
  metadata?: any
  [key: string]: any
}
