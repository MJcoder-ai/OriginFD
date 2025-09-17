import { NextRequest, NextResponse } from "next/server";
import { ODLComponentStatus } from "@/lib/types";

interface LifecycleTransitionRequest {
  from_status: ODLComponentStatus;
  to_status: ODLComponentStatus;
  trigger_event: string;
  trigger_data?: {
    rfq_id?: string;
    award_id?: string;
    po_id?: string;
    shipment_id?: string;
    installation_id?: string;
    [key: string]: any;
  };
  user_id: string;
  notes?: string;
}

interface LifecycleValidationRule {
  from: ODLComponentStatus;
  to: ODLComponentStatus[];
  required_conditions?: string[];
  trigger_events: string[];
  user_roles_allowed: string[];
  automatic?: boolean;
}

// ODL-SD v4.1 Component Lifecycle State Machine Rules
const LIFECYCLE_RULES: LifecycleValidationRule[] = [
  {
    from: "draft",
    to: ["approved", "cancelled"],
    trigger_events: [
      "technical_approval",
      "specification_finalized",
      "cancelled_by_user",
    ],
    user_roles_allowed: ["procurement", "engineering", "admin"],
    required_conditions: ["specifications_complete", "technical_review_passed"],
  },
  {
    from: "approved",
    to: ["available", "draft", "cancelled"],
    trigger_events: [
      "market_research_complete",
      "supplier_identified",
      "revision_required",
    ],
    user_roles_allowed: ["procurement", "admin"],
  },
  {
    from: "available",
    to: ["sourcing", "draft", "archived"],
    trigger_events: ["procurement_initiated", "rfq_created", "obsoleted"],
    user_roles_allowed: ["procurement", "admin"],
  },
  {
    from: "sourcing",
    to: ["rfq_open", "available", "cancelled"],
    trigger_events: [
      "rfq_published",
      "sourcing_cancelled",
      "supplier_not_found",
    ],
    user_roles_allowed: ["procurement", "admin"],
    required_conditions: ["rfq_created"],
  },
  {
    from: "rfq_open",
    to: ["rfq_awarded", "available", "cancelled"],
    trigger_events: ["rfq_awarded", "rfq_cancelled", "no_suitable_bids"],
    user_roles_allowed: ["procurement", "admin"],
    required_conditions: ["bids_received", "evaluation_complete"],
  },
  {
    from: "rfq_awarded",
    to: ["purchasing", "sourcing", "cancelled"],
    trigger_events: ["po_generated", "award_cancelled", "supplier_declined"],
    user_roles_allowed: ["procurement", "admin"],
    required_conditions: ["award_accepted"],
  },
  {
    from: "purchasing",
    to: ["ordered", "rfq_awarded", "cancelled"],
    trigger_events: ["po_sent_to_supplier", "po_cancelled", "po_rejected"],
    user_roles_allowed: ["procurement", "admin"],
    required_conditions: ["po_approved"],
  },
  {
    from: "ordered",
    to: ["shipped", "purchasing", "cancelled"],
    trigger_events: [
      "shipment_dispatched",
      "order_cancelled",
      "production_failed",
    ],
    user_roles_allowed: ["procurement", "supplier", "admin"],
    required_conditions: ["po_acknowledged", "production_complete"],
  },
  {
    from: "shipped",
    to: ["received", "ordered", "returned"],
    trigger_events: ["delivery_confirmed", "shipment_lost", "quality_rejected"],
    user_roles_allowed: ["procurement", "warehouse", "admin"],
    required_conditions: ["shipping_confirmation"],
  },
  {
    from: "received",
    to: ["installed", "shipped", "returned", "quarantine"],
    trigger_events: [
      "installation_started",
      "damaged_in_transit",
      "quality_failed",
      "defect_found",
    ],
    user_roles_allowed: ["installation", "quality", "admin"],
    required_conditions: ["quality_inspection_passed"],
  },
  {
    from: "installed",
    to: ["commissioned", "received", "returned"],
    trigger_events: [
      "commissioning_started",
      "installation_failed",
      "component_failed",
    ],
    user_roles_allowed: ["commissioning", "engineering", "admin"],
    required_conditions: ["installation_verified"],
  },
  {
    from: "commissioned",
    to: ["operational", "installed", "retired"],
    trigger_events: [
      "system_activated",
      "commissioning_failed",
      "premature_failure",
    ],
    user_roles_allowed: ["commissioning", "operations", "admin"],
    required_conditions: ["performance_verified", "safety_checks_passed"],
  },
  {
    from: "operational",
    to: ["warranty_active", "maintenance", "retired"],
    trigger_events: [
      "warranty_period_started",
      "maintenance_required",
      "end_of_life",
    ],
    user_roles_allowed: ["operations", "maintenance", "admin"],
    automatic: true,
  },
  {
    from: "warranty_active",
    to: ["operational", "maintenance", "retired", "returned"],
    trigger_events: [
      "warranty_claim",
      "scheduled_maintenance",
      "warranty_expired",
      "warranty_replacement",
    ],
    user_roles_allowed: ["operations", "warranty", "admin"],
  },
  {
    from: "maintenance",
    to: ["operational", "retired", "returned"],
    trigger_events: [
      "maintenance_complete",
      "beyond_repair",
      "replacement_required",
    ],
    user_roles_allowed: ["maintenance", "operations", "admin"],
  },
  {
    from: "retired",
    to: ["archived", "recycling"],
    trigger_events: ["disposal_scheduled", "recycling_initiated"],
    user_roles_allowed: ["operations", "sustainability", "admin"],
    required_conditions: ["decommissioning_complete"],
  },
  {
    from: "recycling",
    to: ["archived"],
    trigger_events: ["recycling_complete"],
    user_roles_allowed: ["sustainability", "admin"],
    automatic: true,
  },
];

