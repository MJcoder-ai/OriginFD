import { NextRequest, NextResponse } from "next/server";

import {
  addComponentsToProjectDocument,
} from "../../../../shared-data";

const UNSPSC_CATEGORY_MAP: Record<string, string> = {
  "26111704": "pv_module",
  "26111705": "inverter",
  "26111706": "battery",
};

interface IncomingComponent {
  component_id?: string;
  quantity?: number;
  placement?: {
    location?: string;
    coordinates?: { x?: number; y?: number; z?: number };
    orientation?: string;
  };
  configuration?: Record<string, any>;
  notes?: string;
  component?: any;
}

function deriveCategory(component: IncomingComponent) {
  const unspsc =
    component.component?.component_management?.component_identity?.classification
      ?.unspsc ??
    component.component?.classification?.unspsc ??
    component.component?.category ??
    component.component?.metadata?.category ??
    component.component?.component_identity?.classification?.unspsc ??
    component.component_id;

  if (unspsc && UNSPSC_CATEGORY_MAP[unspsc]) {
    return UNSPSC_CATEGORY_MAP[unspsc];
  }

  if (typeof component.component?.category === "string") {
    return component.component.category;
  }

  return "component";
}

function normalizeComponentPayload(component: IncomingComponent) {
  const identity =
    component.component?.component_management?.component_identity ||
    component.component?.component_identity ||
    {};

  const referenceId =
    identity.component_id || component.component_id || component.component?.id;

  const quantity = Math.max(1, Number(component.quantity ?? 1) || 1);

  return {
    id:
      component.component?.id ||
      identity.component_id ||
      component.component_id ||
      `component-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    reference_id: referenceId,
    brand: identity.brand || component.component?.brand || "Unknown",
    part_number:
      identity.part_number || component.component?.part_number || referenceId,
    rating_w: identity.rating_w || component.component?.rating_w || null,
    status:
      component.component?.component_management?.status || "selected",
    category: deriveCategory(component),
    quantity,
    placement: component.placement || null,
    configuration: component.configuration || null,
    notes: component.notes || null,
    added_at: new Date().toISOString(),
  };
}

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } },
) {
  try {
    const { id: projectId } = params;
    const body = await request.json();
    const incomingComponents: IncomingComponent[] = Array.isArray(
      body?.components,
    )
      ? body.components
      : [];

    if (!projectId) {
      return NextResponse.json(
        { error: "Project ID is required" },
        { status: 400 },
      );
    }

    if (incomingComponents.length === 0) {
      return NextResponse.json(
        { error: "At least one component must be provided" },
        { status: 400 },
      );
    }

    const normalizedComponents = incomingComponents.map((component) =>
      normalizeComponentPayload(component),
    );

    const result = addComponentsToProjectDocument(
      projectId,
      normalizedComponents,
    );

    if (!result) {
      return NextResponse.json(
        { error: "Project document not found" },
        { status: 404 },
      );
    }

    return NextResponse.json({
      ok: true,
      added: normalizedComponents.length,
      components: result.components,
    });
  } catch (error) {
    console.error("Failed to add components to project:", error);
    return NextResponse.json(
      { error: "Failed to add components to project" },
      { status: 500 },
    );
  }
}
