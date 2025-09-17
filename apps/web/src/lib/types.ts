export * from "@originfd/types-odl";
import type { ODLComponentStatus } from "@originfd/types-odl";

// ODL-SD v4.1 Component Management Response Structure
export interface ComponentResponse {
  id: string;
  component_management: ComponentManagement;
}

export interface ComponentManagement {
  version: string;
  status: ODLComponentStatus;
  component_identity: ComponentIdentity;
  source_documents: SourceDocuments;
  tracking_policy: TrackingPolicy;
  supplier_chain: SupplierChain;
  order_management: OrderManagement;
  inventory: ComponentInventoryManagement;
  warranty: WarrantyManagement;
  returns: ReturnsManagement;
  traceability: TraceabilityManagement;
  compliance: ComplianceManagement;
  ai_logs: AILogs;
  audit: AuditTrail;
  analytics: ComponentAnalytics;
}

export interface ComponentIdentity {
  component_id: string; // Format: CMP:Brand:Part:Rating:Rev
  brand: string;
  part_number: string;
  rating_w: number;
  name: string;
  classification?: {
    unspsc?: string;
    eclass?: string;
    hs_code?: string;
    gtin?: string;
  };
}

export interface SourceDocuments {
  datasheet: DocumentRef;
  additional: DocumentRef[];
}

export interface DocumentRef {
  type:
    | "datasheet"
    | "warranty"
    | "installation"
    | "faq"
    | "certificate"
    | "test_report"
    | "other";
  url: string;
  hash: string;
  parsed_at: string;
  pages?: number[];
}

export interface TrackingPolicy {
  level: "quantity" | "lot" | "serial";
  auto_rules: {
    regulatory_serial_required: boolean;
    warranty_sn_required: boolean;
    safety_critical: boolean;
  };
}

export interface SupplierChain {
  suppliers: Supplier[];
}

export interface Supplier {
  supplier_id: string;
  name: string;
  gln?: string;
  status: "approved" | "pending" | "suspended";
  contact: {
    email?: string;
    phone?: string;
  };
}

export interface OrderManagement {
  rfq_enabled: boolean;
  orders: any[];
  shipments: any[];
}

export interface ComponentInventoryManagement {
  stocks: InventoryRecord[];
}

export interface InventoryRecord {
  location: {
    name: string;
    gln?: string;
  };
  status: "in_stock" | "reserved" | "quarantine" | "installed" | "scrap";
  uom: "pcs" | "m" | "kg" | "set" | "pair" | "roll";
  on_hand_qty: number;
  lots?: any[];
  serials?: string[];
}

export interface WarrantyManagement {
  terms: {
    type: "product" | "performance" | "combined";
    duration_years: number;
    coverage_min_pct?: number;
  };
  claims: any[];
}

export interface ReturnsManagement {
  policies: {
    return_window_days: number;
    restocking_fee_pct: number;
    return_rate_pct: number;
  };
  records: any[];
}

export interface TraceabilityManagement {
  dpp: {
    enabled: boolean;
    uri: string;
    mandatory_fields: string[];
  };
  serialization: {
    format: string;
    generation_rule: string;
  };
}

export interface ComplianceManagement {
  certificates: ComplianceCertificate[];
  sustainability?: {
    embodied_co2e_kg: number;
    recyclable_pct: number;
    hazardous_substances: string[];
  };
}

export interface ComplianceCertificate {
  standard: string;
  number: string;
  issuer: string;
  valid_until: string;
  scope: string;
}

export interface AILogs {
  classification_confidence: number;
  last_enrichment: string;
  auto_actions: any[];
}

export interface AuditTrail {
  created_by: string;
  created_at: string;
  updated_by: string;
  updated_at: string;
  version: number;
}

export interface ComponentAnalytics {
  procurement_stats: {
    avg_lead_time_days: number;
    price_trend_3m: "increasing" | "stable" | "declining";
    quality_score_pct: number;
  };
}

