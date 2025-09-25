import type { GateView, LifecyclePhaseView } from "@/lib/api-client";

export type LifecycleGate = GateView;
export type LifecyclePhase = LifecyclePhaseView;

const APPROVER_ROLE_VALUES = [
  "admin",
  "engineer",
  "project_manager",
  "approver",
  "role.admin",
  "role.engineer",
  "role.project_manager",
  "role.approver",
] as const;

const APPROVER_ROLE_SET = new Set(
  APPROVER_ROLE_VALUES.map((role) => role.toLowerCase()),
);

export const LIFECYCLE_APPROVER_ROLES = [...APPROVER_ROLE_SET];

export function canUserApproveGate(userRoles?: string[] | null): boolean {
  if (!userRoles?.length) {
    return false;
  }

  return userRoles.some((role) => {
    if (typeof role !== "string") {
      return false;
    }
    const normalized = role.toLowerCase().trim();
    if (!normalized) {
      return false;
    }

    if (APPROVER_ROLE_SET.has(normalized)) {
      return true;
    }

    const tokens = normalized.split(/[:._-]/).filter(Boolean);
    if (!tokens.length) {
      return false;
    }

    if (tokens.some((token) => APPROVER_ROLE_SET.has(token))) {
      return true;
    }

    if (tokens.length >= 2) {
      const lastTwo = tokens.slice(-2).join("_");
      if (APPROVER_ROLE_SET.has(lastTwo)) {
        return true;
      }
    }

    return false;
  });
}
