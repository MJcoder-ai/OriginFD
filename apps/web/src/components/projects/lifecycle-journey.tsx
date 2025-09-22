"use client";

import * as React from "react";
import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutateAsyncFunction,
} from "@tanstack/react-query";
import { Loader2, Check, AlertTriangle, Shield } from "lucide-react";

import {
  Badge,
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Progress,
} from "@originfd/ui";
import {
  apiClient,
  ApiError,
  type LifecycleGateStatus,
} from "@/lib/api-client";
import { useAuth } from "@/lib/auth/auth-provider";
import {
  calculatePhaseProgress,
  canUserApproveGate,
  shouldShowGateApproveAction,
  type LifecycleGate,
} from "./lifecycle-journey-helpers";

import { ProjectOrchestratorTasks } from "./project-orchestrator-tasks";

interface LifecycleJourneyProps {
  projectId: string;
}

const phaseStatusMap: Record<
  string,
  { label: string; variant: "outline" | "secondary" | "default" }
> = {
  completed: { label: "Completed", variant: "default" },
  current: { label: "In Progress", variant: "secondary" },
  upcoming: { label: "Upcoming", variant: "outline" },
  not_started: { label: "Not Started", variant: "outline" },
};

const gateStatusMap: Record<
  LifecycleGateStatus,
  { label: string; variant: "outline" | "default" | "destructive" }
> = {
  approved: { label: "Approved", variant: "default" },
  completed: { label: "Approved", variant: "default" },
  in_review: { label: "In Review", variant: "outline" },
  pending: { label: "Pending", variant: "outline" },
  rejected: { label: "Changes Requested", variant: "destructive" },
  blocked: { label: "Blocked", variant: "destructive" },
} as const;

type ApproveGateFn = UseMutateAsyncFunction<
  any,
  Error,
  { gateId: string; status: LifecycleGateStatus; notes?: string }
>;

function GateApprovalButton({
  gate,
  onApprove,
  isPending,
  hasPermission,
  showApproveAction,
}: {
  gate: LifecycleGate;
  onApprove: ApproveGateFn;
  isPending: boolean;
  hasPermission: boolean;
  showApproveAction: boolean;
}) {
  const [errorMessage, setErrorMessage] = React.useState<string | null>(null);

  const handleApprove = async () => {
    setErrorMessage(null);
    try {
      await onApprove({ gateId: gate.id, status: "approved" });
    } catch (error) {
      if (error instanceof ApiError) {
        setErrorMessage(error.message);
      } else if (error instanceof Error) {
        setErrorMessage(error.message);
      } else {
        setErrorMessage("Failed to approve gate");
      }
    }
  };

  if (gate.status === "approved" || gate.status === "completed") {
    return (
      <Badge variant="default" className="gap-1">
        <Check className="h-3.5 w-3.5" /> Approved
      </Badge>
    );
  }

  if (!hasPermission) {
    return (
      <div className="text-xs text-muted-foreground">
        <div className="flex items-center gap-2">
          <Shield className="h-3.5 w-3.5" />
          Approvals limited to project managers, engineers, approvers, and
          admins.
        </div>
      </div>
    );
  }

  if (!showApproveAction) {
    return null;
  }

  return (
    <div className="flex flex-col gap-2">
      <Button
        size="sm"
        disabled={isPending}
        onClick={() => {
          void handleApprove();
        }}
      >
        {isPending ? (
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
        ) : (
          <Check className="mr-2 h-4 w-4" />
        )}
        Approve Gate
      </Button>
      {errorMessage && (
        <div className="text-xs text-red-600">{errorMessage}</div>
      )}
    </div>
  );
}

