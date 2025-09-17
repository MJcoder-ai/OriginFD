import { ODLComponentStatus } from './types'

// ODL-SD v4.1 Component Lifecycle State Machine
export class ComponentLifecycleManager {
  private static readonly STATUS_TRANSITIONS: Record<ODLComponentStatus, ODLComponentStatus[]> = {
    'draft': ['parsed', 'archived'],
    'parsed': ['enriched', 'draft', 'archived'],
    'enriched': ['dedupe_pending', 'parsed', 'archived'],
    'dedupe_pending': ['compliance_pending', 'enriched', 'archived'],
    'compliance_pending': ['approved', 'dedupe_pending', 'archived'],
    'approved': ['available', 'compliance_pending', 'archived'],
    'available': ['rfq_open', 'sourcing', 'approved', 'installed', 'archived'],
    'sourcing': ['available', 'rfq_open', 'archived'],
    'rfq_open': ['rfq_awarded', 'available', 'archived'],
    'rfq_awarded': ['purchasing', 'available', 'archived'],
    'purchasing': ['ordered', 'available', 'archived'],
    'ordered': ['shipped', 'purchasing', 'archived'],
    'shipped': ['received', 'ordered', 'archived'],
    'received': ['installed', 'available', 'archived'],
    'installed': ['commissioned', 'received', 'operational', 'retired'],
    'commissioned': ['operational', 'installed', 'retired'],
    'operational': ['warranty_active', 'maintenance', 'commissioned', 'retired'],
    'warranty_active': ['operational', 'maintenance', 'retired'],
    'maintenance': ['operational', 'warranty_active', 'quarantine'],
    'retired': ['recycling', 'archived'],
    'recycling': ['archived'],
    'quarantine': ['maintenance', 'returned', 'archived'],
    'returned': ['available', 'quarantine', 'archived'],
    'cancelled': ['archived'],
    'archived': [] // Terminal state
  }

