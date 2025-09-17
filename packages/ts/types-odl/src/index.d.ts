/**
 * TypeScript types for ODL-SD v4.1 documents
 * Generated from Python Pydantic models
 */
import * as React from "react";
export type Domain = "PV" | "BESS" | "HYBRID" | "GRID" | "MICROGRID";
export type Scale =
  | "RESIDENTIAL"
  | "COMMERCIAL"
  | "INDUSTRIAL"
  | "UTILITY"
  | "HYPERSCALE";
export type UnitSystem = "SI" | "IMPERIAL";
export type HierarchyType =
  | "PORTFOLIO"
  | "SITE"
  | "PLANT"
  | "BLOCK"
  | "ARRAY"
  | "STRING"
  | "DEVICE";
export type TaskStatus =
  | "pending"
  | "planning"
  | "executing"
  | "reviewing"
  | "completed"
  | "failed"
  | "cancelled";
export type TaskPriority = "low" | "normal" | "high" | "urgent";
export interface Units {
  system: UnitSystem;
  currency: string;
  coordinate_system: string;
}
export interface Timestamps {
  created_at: string;
  updated_at: string;
  valid_from?: string;
  valid_until?: string;
}
export interface Versioning {
  document_version: string;
  content_hash: string;
  previous_hash?: string;
  change_summary?: string;
}
export interface DocumentMeta {
  project: string;
  portfolio_id?: string;
  domain: Domain;
  scale: Scale;
  units: Units;
  timestamps: Timestamps;
  versioning: Versioning;
}
export interface Portfolio {
  id: string;
  name: string;
  total_capacity_gw: number;
  regions: Record<string, any>;
}
export interface Site {
  id: string;
  name: string;
  location: {
    lat: number;
    lon: number;
    elevation?: number;
  };
  timezone: string;
  capacity_mw: number;
}
export interface Plant {
  id: string;
  name: string;
  site_id: string;
  plant_type: string;
  capacity_mw: number;
  interconnection_voltage_kv: number;
}
export interface Block {
  id: string;
  name: string;
  plant_id: string;
  capacity_mw: number;
  dc_ac_ratio?: number;
}
export interface Hierarchy {
  type: HierarchyType;
  id: string;
  parent_id?: string;
  children: string[];
  portfolio?: Portfolio;
  site?: Site;
  plant?: Plant;
  block?: Block;
}
export interface ComponentInstance {
  id: string;
  component_id: string;
  name?: string;
  location?: any;
  parameters: Record<string, any>;
  status: string;
}
export interface Connection {
  id: string;
  from_instance_id: string;
  from_port: string;
  to_instance_id: string;
  to_port: string;
  connection_type: string;
  parameters?: Record<string, any>;
}
export interface Analysis {
  id: string;
  type: string;
  version: string;
  inputs: Record<string, any>;
  outputs: Record<string, any>;
  timestamp: string;
  status: string;
}
export interface DataManagement {
  partitioning_enabled: boolean;
  partition_strategy?: string;
  external_refs_enabled: boolean;
  streaming_enabled: boolean;
  max_document_size_mb: number;
}
export interface AuditEntry {
  timestamp: string;
  action: string;
  actor: string;
  version: number;
  details: Record<string, any>;
}
export interface OdlDocument {
  $schema: string;
  schema_version: string;
  meta: DocumentMeta;
  hierarchy?: Hierarchy;
  requirements?: Record<string, any>;
  libraries: Record<string, any>;
  instances: ComponentInstance[];
  connections: Connection[];
  structures?: Record<string, any>;
  physical?: Record<string, any>;
  analysis: Analysis[];
  compliance?: Record<string, any>;
  finance?: Record<string, any>;
  operations?: Record<string, any>;
  esg?: Record<string, any>;
  governance?: Record<string, any>;
  external_models?: Record<string, any>;
  audit: AuditEntry[];
  data_management: DataManagement;
}
export interface LoginRequest {
  email: string;
  password: string;
}
export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}
export interface UserResponse {
  id: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  roles: string[];
}
export interface DocumentCreateRequest {
  project_name: string;
  portfolio_id?: string;
  domain: Domain;
  scale: Scale;
  document_data: OdlDocument;
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
export interface PatchOperation {
  op: "add" | "remove" | "replace" | "move" | "copy" | "test";
  path: string;
  value?: any;
  from?: string;
}
export interface PatchRequest {
  doc_id: string;
  doc_version: number;
  patch: PatchOperation[];
  evidence: string[];
  dry_run: boolean;
  change_summary?: string;
}
export interface PatchResponse {
  success: boolean;
  doc_version: number;
  content_hash: string;
  inverse_patch: PatchOperation[];
  applied_at: string;
}
export interface DocumentVersion {
  version_number: number;
  content_hash: string;
  change_summary?: string;
  created_by: string;
  created_at: string;
  patch_operations_count: number;
}
export interface Task {
  id: string;
  type: string;
  description: string;
  status: TaskStatus;
  priority: TaskPriority;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  errors: string[];
  patches_generated: number;
}
export interface ToolMetadata {
  name: string;
  version: string;
  description: string;
  category: string;
  inputs_schema: Record<string, any>;
  outputs_schema: Record<string, any>;
  side_effects: string;
  rbac_scope: string[];
  execution_time_estimate_ms: number;
  psu_cost_estimate: number;
  tags: string[];
}
export interface ToolResult {
  success: boolean;
  execution_time_ms: number;
  outputs: Record<string, any>;
  errors: string[];
  evidence: string[];
  intent?: string;
}
export interface UseApiOptions {
  retry?: number;
  retryDelay?: number;
  onError?: (error: Error) => void;
  onSuccess?: (data: any) => void;
}
export interface UseMutationOptions<TData, TVariables> {
  onSuccess?: (data: TData, variables: TVariables) => void;
  onError?: (error: Error, variables: TVariables) => void;
  onSettled?: (
    data: TData | undefined,
    error: Error | null,
    variables: TVariables,
  ) => void;
}
export interface BaseComponentProps {
  className?: string;
  children?: React.ReactNode;
}
export interface LoadingProps extends BaseComponentProps {
  size?: "sm" | "md" | "lg";
  text?: string;
}
export interface ErrorBoundaryProps extends BaseComponentProps {
  fallback?: React.ComponentType<{
    error: Error;
    resetError: () => void;
  }>;
  onError?: (error: Error, errorInfo: any) => void;
}
//# sourceMappingURL=index.d.ts.map
