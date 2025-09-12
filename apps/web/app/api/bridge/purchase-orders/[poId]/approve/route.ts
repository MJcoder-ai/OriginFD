import { NextRequest, NextResponse } from 'next/server'
import { ApprovalStep } from '@/lib/types'

interface ApprovalRequest {
  approver_id: string
  approver_role: string
  action: 'approve' | 'reject'
  notes?: string
}

export async function POST(
  request: NextRequest,
  { params }: { params: { poId: string } }
) {
  try {
    const { poId } = params
    const approvalData: ApprovalRequest = await request.json()

    // Validate required fields
    if (!approvalData.approver_id || !approvalData.action) {
      return NextResponse.json(
        { error: 'Missing required fields: approver_id, action' },
        { status: 400 }
      )
    }

    // Mock PO lookup (in real implementation, query database)
    const mockPO = {
      id: poId,
      po_number: 'PO-2025-002',
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
        overall_status: 'pending' as const
      }
    }

    // Find current approval step
    const currentStep = mockPO.approval_workflow.required_approvals.find(
      step => step.step_number === mockPO.approval_workflow.current_step
    )

    if (!currentStep) {
      return NextResponse.json(
        { error: 'No pending approval step found' },
        { status: 400 }
      )
    }

    // Update approval step
    const updatedStep: ApprovalStep = {
      ...currentStep,
      approver_id: approvalData.approver_id,
      status: approvalData.action === 'approve' ? 'approved' : 'rejected',
      approved_at: new Date().toISOString(),
      notes: approvalData.notes
    }

    let newStatus = mockPO.status
    let overallStatus = mockPO.approval_workflow.overall_status
    let nextStep = mockPO.approval_workflow.current_step

    if (approvalData.action === 'reject') {
      // If rejected, stop the workflow
      newStatus = 'cancelled'
      overallStatus = 'rejected'
    } else if (approvalData.action === 'approve') {
      // If approved, check if more steps are needed
      const hasMoreSteps = mockPO.approval_workflow.required_approvals
        .some(step => step.step_number > mockPO.approval_workflow.current_step)
      
      if (hasMoreSteps) {
        nextStep = mockPO.approval_workflow.current_step + 1
        overallStatus = 'pending'
      } else {
        // All approvals complete
        newStatus = 'approved'
        overallStatus = 'approved'
      }
    }

    const approvalResult = {
      po_id: poId,
      step_approved: updatedStep,
      new_status: newStatus,
      approval_workflow: {
        ...mockPO.approval_workflow,
        current_step: nextStep,
        overall_status: overallStatus,
        approved_by: approvalData.action === 'approve' 
          ? [...(mockPO.approval_workflow.approved_by || []), approvalData.approver_id]
          : mockPO.approval_workflow.approved_by,
        approved_at: overallStatus === 'approved' ? new Date().toISOString() : undefined,
        rejection_reason: approvalData.action === 'reject' ? approvalData.notes : undefined
      },
      next_actions: getNextActions(newStatus, overallStatus)
    }

    console.log(`PO ${mockPO.po_number} ${approvalData.action} by ${approvalData.approver_role}`)
    return NextResponse.json(approvalResult)
  } catch (error) {
    console.error('Error processing PO approval:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

function getNextActions(status: string, approvalStatus: string): string[] {
  if (status === 'cancelled') {
    return ['Review rejection reason', 'Revise PO if needed', 'Resubmit for approval']
  }
  
  if (status === 'approved') {
    return [
      'Send PO to supplier',
      'Await supplier acknowledgment',
      'Setup milestone tracking',
      'Activate delivery schedule'
    ]
  }
  
  if (approvalStatus === 'pending') {
    return ['Waiting for next level approval']
  }
  
  return []
}