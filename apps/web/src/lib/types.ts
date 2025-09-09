export * from '@originfd/types-odl'

export interface ComponentResponse {
  id: string
  name: string
  status: ComponentStatus
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
