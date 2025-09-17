import { NextRequest, NextResponse } from "next/server";
import { ODLComponentStatus } from "@/lib/types";

interface WorkflowValidationRequest {
  component_id: string;
  current_status: ODLComponentStatus;
  target_status?: ODLComponentStatus;
  validate_full_workflow?: boolean;
}

interface WorkflowStep {
  stage: ODLComponentStatus;
  name: string;
  description: string;
  required_actions: string[];
  key_stakeholders: string[];
  prerequisites: string[];
  outputs: string[];
  estimated_duration: string;
  automation_level: "manual" | "semi-automated" | "automated";
  integrations: string[];
}

interface ValidationResult {
  is_valid: boolean;
  current_stage: WorkflowStep;
  next_possible_stages: WorkflowStep[];
  workflow_completion: number; // 0-100%
  missing_prerequisites: string[];
  recommendations: string[];
  warnings: string[];
  integration_status: {
    rfq_system: boolean;
    purchase_orders: boolean;
    lifecycle_transitions: boolean;
    media_management: boolean;
    inventory_tracking: boolean;
  };
}

// Complete ODL-SD v4.1 Component Lifecycle Workflow Definition
const WORKFLOW_STAGES: WorkflowStep[] = [
  {
    stage: "draft",
    name: "Specification Development",
    description:
      "Initial component specification and technical requirements definition",
    required_actions: [
      "Define technical specifications",
      "Conduct market research",
      "Create component classification",
      "Prepare initial documentation",
    ],
    key_stakeholders: ["Engineering", "Product Management", "Procurement"],
    prerequisites: [],
    outputs: [
      "Technical specification document",
      "Component classification (UNSPSC)",
      "Initial cost estimates",
    ],
    estimated_duration: "1-2 weeks",
    automation_level: "manual",
    integrations: ["media_management"],
  },
  {
    stage: "approved",
    name: "Technical Approval",
    description: "Engineering review and approval of component specifications",
    required_actions: [
      "Technical review and validation",
      "Standards compliance verification",
      "Design review approval",
      "Risk assessment completion",
    ],
    key_stakeholders: ["Engineering", "Quality", "Compliance"],
    prerequisites: [
      "Complete technical specifications",
      "Standards compliance verification",
      "Risk assessment",
    ],
    outputs: [
      "Approved technical specification",
      "Compliance checklist",
      "Design review report",
    ],
    estimated_duration: "3-5 business days",
    automation_level: "semi-automated",
    integrations: ["lifecycle_transitions", "media_management"],
  },
  {
    stage: "available",
    name: "Market Availability",
    description: "Component approved for procurement and sourcing activities",
    required_actions: [
      "Market research completion",
      "Supplier database update",
      "Pricing baseline establishment",
      "Availability confirmation",
    ],
    key_stakeholders: ["Procurement", "Supply Chain", "Engineering"],
    prerequisites: [
      "Technical approval",
      "Market research data",
      "Supplier qualification criteria",
    ],
    outputs: [
      "Market research report",
      "Qualified supplier list",
      "Pricing baseline",
    ],
    estimated_duration: "1-2 weeks",
    automation_level: "semi-automated",
    integrations: ["lifecycle_transitions"],
  },
  {
    stage: "sourcing",
    name: "Strategic Sourcing",
    description:
      "Active sourcing and supplier engagement for component procurement",
    required_actions: [
      "Supplier identification and qualification",
      "RFQ preparation",
      "Negotiation strategy development",
      "Contract terms preparation",
    ],
    key_stakeholders: ["Procurement", "Legal", "Finance"],
    prerequisites: [
      "Approved component specification",
      "Market availability confirmation",
      "Budget approval",
    ],
    outputs: [
      "Qualified supplier shortlist",
      "RFQ documentation",
      "Negotiation parameters",
    ],
    estimated_duration: "2-3 weeks",
    automation_level: "manual",
    integrations: ["rfq_system"],
  },
  {
    stage: "rfq_open",
    name: "RFQ Bidding Process",
    description: "Active RFQ with suppliers submitting competitive bids",
    required_actions: [
      "RFQ distribution to qualified suppliers",
      "Bid clarification and Q&A management",
      "Bid collection and validation",
      "Preliminary evaluation",
    ],
    key_stakeholders: ["Procurement", "Engineering", "Finance"],
    prerequisites: [
      "RFQ documentation complete",
      "Qualified supplier list",
      "Evaluation criteria defined",
    ],
    outputs: [
      "Submitted bids collection",
      "Bid analysis report",
      "Supplier responses",
    ],
    estimated_duration: "2-4 weeks",
    automation_level: "automated",
    integrations: ["rfq_system", "lifecycle_transitions"],
  },
  {
    stage: "rfq_awarded",
    name: "Supplier Award",
    description:
      "RFQ evaluation complete and contract awarded to selected supplier",
    required_actions: [
      "Bid evaluation and scoring",
      "Supplier selection decision",
      "Award notification",
      "Contract negotiation finalization",
    ],
    key_stakeholders: ["Procurement", "Legal", "Finance", "Engineering"],
    prerequisites: [
      "All bids received and evaluated",
      "Evaluation committee approval",
      "Budget confirmation",
    ],
    outputs: [
      "Supplier award notification",
      "Evaluation report",
      "Contract terms agreement",
    ],
    estimated_duration: "1-2 weeks",
    automation_level: "semi-automated",
    integrations: ["rfq_system", "purchase_orders"],
  },
  {
    stage: "purchasing",
    name: "Purchase Order Generation",
    description: "Converting awarded RFQ into formal purchase order",
    required_actions: [
      "Purchase order creation",
      "Internal approval workflow",
      "Legal review and approval",
      "Financial authorization",
    ],
    key_stakeholders: ["Procurement", "Finance", "Legal"],
    prerequisites: [
      "Signed contract or award acceptance",
      "Budget allocation",
      "Delivery terms agreement",
    ],
    outputs: [
      "Approved purchase order",
      "Payment terms schedule",
      "Delivery milestone plan",
    ],
    estimated_duration: "3-7 business days",
    automation_level: "automated",
    integrations: ["purchase_orders", "lifecycle_transitions"],
  },
  {
    stage: "ordered",
    name: "Production & Manufacturing",
    description: "Supplier acknowledged PO and component is in production",
    required_actions: [
      "Supplier acknowledgment",
      "Production schedule confirmation",
      "Quality plan activation",
      "Progress monitoring setup",
    ],
    key_stakeholders: ["Supplier", "Procurement", "Quality"],
    prerequisites: [
      "Purchase order sent to supplier",
      "Supplier acknowledgment received",
      "Production capacity confirmed",
    ],
    outputs: [
      "Production schedule",
      "Quality control plan",
      "Progress tracking system",
    ],
    estimated_duration: "4-12 weeks (varies by component)",
    automation_level: "semi-automated",
    integrations: ["purchase_orders", "inventory_tracking"],
  },
  {
    stage: "shipped",
    name: "Logistics & Transit",
    description: "Component manufactured and in transit to delivery location",
    required_actions: [
      "Shipping arrangement and tracking",
      "Transit insurance activation",
      "Delivery coordination",
      "Receiving preparation",
    ],
    key_stakeholders: ["Supplier", "Logistics", "Warehouse"],
    prerequisites: [
      "Manufacturing completion",
      "Quality inspection passed",
      "Shipping documentation",
    ],
    outputs: ["Shipping manifest", "Tracking information", "Delivery schedule"],
    estimated_duration: "1-4 weeks (varies by location)",
    automation_level: "automated",
    integrations: ["purchase_orders", "inventory_tracking"],
  },
  {
    stage: "received",
    name: "Receiving & Inspection",
    description: "Component delivered and undergoing receiving inspection",
    required_actions: [
      "Physical receipt confirmation",
      "Damage assessment",
      "Quality inspection",
      "Documentation verification",
    ],
    key_stakeholders: ["Warehouse", "Quality", "Procurement"],
    prerequisites: [
      "Delivery completion",
      "Receiving documentation",
      "Inspection procedures",
    ],
    outputs: [
      "Receiving report",
      "Quality inspection results",
      "Inventory update",
    ],
    estimated_duration: "1-3 business days",
    automation_level: "semi-automated",
    integrations: ["inventory_tracking", "media_management"],
  },
  {
    stage: "installed",
    name: "Installation",
    description: "Component installed in final system or project location",
    required_actions: [
      "Installation planning",
      "Component installation",
      "Connection and integration",
      "Initial functionality testing",
    ],
    key_stakeholders: [
      "Installation Team",
      "Engineering",
      "Project Management",
    ],
    prerequisites: [
      "Site readiness",
      "Installation procedures",
      "Required tools and equipment",
    ],
    outputs: [
      "Installation report",
      "As-built documentation",
      "Initial test results",
    ],
    estimated_duration: "1-5 days (varies by component)",
    automation_level: "manual",
    integrations: ["media_management", "lifecycle_transitions"],
  },
  {
    stage: "commissioned",
    name: "Commissioning",
    description: "Component commissioned and performance verified",
    required_actions: [
      "System commissioning tests",
      "Performance verification",
      "Safety checks completion",
      "Commissioning report generation",
    ],
    key_stakeholders: ["Commissioning Team", "Engineering", "Safety"],
    prerequisites: [
      "Installation completion",
      "System integration",
      "Safety systems verification",
    ],
    outputs: [
      "Commissioning report",
      "Performance certificates",
      "Safety compliance verification",
    ],
    estimated_duration: "1-2 weeks",
    automation_level: "semi-automated",
    integrations: ["media_management", "lifecycle_transitions"],
  },
  {
    stage: "operational",
    name: "Operations",
    description: "Component fully operational and generating value",
    required_actions: [
      "Operational monitoring activation",
      "Performance tracking setup",
      "Maintenance schedule creation",
      "Warranty registration",
    ],
    key_stakeholders: ["Operations", "Maintenance", "Engineering"],
    prerequisites: [
      "Commissioning completion",
      "Performance verification",
      "Operational procedures",
    ],
    outputs: [
      "Operational performance data",
      "Maintenance schedule",
      "Warranty documentation",
    ],
    estimated_duration: "Ongoing (component lifetime)",
    automation_level: "automated",
    integrations: ["inventory_tracking", "media_management"],
  },
  {
    stage: "warranty_active",
    name: "Warranty Management",
    description:
      "Component under active warranty coverage with performance monitoring",
    required_actions: [
      "Warranty tracking and monitoring",
      "Performance analysis",
      "Preventive maintenance execution",
      "Issue resolution and claims",
    ],
    key_stakeholders: ["Operations", "Maintenance", "Warranty Team"],
    prerequisites: [
      "Operational status",
      "Warranty registration",
      "Performance baselines",
    ],
    outputs: [
      "Warranty status reports",
      "Performance analytics",
      "Maintenance records",
    ],
    estimated_duration: "Warranty period (typically 10-25 years)",
    automation_level: "automated",
    integrations: ["inventory_tracking", "media_management"],
  },
  {
    stage: "maintenance",
    name: "Maintenance & Repair",
    description: "Component undergoing scheduled or corrective maintenance",
    required_actions: [
      "Maintenance planning and scheduling",
      "Maintenance execution",
      "Performance restoration",
      "Documentation update",
    ],
    key_stakeholders: ["Maintenance Team", "Operations", "Engineering"],
    prerequisites: [
      "Maintenance requirements identification",
      "Resource availability",
      "Maintenance procedures",
    ],
    outputs: [
      "Maintenance reports",
      "Updated performance data",
      "Component condition assessment",
    ],
    estimated_duration: "1 day - 2 weeks (varies by maintenance type)",
    automation_level: "semi-automated",
    integrations: ["inventory_tracking", "media_management"],
  },
  {
    stage: "retired",
    name: "Retirement",
    description:
      "Component end-of-life and preparation for disposal or recycling",
    required_actions: [
      "End-of-life assessment",
      "Decommissioning planning",
      "Asset recovery evaluation",
      "Disposal/recycling preparation",
    ],
    key_stakeholders: ["Operations", "Engineering", "Sustainability"],
    prerequisites: [
      "End-of-life criteria met",
      "Replacement planning",
      "Environmental compliance",
    ],
    outputs: [
      "Decommissioning plan",
      "Asset recovery report",
      "Environmental compliance documentation",
    ],
    estimated_duration: "1-4 weeks",
    automation_level: "manual",
    integrations: ["lifecycle_transitions", "media_management"],
  },
  {
    stage: "recycling",
    name: "Recycling & Disposal",
    description: "Component material recovery and environmental disposal",
    required_actions: [
      "Material separation and recovery",
      "Environmental disposal execution",
      "Recycling certification",
      "Sustainability reporting",
    ],
    key_stakeholders: ["Sustainability Team", "Environmental Compliance"],
    prerequisites: [
      "Decommissioning completion",
      "Recycling facility availability",
      "Environmental permits",
    ],
    outputs: [
      "Recycling certificates",
      "Material recovery report",
      "Environmental compliance documentation",
    ],
    estimated_duration: "2-8 weeks",
    automation_level: "semi-automated",
    integrations: ["media_management", "lifecycle_transitions"],
  },
  {
    stage: "archived",
    name: "Documentation Archive",
    description:
      "Component lifecycle documentation archived for future reference",
    required_actions: [
      "Documentation compilation",
      "Archive system storage",
      "Metadata indexing",
      "Long-term preservation",
    ],
    key_stakeholders: ["Data Management", "Compliance"],
    prerequisites: [
      "Complete lifecycle documentation",
      "Legal retention requirements",
      "Archive system access",
    ],
    outputs: [
      "Archived documentation package",
      "Searchable metadata",
      "Long-term access procedures",
    ],
    estimated_duration: "1-2 weeks",
    automation_level: "automated",
    integrations: ["media_management"],
  },
];