export function LifecycleJourney({ projectId }: LifecycleJourneyProps) {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [activeGateId, setActiveGateId] = React.useState<string | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ["project-lifecycle", projectId],
    queryFn: () => apiClient.getProjectLifecycle(projectId),
  });

  const mutation = useMutation({
    mutationFn: ({ gateId, status, notes }: { gateId: string; status: LifecycleGateStatus; notes?: string }) =>
      apiClient.updateProjectLifecycleGateStatus(
        projectId,
        gateId,
        status,
        notes,
      ),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["project-lifecycle", projectId],
      });
    },
    onSettled: () => {
      setActiveGateId(null);
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" />
        Loading lifecycle...
      </div>
    );
  }

  if (error) {
    return <div className="text-sm text-red-500">Failed to load lifecycle</div>;
  }

  const phases = data?.phases ?? [];
  const userRoles = user?.roles ?? [];
  const canApprove = canUserApproveGate(userRoles);

  if (!phases.length) {
    return (
      <div className="rounded-md border border-dashed p-6 text-center text-sm text-muted-foreground">
        No lifecycle phases available for this project yet.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h3 className="text-lg font-semibold">Lifecycle Phases</h3>
        <p className="text-sm text-muted-foreground">
          Track progress through each phase and approve gates as milestones are
          completed.
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {phases.map((phase) => {
          const progress = calculatePhaseProgress(phase);
          const phaseStatus = phaseStatusMap[phase.status] ?? {
            label: phase.status,
            variant: "outline" as const,
          };

          return (
            <Card key={phase.id} className="flex flex-col gap-3">
              <CardHeader className="space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <CardTitle className="text-base font-semibold">
                      {phase.name}
                    </CardTitle>
                    <p className="text-xs text-muted-foreground">
                      {progress.approvedGates} of {progress.totalGates} gates approved
                    </p>
                  </div>
                  <Badge variant={phaseStatus.variant}>{phaseStatus.label}</Badge>
                </div>
                <div className="space-y-1">
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span>Phase progress</span>
                    <span>{progress.percentComplete}%</span>
                  </div>
                  <Progress value={progress.percentComplete} className="h-1.5" />
                </div>
              </CardHeader>
              <CardContent className="flex flex-col gap-3">
                {(phase.gates ?? []).map((gate) => {
                  const statusMeta = gateStatusMap[gate.status] ?? {
                    label: gate.status,
                    variant: "outline" as const,
                  };
                  const isGatePending = mutation.isPending && activeGateId === gate.id;
                  const showApproveButton = shouldShowGateApproveAction(
                    gate,
                    userRoles,
                  );

                  return (
                    <div
                      key={gate.id}
                      className="rounded-lg border p-3 shadow-sm transition hover:border-primary/50"
                    >
                      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            {gate.status === "approved" || gate.status === "completed" ? (
                              <Check className="h-4 w-4 text-green-600" />
                            ) : gate.bottleneck ? (
                              <AlertTriangle className="h-4 w-4 text-red-600" />
                            ) : (
                              <Loader2 className="h-4 w-4 text-muted-foreground" />
                            )}
                            <span className="text-sm font-medium">{gate.name}</span>
                          </div>
                          <p className="text-xs text-muted-foreground">
                            Status updated by {gate.updated_by ?? "system"}
                            {gate.updated_at ? ` on ${new Date(gate.updated_at).toLocaleDateString()}` : ""}
                          </p>
                          {gate.notes && (
                            <p className="text-xs text-muted-foreground">Notes: {gate.notes}</p>
                          )}
                        </div>
                        <Badge variant={statusMeta.variant}>{statusMeta.label}</Badge>
                      </div>

                      {gate.bottleneck && (
                        <div className="mt-2 flex items-center gap-2 text-xs text-red-600">
                          <AlertTriangle className="h-3.5 w-3.5" />
                          {gate.bottleneck}
                        </div>
                      )}

                      <div className="mt-3">
                        <GateApprovalButton
                          gate={gate}
                          hasPermission={canApprove}
                          showApproveAction={showApproveButton}
                          isPending={isGatePending}
                          onApprove={async ({ gateId, status, notes }) => {
                            setActiveGateId(gateId);
                            await mutation.mutateAsync({ gateId, status, notes });
                          }}
                        />
                      </div>
                    </div>
                  );
                })}
              </CardContent>
            </Card>
          );
        })}
      </div>
      <ProjectOrchestratorTasks projectId={projectId} />
    </div>
  );
}

export default LifecycleJourney;