function validateTransition(
  componentId: string,
  fromStatus: ODLComponentStatus,
  toStatus: ODLComponentStatus,
  triggerEvent: string,
  userRole: string = "procurement",
): { valid: boolean; errors: string[]; warnings: string[] } {
  const errors: string[] = [];
  const warnings: string[] = [];

  // Find applicable rule
  const rule = LIFECYCLE_RULES.find((r) => r.from === fromStatus);
  if (!rule) {
    errors.push(`No lifecycle rules defined for status: ${fromStatus}`);
    return { valid: false, errors, warnings };
  }

  // Check if target status is allowed
  if (!rule.to.includes(toStatus)) {
    errors.push(
      `Invalid transition from ${fromStatus} to ${toStatus}. Allowed transitions: ${rule.to.join(", ")}`,
    );
    return { valid: false, errors, warnings };
  }

  // Check if trigger event is valid
  if (!rule.trigger_events.includes(triggerEvent)) {
    errors.push(
      `Invalid trigger event: ${triggerEvent}. Allowed events: ${rule.trigger_events.join(", ")}`,
    );
    return { valid: false, errors, warnings };
  }

  // Check user role permissions
  if (!rule.user_roles_allowed.includes(userRole)) {
    errors.push(
      `User role ${userRole} not authorized for this transition. Allowed roles: ${rule.user_roles_allowed.join(", ")}`,
    );
    return { valid: false, errors, warnings };
  }

  return { valid: true, errors, warnings };
}

function getNextPossibleStates(
  currentStatus: ODLComponentStatus,
): ODLComponentStatus[] {
  const rule = LIFECYCLE_RULES.find((r) => r.from === currentStatus);
  return rule ? rule.to : [];
}

export async function POST(
  request: NextRequest,
  { params }: { params: { componentId: string } },
) {
  try {
    const { componentId } = params;
    const transitionRequest: LifecycleTransitionRequest = await request.json();

    // Validate the transition
    const validation = validateTransition(
      componentId,
      transitionRequest.from_status,
      transitionRequest.to_status,
      transitionRequest.trigger_event,
      "procurement", // In real implementation, derive from authenticated user
    );

    if (!validation.valid) {
      return NextResponse.json(
        {
          success: false,
          errors: validation.errors,
          warnings: validation.warnings,
        },
        { status: 400 },
      );
    }

    const transitionTimestamp = new Date().toISOString();
    const transition = {
      from: transitionRequest.from_status,
      to: transitionRequest.to_status,
      timestamp: transitionTimestamp,
      trigger_event: transitionRequest.trigger_event,
      user_id: transitionRequest.user_id,
      notes: transitionRequest.notes,
    };

    const result = {
      success: true,
      component_id: componentId,
      transition,
      updated_component: {
        current_status: transitionRequest.to_status,
        status_updated_at: transitionTimestamp,
      },
      next_possible_states: getNextPossibleStates(transitionRequest.to_status),
      warnings:
        validation.warnings.length > 0 ? validation.warnings : undefined,
    };

    console.log(
      `Component ${componentId} transitioned from ${transitionRequest.from_status} to ${transitionRequest.to_status}`,
    );

    return NextResponse.json(result);
  } catch (error) {
    console.error("Error processing lifecycle transition:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 },
    );
  }
}

export async function GET(
  request: NextRequest,
  { params }: { params: { componentId: string } },
) {
  try {
    const { componentId } = params;
    const { searchParams } = new URL(request.url);
    const currentStatus = searchParams.get(
      "current_status",
    ) as ODLComponentStatus;

    if (!currentStatus) {
      return NextResponse.json(
        { error: "current_status parameter is required" },
        { status: 400 },
      );
    }

    const nextStates = getNextPossibleStates(currentStatus);
    const rule = LIFECYCLE_RULES.find((r) => r.from === currentStatus);

    const response = {
      component_id: componentId,
      current_status: currentStatus,
      next_possible_states: nextStates,
      available_transitions: rule
        ? rule.trigger_events.map((event) => ({
            trigger_event: event,
            allowed_target_states: nextStates,
            user_roles_allowed: rule.user_roles_allowed,
            required_conditions: rule.required_conditions || [],
          }))
        : [],
      lifecycle_rules: {
        total_states: LIFECYCLE_RULES.length,
        automatic_transitions: LIFECYCLE_RULES.filter((r) => r.automatic)
          .length,
      },
    };

    return NextResponse.json(response);
  } catch (error) {
    console.error("Error fetching lifecycle information:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 },
    );
  }
}