  private static readonly STATUS_METADATA = {
    'draft': {
      label: 'Draft',
      description: 'Initial component record created, basic information captured',
      color: 'gray',
      stage: 'planning',
      required_actions: ['Complete component identity', 'Upload datasheet'],
      stakeholders: ['data_entry', 'technical_review']
    },
    'parsed': {
      label: 'Parsed',
      description: 'Datasheet parsed and technical specifications extracted',
      color: 'blue',
      stage: 'data_processing',
      required_actions: ['Review parsed data', 'Assign classification'],
      stakeholders: ['technical_review', 'data_quality']
    },
    'enriched': {
      label: 'Enriched',
      description: 'Additional data enrichment completed, classifications assigned',
      color: 'cyan',
      stage: 'data_processing',
      required_actions: ['Initiate duplicate check', 'Validate classifications'],
      stakeholders: ['data_quality', 'procurement']
    },
    'dedupe_pending': {
      label: 'Duplicate Check',
      description: 'Duplicate detection process in progress',
      color: 'yellow',
      stage: 'quality_control',
      required_actions: ['Complete duplicate analysis', 'Resolve duplicates'],
      stakeholders: ['data_quality', 'technical_review']
    },
    'compliance_pending': {
      label: 'Compliance Review',
      description: 'Compliance and certification review in progress',
      color: 'orange',
      stage: 'quality_control',
      required_actions: ['Validate certificates', 'Verify compliance'],
      stakeholders: ['compliance_officer', 'quality_assurance']
    },
    'approved': {
      label: 'Approved',
      description: 'Component approved for procurement and use',
      color: 'green',
      stage: 'approved',
      required_actions: ['Setup inventory tracking', 'Configure availability'],
      stakeholders: ['procurement', 'inventory_manager']
    },
    'available': {
      label: 'Available',
      description: 'Component available for procurement or direct installation',
      color: 'emerald',
      stage: 'procurement',
      required_actions: ['Create RFQ when needed', 'Monitor inventory levels'],
      stakeholders: ['procurement', 'project_manager']
    },
    'rfq_open': {
      label: 'RFQ Open',
      description: 'Request for Quote published, receiving supplier bids',
      color: 'violet',
      stage: 'procurement',
      required_actions: ['Evaluate bids', 'Select supplier'],
      stakeholders: ['procurement', 'technical_evaluation']
    },
    'rfq_awarded': {
      label: 'RFQ Awarded',
      description: 'Supplier selected, preparing purchase order',
      color: 'purple',
      stage: 'procurement',
      required_actions: ['Generate PO', 'Negotiate terms'],
      stakeholders: ['procurement', 'finance']
    },
    'purchasing': {
      label: 'Purchasing',
      description: 'Purchase order in progress, awaiting supplier acknowledgment',
      color: 'indigo',
      stage: 'ordering',
      required_actions: ['Confirm PO details', 'Track supplier response'],
      stakeholders: ['procurement', 'supplier_relations']
    },
    'ordered': {
      label: 'Ordered',
      description: 'Order confirmed by supplier, production/manufacturing in progress',
      color: 'blue',
      stage: 'ordering',
      required_actions: ['Monitor production', 'Prepare logistics'],
      stakeholders: ['procurement', 'logistics', 'supplier_relations']
    },
    'shipped': {
      label: 'Shipped',
      description: 'Component shipped from supplier, in transit',
      color: 'sky',
      stage: 'logistics',
      required_actions: ['Track shipment', 'Prepare receiving'],
      stakeholders: ['logistics', 'warehouse', 'receiving']
    },
    'received': {
      label: 'Received',
      description: 'Component received and inspected, ready for installation',
      color: 'teal',
      stage: 'inventory',
      required_actions: ['Update inventory', 'Quality inspection'],
      stakeholders: ['warehouse', 'quality_assurance', 'project_manager']
    },
    'installed': {
      label: 'Installed',
      description: 'Component physically installed in project location',
      color: 'green',
      stage: 'deployment',
      required_actions: ['System integration', 'Initial testing'],
      stakeholders: ['installation_team', 'project_manager', 'commissioning']
    },
    'commissioned': {
      label: 'Commissioned',
      description: 'Component commissioned and tested, ready for operation',
      color: 'emerald',
      stage: 'deployment',
      required_actions: ['Performance verification', 'Final acceptance'],
      stakeholders: ['commissioning', 'operations', 'customer']
    },
    'operational': {
      label: 'Operational',
      description: 'Component in active service, performing as expected',
      color: 'lime',
      stage: 'operations',
      required_actions: ['Performance monitoring', 'Preventive maintenance'],
      stakeholders: ['operations', 'maintenance', 'monitoring']
    },
    'warranty_active': {
      label: 'Under Warranty',
      description: 'Component operational with active warranty coverage',
      color: 'green',
      stage: 'operations',
      required_actions: ['Monitor warranty terms', 'Track performance'],
      stakeholders: ['operations', 'warranty_manager', 'maintenance']
    },
    'retired': {
      label: 'Retired',
      description: 'Component end-of-life, removed from active service',
      color: 'red',
      stage: 'end_of_life',
      required_actions: ['Decommission', 'Asset disposal planning'],
      stakeholders: ['operations', 'maintenance', 'asset_management']
    },
    'sourcing': {
      label: 'Sourcing',
      description: 'Actively sourcing component from suppliers',
      color: 'blue',
      stage: 'procurement',
      required_actions: ['Contact suppliers', 'Compare quotes'],
      stakeholders: ['procurement', 'sourcing']
    },
    'maintenance': {
      label: 'Maintenance',
      description: 'Component undergoing scheduled or corrective maintenance',
      color: 'orange',
      stage: 'operations',
      required_actions: ['Complete maintenance', 'Update records'],
      stakeholders: ['maintenance', 'operations']
    },
    'recycling': {
      label: 'Recycling',
      description: 'Component being processed for material recovery',
      color: 'green',
      stage: 'end_of_life',
      required_actions: ['Material separation', 'Recovery tracking'],
      stakeholders: ['recycling', 'environmental']
    },
    'quarantine': {
      label: 'Quarantine',
      description: 'Component isolated due to quality or safety concerns',
      color: 'red',
      stage: 'operations',
      required_actions: ['Investigation', 'Quality assessment'],
      stakeholders: ['quality_assurance', 'safety']
    },
    'returned': {
      label: 'Returned',
      description: 'Component returned from field, awaiting disposition',
      color: 'yellow',
      stage: 'procurement',
      required_actions: ['Inspection', 'Disposition decision'],
      stakeholders: ['returns', 'quality_assurance']
    },
    'cancelled': {
      label: 'Cancelled',
      description: 'Component procurement or deployment cancelled',
      color: 'red',
      stage: 'procurement',
      required_actions: ['Cancel orders', 'Update records'],
      stakeholders: ['procurement', 'project_management']
    },
    'archived': {
      label: 'Archived',
      description: 'Component record archived, all lifecycle activities complete',
      color: 'gray',
      stage: 'archived',
      required_actions: ['Record retention', 'Historical reference'],
      stakeholders: ['records_management', 'compliance']
    }
  } as const

  static getValidTransitions(currentStatus: ODLComponentStatus): ODLComponentStatus[] {
    return this.STATUS_TRANSITIONS[currentStatus] || []
  }