function findWorkflowStage(
  status: ODLComponentStatus,
): WorkflowStep | undefined {
  return WORKFLOW_STAGES.find((stage) => stage.stage === status);
}

function calculateWorkflowCompletion(
  currentStatus: ODLComponentStatus,
): number {
  const currentIndex = WORKFLOW_STAGES.findIndex(
    (stage) => stage.stage === currentStatus,
  );
  return currentIndex >= 0
    ? Math.round(((currentIndex + 1) / WORKFLOW_STAGES.length) * 100)
    : 0;
}

function getNextPossibleStages(
  currentStatus: ODLComponentStatus,
): WorkflowStep[] {
  // This would reference the same transition rules from the lifecycle API
  const transitionMap: Partial<
    Record<ODLComponentStatus, ODLComponentStatus[]>
  > = {
    draft: ["approved", "cancelled"],
    approved: ["available", "draft", "cancelled"],
    available: ["sourcing", "draft", "archived"],
    sourcing: ["rfq_open", "available", "cancelled"],
    rfq_open: ["rfq_awarded", "available", "cancelled"],
    rfq_awarded: ["purchasing", "sourcing", "cancelled"],
    purchasing: ["ordered", "rfq_awarded", "cancelled"],
    ordered: ["shipped", "purchasing", "cancelled"],
    shipped: ["received", "ordered", "returned"],
    received: ["installed", "shipped", "returned", "quarantine"],
    installed: ["commissioned", "received", "returned"],
    commissioned: ["operational", "installed", "retired"],
    operational: ["warranty_active", "maintenance", "retired"],
    warranty_active: ["operational", "maintenance", "retired", "returned"],
    maintenance: ["operational", "retired", "returned"],
    retired: ["archived", "recycling"],
    recycling: ["archived"],
  };

  const nextStatuses = transitionMap[currentStatus] || [];
  return WORKFLOW_STAGES.filter((stage) => nextStatuses.includes(stage.stage));
}