// Legacy status type for backward compatibility - use ODLComponentStatus from @originfd/types-odl instead
export type ComponentStatus = import("@originfd/types-odl").ODLComponentStatus;

// RFQ/Bidding Workflow Types for Phase 2
export interface RFQRequest {
  id: string;
  component_id: string;
  requester_id: string;
  title: string;
  description: string;
  quantity: number;
  unit_of_measure: string;
  delivery_location: string;
  required_delivery_date: string;
  budget_range?: {
    min: number;
    max: number;
    currency: string;
  };
  specifications: RFQSpecification[];
  evaluation_criteria: EvaluationCriteria;
  status: RFQStatus;
  created_at: string;
  response_deadline: string;
  bids: RFQBid[];
  awarded_bid_id?: string;
}

export interface RFQSpecification {
  category: string;
  requirement: string;
  mandatory: boolean;
  measurement_unit?: string;
  min_value?: number;
  max_value?: number;
}

export interface EvaluationCriteria {
  price_weight: number; // Percentage (0-100)
  delivery_weight: number;
  quality_weight: number;
  experience_weight: number;
  sustainability_weight: number;
  total_weight: number; // Must equal 100
}

export interface RFQBid {
  id: string;
  rfq_id: string;
  supplier_id: string;
  supplier_name: string;
  unit_price: number;
  total_price: number;
  currency: string;
  delivery_date: string;
  delivery_terms: string;
  validity_period_days: number;
  specifications_compliance: SpecificationCompliance[];
  sustainability_score?: number;
  certifications: string[];
  notes?: string;
  status: BidStatus;
  submitted_at: string;
  evaluation_score?: number;
}

export interface SpecificationCompliance {
  specification_id: string;
  compliant: boolean;
  value?: string;
  notes?: string;
}

export type RFQStatus =
  | "draft"
  | "published"
  | "receiving_bids"
  | "evaluation"
  | "awarded"
  | "cancelled"
  | "completed";

export type BidStatus =
  | "draft"
  | "submitted"
  | "under_review"
  | "shortlisted"
  | "awarded"
  | "rejected"
  | "withdrawn";

// Purchase Order Management Types
export interface PurchaseOrder {
  id: string;
  po_number: string;
  rfq_id?: string;
  award_id?: string;
  supplier_id: string;
  supplier: Supplier;
  buyer_id: string;
  buyer_contact: ContactInfo;
  component_id: string;
  component_details: ComponentOrderDetails;
  order_details: OrderDetails;
  pricing: PricingDetails;
  delivery: DeliveryDetails;
  terms: ContractTerms;
  status: POStatus;
  approval_workflow: ApprovalWorkflow;
  documents: PODocument[];
  milestones: Milestone[];
  amendments: POAmendment[];
  created_at: string;
  created_by: string;
  updated_at: string;
}

export interface ComponentOrderDetails {
  component_id: string;
  component_name: string;
  specification: string;
  quantity_ordered: number;
  unit_of_measure: string;
  unit_price: number;
  total_line_amount: number;
  technical_requirements: TechnicalRequirement[];
}

export interface TechnicalRequirement {
  category: string;
  specification: string;
  value: string;
  tolerance?: string;
  test_method?: string;
  mandatory: boolean;
}

export interface OrderDetails {
  order_date: string;
  requested_delivery_date: string;
  confirmed_delivery_date?: string;
  delivery_location: DeliveryLocation;
  shipping_terms: string;
  payment_terms: string;
  currency: string;
}

export interface DeliveryLocation {
  name: string;
  address: {
    street: string;
    city: string;
    state: string;
    postal_code: string;
    country: string;
  };
  contact: ContactInfo;
  special_instructions?: string;
}

export interface ContactInfo {
  name: string;
  title?: string;
  email: string;
  phone: string;
}

export interface PricingDetails {
  subtotal: number;
  tax_amount: number;
  shipping_amount: number;
  discount_amount: number;
  total_amount: number;
  currency: string;
  payment_terms: string;
  early_payment_discount?: {
    percentage: number;
    days: number;
  };
}