  static isValidTransition(from: ODLComponentStatus, to: ODLComponentStatus): boolean {
    const validTransitions = this.getValidTransitions(from)
    return validTransitions.includes(to)
  }

  static getStatusMetadata(status: ODLComponentStatus) {
    return this.STATUS_METADATA[status]
  }

  static getStatusDisplay(status: ODLComponentStatus) {
    const metadata = this.getStatusMetadata(status)
    return {
      status,
      label: metadata.label,
      description: metadata.description,
      color: metadata.color,
      stage: metadata.stage
    }
  }

  static getLifecycleStages() {
    return [
      { stage: 'planning', label: 'Planning', color: 'gray' },
      { stage: 'data_processing', label: 'Data Processing', color: 'blue' },
      { stage: 'quality_control', label: 'Quality Control', color: 'yellow' },
      { stage: 'approved', label: 'Approved', color: 'green' },
      { stage: 'procurement', label: 'Procurement', color: 'purple' },
      { stage: 'ordering', label: 'Ordering', color: 'indigo' },
      { stage: 'logistics', label: 'Logistics', color: 'sky' },
      { stage: 'inventory', label: 'Inventory', color: 'teal' },
      { stage: 'deployment', label: 'Deployment', color: 'emerald' },
      { stage: 'operations', label: 'Operations', color: 'lime' },
      { stage: 'end_of_life', label: 'End of Life', color: 'red' },
      { stage: 'archived', label: 'Archived', color: 'gray' }
    ]
  }

  static getStakeholdersForStatus(status: ODLComponentStatus): string[] {
    const metadata = this.getStatusMetadata(status)
    return [...metadata.stakeholders]
  }

  static getRequiredActionsForStatus(status: ODLComponentStatus): string[] {
    const metadata = this.getStatusMetadata(status)
    return [...metadata.required_actions]
  }

  static getStatusesByStage(stage: string): ODLComponentStatus[] {
    return Object.entries(this.STATUS_METADATA)
      .filter(([_, metadata]) => metadata.stage === stage)
      .map(([status, _]) => status as ODLComponentStatus)
  }

  static getProgressPercentage(status: ODLComponentStatus): number {
    const statusOrder: ODLComponentStatus[] = [
      'draft', 'parsed', 'enriched', 'dedupe_pending', 'compliance_pending',
      'approved', 'available', 'rfq_open', 'rfq_awarded', 'purchasing',
      'ordered', 'shipped', 'received', 'installed', 'commissioned',
      'operational', 'warranty_active', 'retired', 'archived'
    ]

    const index = statusOrder.indexOf(status)
    if (index === -1) return 0

    return Math.round((index / (statusOrder.length - 1)) * 100)
  }

  static canTransitionTo(currentStatus: ODLComponentStatus, targetStatus: ODLComponentStatus): {
    allowed: boolean
    path?: ODLComponentStatus[]
    reason?: string
  } {
    if (!this.isValidTransition(currentStatus, targetStatus)) {
      // Try to find a path through multiple transitions
      const path = this.findTransitionPath(currentStatus, targetStatus)
      if (path.length > 0) {
        return {
          allowed: true,
          path: path,
          reason: `Requires ${path.length - 1} intermediate transitions`
        }
      }

      return {
        allowed: false,
        reason: `No valid transition path from ${currentStatus} to ${targetStatus}`
      }
    }

    return { allowed: true }
  }

  private static findTransitionPath(from: ODLComponentStatus, to: ODLComponentStatus, visited: Set<ODLComponentStatus> = new Set(), path: ODLComponentStatus[] = []): ODLComponentStatus[] {
    if (from === to) {
      return [...path, to]
    }

    if (visited.has(from) || path.length > 10) { // Prevent infinite loops and excessive paths
      return []
    }

    visited.add(from)
    const currentPath = [...path, from]

    for (const nextStatus of this.getValidTransitions(from)) {
      const result = this.findTransitionPath(nextStatus, to, new Set(visited), currentPath)
      if (result.length > 0) {
        return result
      }
    }

    return []
  }
}

// Helper functions for UI components
export const getStatusBadgeProps = (status: ODLComponentStatus) => {
  const display = ComponentLifecycleManager.getStatusDisplay(status)
  return {
    variant: 'outline' as const,
    className: `border-${display.color}-200 bg-${display.color}-50 text-${display.color}-700`,
    children: display.label
  }
}

export const getProgressColor = (status: ODLComponentStatus): string => {
  const metadata = ComponentLifecycleManager.getStatusMetadata(status)
  return metadata.color
}
