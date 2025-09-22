import { strict as assert } from "node:assert";
import test from "node:test";

import {
  calculatePhaseProgress,
  canUserApproveGate,
  shouldShowGateApproveAction,
  type LifecycleGate,
  type LifecyclePhase,
} from "../../src/components/projects/lifecycle-journey-helpers";

const mockGate = (status: LifecycleGate["status"]): LifecycleGate => ({
  id: `${status}-gate`,
  name: `${status} gate`,
  status,
  approved_at: null,
  approved_by: null,
  updated_at: null,
  updated_by: null,
  notes: null,
});

const mockPhase = (gates: LifecycleGate[]): LifecyclePhase => ({
  id: "phase-1",
  name: "Design",
  status: "current",
  gates,
});

test("canUserApproveGate allows configured roles regardless of case", () => {
  assert.equal(canUserApproveGate(["admin"]), true);
  assert.equal(canUserApproveGate(["Engineer"]), true);
  assert.equal(canUserApproveGate(["PROJECT_MANAGER"]), true);
  assert.equal(canUserApproveGate(["viewer", "approver"]), true);
  assert.equal(canUserApproveGate(["viewer", "guest"]), false);
  assert.equal(canUserApproveGate(undefined), false);
});

test("shouldShowGateApproveAction hides actions for approved gates", () => {
  const approvedGate = mockGate("approved");
  const pendingGate = mockGate("pending");

  assert.equal(shouldShowGateApproveAction(approvedGate, ["admin"]), false);
  assert.equal(shouldShowGateApproveAction(pendingGate, ["admin"]), true);
  assert.equal(shouldShowGateApproveAction(pendingGate, ["viewer"]), false);
});

test("calculatePhaseProgress derives completion metrics", () => {
  const phase = mockPhase([
    mockGate("approved"),
    mockGate("pending"),
    mockGate("completed"),
  ]);

  const progress = calculatePhaseProgress(phase);

  assert.equal(progress.totalGates, 3);
  assert.equal(progress.approvedGates, 2);
  assert.equal(progress.percentComplete, 67);
});