export interface DeliveryDetails {
  estimated_ship_date: string;
  requested_delivery_date: string;
  confirmed_delivery_date?: string;
  delivery_terms: string;
  shipping_method: string;
  tracking_number?: string;
  delivery_status: DeliveryStatus;
  partial_delivery_allowed: boolean;
  packages?: DeliveryPackage[];
}

export interface DeliveryPackage {
  package_id: string;
  tracking_number: string;
  weight: number;
  dimensions: {
    length: number;
    width: number;
    height: number;
    unit: string;
  };
  shipped_date: string;
  delivered_date?: string;
  status: "pending" | "shipped" | "in_transit" | "delivered" | "failed";
}

export interface ContractTerms {
  warranty_period_months: number;
  return_policy: string;
  force_majeure_clause: boolean;
  dispute_resolution: string;
  governing_law: string;
  intellectual_property_terms?: string;
  confidentiality_terms?: string;
}

export interface ApprovalWorkflow {
  required_approvals: ApprovalStep[];
  current_step: number;
  overall_status: "pending" | "approved" | "rejected" | "cancelled";
  approved_by?: string[];
  approved_at?: string;
  rejection_reason?: string;
}

export interface ApprovalStep {
  step_number: number;
  approver_role: string;
  approver_id?: string;
  required: boolean;
  status: "pending" | "approved" | "rejected" | "skipped";
  approved_at?: string;
  notes?: string;
}

export interface PODocument {
  id: string;
  type: PODocumentType;
  name: string;
  file_url: string;
  file_size: number;
  uploaded_by: string;
  uploaded_at: string;
  version: number;
  description?: string;
}

export interface Milestone {
  id: string;
  name: string;
  description: string;
  due_date: string;
  completed_date?: string;
  status: "pending" | "in_progress" | "completed" | "overdue";
  responsible_party: "buyer" | "supplier";
  dependencies?: string[];
  notes?: string;
}

export interface POAmendment {
  id: string;
  amendment_number: number;
  change_reason: string;
  changes_summary: string;
  old_values: Record<string, any>;
  new_values: Record<string, any>;
  financial_impact: number;
  schedule_impact_days: number;
  approved_by: string;
  approved_at: string;
  effective_date: string;
}

export type POStatus =
  | "draft"
  | "pending_approval"
  | "approved"
  | "sent_to_supplier"
  | "acknowledged"
  | "in_production"
  | "ready_to_ship"
  | "shipped"
  | "partially_delivered"
  | "delivered"
  | "completed"
  | "cancelled"
  | "on_hold";

export type DeliveryStatus =
  | "pending"
  | "scheduled"
  | "in_transit"
  | "delivered"
  | "failed"
  | "returned";

export type PODocumentType =
  | "purchase_order"
  | "technical_specification"
  | "terms_conditions"
  | "quality_certificate"
  | "test_report"
  | "shipping_document"
  | "invoice"
  | "receipt"
  | "amendment"
  | "correspondence";

// Media Asset Management Types
export interface MediaAsset {
  id: string;
  component_id: string;
  asset_type: MediaAssetType;
  file_name: string;
  file_size: number;
  mime_type: string;
  file_url: string;
  cdn_url?: string;
  thumbnail_url?: string;
  metadata: MediaMetadata;
  tags: string[];
  status: MediaAssetStatus;
  visibility: MediaVisibility;
  version: number;
  uploaded_by: string;
  uploaded_at: string;
  updated_at: string;
  access_history: AccessRecord[];
}

export interface MediaMetadata {
  // Document specific
  page_count?: number;
  language?: string;

  // Image specific
  dimensions?: {
    width: number;
    height: number;
    resolution_dpi?: number;
  };

  // Video specific
  duration_seconds?: number;
  frame_rate?: number;
  codec?: string;

  // Common technical metadata
  checksum_md5: string;
  checksum_sha256: string;
  original_filename: string;
  compression_ratio?: number;

  // Business metadata
  document_version?: string;
  revision_date?: string;
  expiration_date?: string;
  certification_number?: string;
  test_standard?: string;