export async function POST(request: NextRequest) {
  try {
    const validationRequest: WorkflowValidationRequest = await request.json();

    const currentStage = findWorkflowStage(validationRequest.current_status);
    if (!currentStage) {
      return NextResponse.json(
        {
          error: `Invalid component status: ${validationRequest.current_status}`,
        },
        { status: 400 },
      );
    }

    const nextPossibleStages = getNextPossibleStages(
      validationRequest.current_status,
    );
    const workflowCompletion = calculateWorkflowCompletion(
      validationRequest.current_status,
    );

    // Mock integration status - in real implementation, these would be actual system checks
    const integrationStatus = {
      rfq_system: true,
      purchase_orders: true,
      lifecycle_transitions: true,
      media_management: true,
      inventory_tracking: true,
    };

    // Generate recommendations based on current stage
    const recommendations: string[] = [];
    switch (validationRequest.current_status) {
      case "draft":
        recommendations.push(
          "Ensure all technical specifications are complete before approval",
        );
        recommendations.push("Consider conducting preliminary market research");
        break;
      case "sourcing":
        recommendations.push("Prepare comprehensive RFQ documentation");
        recommendations.push(
          "Define clear evaluation criteria and scoring methodology",
        );
        break;
      case "operational":
        recommendations.push("Establish performance monitoring and alerting");
        recommendations.push("Schedule preventive maintenance activities");
        break;
      case "retired":
        recommendations.push("Plan sustainable disposal or recycling options");
        recommendations.push(
          "Archive all documentation for compliance requirements",
        );
        break;
    }

    // Check for missing prerequisites
    const missingPrerequisites: string[] = [];
    // In real implementation, validate against actual system state
    currentStage.prerequisites.forEach((prerequisite) => {
      // Mock validation - in real implementation, check system state
      if (Math.random() > 0.8) {
        // Randomly flag some prerequisites as missing for demo
        missingPrerequisites.push(prerequisite);
      }
    });

    const result: ValidationResult = {
      is_valid: missingPrerequisites.length === 0,
      current_stage: currentStage,
      next_possible_stages: nextPossibleStages,
      workflow_completion: workflowCompletion,
      missing_prerequisites: missingPrerequisites,
      recommendations,
      warnings:
        missingPrerequisites.length > 0
          ? [
              `${missingPrerequisites.length} prerequisite(s) not met for current stage`,
            ]
          : [],
      integration_status: integrationStatus,
    };

    console.log(
      `Workflow validation for component ${validationRequest.component_id} at stage ${validationRequest.current_status}`,
    );

    return NextResponse.json(result);
  } catch (error) {
    console.error("Error validating workflow:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 },
    );
  }
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const componentId = searchParams.get("component_id");
    const includeMetrics = searchParams.get("include_metrics") === "true";

    const workflowOverview = {
      total_stages: WORKFLOW_STAGES.length,
      workflow_stages: WORKFLOW_STAGES.map((stage) => ({
        stage: stage.stage,
        name: stage.name,
        description: stage.description,
        estimated_duration: stage.estimated_duration,
        automation_level: stage.automation_level,
        key_stakeholders: stage.key_stakeholders,
        integrations: stage.integrations,
      })),
      automation_summary: {
        manual: WORKFLOW_STAGES.filter((s) => s.automation_level === "manual")
          .length,
        semi_automated: WORKFLOW_STAGES.filter(
          (s) => s.automation_level === "semi-automated",
        ).length,
        automated: WORKFLOW_STAGES.filter(
          (s) => s.automation_level === "automated",
        ).length,
      },
      stakeholder_involvement: WORKFLOW_STAGES.reduce(
        (acc, stage) => {
          stage.key_stakeholders.forEach((stakeholder) => {
            acc[stakeholder] = (acc[stakeholder] || 0) + 1;
          });
          return acc;
        },
        {} as Record<string, number>,
      ),
    };

    if (includeMetrics && componentId) {
      // In real implementation, fetch actual metrics from database
      const mockMetrics = {
        average_stage_duration: {
          draft: "10 days",
          approved: "3 days",
          sourcing: "18 days",
          rfq_open: "21 days",
          purchasing: "5 days",
          ordered: "45 days",
        },
        bottleneck_stages: ["sourcing", "ordered", "commissioned"],
        success_rate: 94.5,
        average_total_duration: "180 days",
      };

      return NextResponse.json({
        ...workflowOverview,
        metrics: mockMetrics,
      });
    }

    return NextResponse.json(workflowOverview);
  } catch (error) {
    console.error("Error fetching workflow information:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 },
    );
  }
}
