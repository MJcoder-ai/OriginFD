import type {
  LifecycleGateResponse,
  LifecyclePhaseResponse,
} from "@/lib/api-client";

export type LifecycleGate = LifecycleGateResponse;
export type LifecyclePhase = LifecyclePhaseResponse;

export const LIFECYCLE_APPROVER_ROLES = [
  "admin",
  "engineer",
  "project_manager",
  "approver",
] as const;

export function canUserApproveGate(
  userRoles?: string[] | null,
): boolean {
  if (!userRoles?.length) return false;
  return userRoles.some((role) =>
    LIFECYCLE_APPROVER_ROLES.includes(role.toLowerCase() as any),
  );
}

export function shouldShowGateApproveAction(
  gate: LifecycleGate,
  userRoles?: string[] | null,
): boolean {
  if (!gate) return false;
  if (gate.status === "approved" || gate.status === "completed") {
    return false;
  }
  return canUserApproveGate(userRoles);
}

export function calculatePhaseProgress(phase: LifecyclePhase) {
  const totalGates = phase.gates?.length ?? 0;
  const approvedGates = (phase.gates ?? []).filter((gate) =>
    ["approved", "completed"].includes(gate.status),
  ).length;
  const percentComplete = totalGates
    ? Math.round((approvedGates / totalGates) * 100)
    : 0;

  return { totalGates, approvedGates, percentComplete };
}