  // AI extraction metadata
  extracted_text?: string;
  extracted_data?: Record<string, any>;
  confidence_score?: number;
  ai_processed_at?: string;
}

export interface AccessRecord {
  accessed_by: string;
  accessed_at: string;
  access_type: "view" | "download" | "share" | "edit";
  ip_address?: string;
  user_agent?: string;
}

export type MediaAssetType =
  | "datasheet"
  | "installation_guide"
  | "warranty_document"
  | "certificate"
  | "test_report"
  | "product_image"
  | "technical_drawing"
  | "video_demo"
  | "safety_document"
  | "compliance_report"
  | "performance_data"
  | "dimensional_drawing"
  | "wiring_diagram"
  | "user_manual"
  | "marketing_material"
  | "other";

export type MediaAssetStatus =
  | "uploaded"
  | "processing"
  | "processed"
  | "approved"
  | "rejected"
  | "archived"
  | "expired";

export type MediaVisibility =
  | "public"
  | "internal"
  | "restricted"
  | "confidential";

export interface MediaCollection {
  id: string;
  name: string;
  description: string;
  component_id?: string;
  asset_ids: string[];
  created_by: string;
  created_at: string;
  tags: string[];
  visibility: MediaVisibility;
}

export interface MediaProcessingJob {
  id: string;
  asset_id: string;
  job_type: ProcessingJobType;
  status: "queued" | "processing" | "completed" | "failed";
  progress_percentage: number;
  started_at: string;
  completed_at?: string;
  error_message?: string;
  output_metadata?: Record<string, any>;
}

export type ProcessingJobType =
  | "thumbnail_generation"
  | "text_extraction"
  | "data_extraction"
  | "format_conversion"
  | "compression"
  | "virus_scan"
  | "compliance_check";

export type ComponentCategory =
  | "generation"
  | "transmission"
  | "distribution"
  | "storage"
  | "monitoring"
  | "control";

export type ComponentDomain =
  | "electrical"
  | "mechanical"
  | "thermal"
  | "software"
  | "data";

export type Domain = "PV" | "BESS" | "HYBRID" | "GRID" | "MICROGRID";
export type Scale =
  | "RESIDENTIAL"
  | "COMMERCIAL"
  | "INDUSTRIAL"
  | "UTILITY"
  | "HYPERSCALE";

// Enhanced Phase 1 Types for ODL-SD v4.1 Compliance
export type LifecycleStage =
  | "development"
  | "active"
  | "mature"
  | "deprecated"
  | "obsolete"
  | "discontinued";

export type ComplianceStatus =
  | "compliant"
  | "non_compliant"
  | "pending_review"
  | "expired"
  | "not_applicable";

export interface WarrantyDetails {
  start_date?: string;
  end_date?: string;
  coverage_type?: "full" | "limited" | "extended";
  warranty_provider?: string;
  terms_conditions?: string;
  contact_info?: string;
}

export interface ComponentInventory {
  component_id: string;
  warehouse_location: string;
  quantity_available: number;
  quantity_reserved: number;
  quantity_on_order: number;
  reorder_level: number;
  reorder_quantity: number;
  unit_cost: number;
  last_updated: string;
  location_details?: {
    building?: string;
    room?: string;
    shelf?: string;
    bin?: string;
  };
}

export interface InventoryTransaction {
  id: string;
  component_id: string;
  transaction_type: "receipt" | "issue" | "transfer" | "adjustment" | "return";
  quantity: number;
  unit_cost?: number;
  from_location?: string;
  to_location?: string;
  reference_number?: string;
  notes?: string;
  created_by: string;
  created_at: string;
}

export interface DocumentResponse {
  id: string;
  project_name: string;
  domain: Domain;
  scale: Scale;
  current_version: number;
  content_hash: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface OdlDocument {
  id: string;
  project_name: string;
  domain: Domain;
  scale: Scale;
  content: any;
  metadata?: any;
  [key: string]: any;
}
