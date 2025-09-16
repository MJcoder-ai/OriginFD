import { NextRequest, NextResponse } from 'next/server'
import { POStatus, Milestone } from '@/lib/types'

interface StatusUpdateRequest {
  new_status: POStatus
  updated_by: string
  notes?: string
  milestone_updates?: {
    milestone_id: string
    status: 'pending' | 'in_progress' | 'completed' | 'overdue'
    completed_date?: string
    notes?: string
  }[]
}

interface StatusUpdateResponse {
  po_id: string
  old_status: POStatus
  new_status: POStatus
  updated_at: string
  updated_by: string
  component_lifecycle_impact?: {
    should_update_component_status: boolean
    recommended_component_status?: string
    reason?: string
  }
  next_actions: string[]
  notifications: {
    recipients: string[]
    message: string
  }[]
}

export async function PATCH(
  request: NextRequest,
  { params }: { params: { poId: string } }
) {
  try {
    const { poId } = params
    const updateData: StatusUpdateRequest = await request.json()

    // Validate required fields
    if (!updateData.new_status || !updateData.updated_by) {
      return NextResponse.json(
        { error: 'Missing required fields: new_status, updated_by' },
        { status: 400 }
      )
    }

    // Mock PO lookup (in real implementation, query database)
    const mockPO = {
      id: poId,
      po_number: 'PO-2025-001',
      status: 'acknowledged' as POStatus,
      component_id: 'comp_001',
      supplier: {
        name: 'JinkoSolar',
        contact: { email: 'sales@jinkosolar.com' }
      },
      buyer_contact: {
        name: 'Sarah Johnson',
        email: 'sarah.johnson@originfd.com'
      }
    }

    const oldStatus = mockPO.status
    const newStatus = updateData.new_status

    // Validate status transition
    const validTransitions = getValidStatusTransitions(oldStatus)
    if (!validTransitions.includes(newStatus)) {
      return NextResponse.json(
        { error: `Invalid status transition from ${oldStatus} to ${newStatus}` },
        { status: 400 }
      )
    }

    // Update milestones if provided
    if (updateData.milestone_updates) {
      // In real implementation, update milestone records
      console.log('Updating milestones:', updateData.milestone_updates)
    }

    // Determine component lifecycle impact
    const componentImpact = getComponentLifecycleImpact(newStatus, mockPO.component_id)

    // Determine notifications
    const notifications = getStatusChangeNotifications(oldStatus, newStatus, mockPO)

    // Get next actions
    const nextActions = getNextActionsForStatus(newStatus)

    const updateResult: StatusUpdateResponse = {
      po_id: poId,
      old_status: oldStatus,
      new_status: newStatus,
      updated_at: new Date().toISOString(),
      updated_by: updateData.updated_by,
      component_lifecycle_impact: componentImpact,
      next_actions: nextActions,
      notifications
    }

    // In real implementation:
    // 1. Update PO record in database
    // 2. Update milestone records if provided
    // 3. Trigger component status update if needed
    // 4. Send notifications
    // 5. Log audit trail

    console.log(`PO ${mockPO.po_number} status updated: ${oldStatus} → ${newStatus}`)
    return NextResponse.json(updateResult)
  } catch (error) {
    console.error('Error updating PO status:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

function getValidStatusTransitions(currentStatus: POStatus): POStatus[] {
  const transitions: Record<POStatus, POStatus[]> = {
    'draft': ['pending_approval', 'cancelled'],
    'pending_approval': ['approved', 'cancelled'],
    'approved': ['sent_to_supplier', 'cancelled'],
    'sent_to_supplier': ['acknowledged', 'cancelled'],
    'acknowledged': ['in_production', 'on_hold', 'cancelled'],
    'in_production': ['ready_to_ship', 'on_hold', 'cancelled'],
    'ready_to_ship': ['shipped', 'on_hold', 'cancelled'],
    'shipped': ['partially_delivered', 'delivered', 'cancelled'],
    'partially_delivered': ['delivered', 'cancelled'],
    'delivered': ['completed', 'cancelled'],
    'completed': [],
    'cancelled': ['draft'], // Allow recreation
    'on_hold': ['acknowledged', 'in_production', 'ready_to_ship', 'cancelled']
  }

  return transitions[currentStatus] || []
}

function getComponentLifecycleImpact(poStatus: POStatus, componentId: string) {
  switch (poStatus) {
    case 'acknowledged':
      return {
        should_update_component_status: true,
        recommended_component_status: 'purchasing',
        reason: 'PO acknowledged by supplier'
      }
    case 'in_production':
      return {
        should_update_component_status: true,
        recommended_component_status: 'ordered',
        reason: 'Component in production'
      }
    case 'shipped':
      return {
        should_update_component_status: true,
        recommended_component_status: 'shipped',
        reason: 'Component shipped from supplier'
      }
    case 'delivered':
      return {
        should_update_component_status: true,
        recommended_component_status: 'received',
        reason: 'Component delivered and received'
      }
    case 'completed':
      return {
        should_update_component_status: true,
        recommended_component_status: 'available',
        reason: 'PO completed, component available for use'
      }
    default:
      return {
        should_update_component_status: false,
        reason: 'Status change does not affect component lifecycle'
      }
  }
}

function getStatusChangeNotifications(oldStatus: POStatus, newStatus: POStatus, po: any) {
  const notifications = []

  // Always notify buyer
  notifications.push({
    recipients: [po.buyer_contact.email],
    message: `PO ${po.po_number} status updated from ${oldStatus} to ${newStatus}`
  })

  // Notify supplier for certain status changes
  if (['sent_to_supplier', 'cancelled', 'on_hold'].includes(newStatus)) {
    notifications.push({
      recipients: [po.supplier.contact.email],
      message: `PO ${po.po_number} status updated to ${newStatus}`
    })
  }

  // Notify warehouse for delivery-related updates
  if (['shipped', 'delivered'].includes(newStatus)) {
    notifications.push({
      recipients: ['warehouse@originfd.com'],
      message: `PO ${po.po_number} - Component ${newStatus}, prepare for receipt`
    })
  }

  return notifications
}

function getNextActionsForStatus(status: POStatus): string[] {
  const actionMap: Record<POStatus, string[]> = {
    'draft': ['Complete PO details', 'Submit for approval'],
    'pending_approval': ['Wait for approver action'],
    'approved': ['Send to supplier', 'Setup milestone tracking'],
    'sent_to_supplier': ['Await supplier acknowledgment'],
    'acknowledged': ['Monitor production progress', 'Track milestones'],
    'in_production': ['Quality assurance monitoring', 'Prepare for shipment'],
    'ready_to_ship': ['Coordinate delivery logistics', 'Prepare receiving'],
    'shipped': ['Track shipment', 'Prepare receiving team'],
    'partially_delivered': ['Verify partial delivery', 'Track remaining items'],
    'delivered': ['Verify complete delivery', 'Update inventory', 'Process invoices'],
    'completed': ['Archive PO', 'Supplier performance review'],
    'cancelled': ['Review cancellation reason', 'Handle supplier coordination'],
    'on_hold': ['Review hold reason', 'Coordinate resolution', 'Update timeline']
  }

  return actionMap[status] || []
}