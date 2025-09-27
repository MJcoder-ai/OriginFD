"use client";

import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import {
  AlertTriangle,
  CheckCircle2,
  X,
  Clock,
  Loader2,
  type LucideIcon,
} from "lucide-react";

import {
  Badge,
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Input,
  Label,
  Textarea,
} from "@originfd/ui";
import {
  apiClient,
  ApiError,
  type ApprovalDecision,
  type GateStatus,
  type LifecyclePhaseView,
} from "@/lib/api-client";
import { useAuth } from "@/lib/auth/auth-provider";
import { cn } from "@/lib/utils";
import { canUserApproveGate } from "./lifecycle-journey-helpers";

import { ProjectOrchestratorTasks } from "./project-orchestrator-tasks";

interface LifecycleJourneyProps {
  projectId: string;
}

type GateStatusMeta = {
  label: string;
  variant: "default" | "secondary" | "outline" | "destructive";
  icon: LucideIcon;
  iconClassName?: string;
  description: string;
};

const gateStatusMeta: Record<GateStatus, GateStatusMeta> = {
  APPROVED: {
    label: "Approved",
    variant: "default",
    icon: CheckCircle2,
    description: "Gate approved and complete.",
  },
  REJECTED: {
    label: "Rejected",
    variant: "destructive",
    icon: X,
    description: "Changes requested before progression.",
  },
  IN_PROGRESS: {
    label: "In Progress",
    variant: "secondary",
    icon: Loader2,
    iconClassName: "animate-spin",
    description: "Gate currently under review.",
  },
  BLOCKED: {
    label: "Blocked",
    variant: "destructive",
    icon: AlertTriangle,
    description: "Gate blocked pending resolution.",
  },
  NOT_STARTED: {
    label: "Not Started",
    variant: "outline",
    icon: Clock,
    description: "Gate awaiting kickoff.",
  },
};

const gateStatusLegendEntries = Object.entries(gateStatusMeta) as Array<
  [GateStatus, GateStatusMeta]
>;

const lifecycleV2Env = process.env.NEXT_PUBLIC_LIFECYCLE_V2;
const LIFECYCLE_V2_ENABLED =
  !lifecycleV2Env ||
  lifecycleV2Env === "1" ||
  lifecycleV2Env.toLowerCase() === "true";

function LifecycleJourney({ projectId }: LifecycleJourneyProps) {
  const queryClient = useQueryClient();
  const { user } = useAuth();

  const lifecycleQuery = useQuery({
    queryKey: ["project-lifecycle", projectId],
    queryFn: () => apiClient.getProjectLifecycle(projectId),
  });

  const phases = React.useMemo<LifecyclePhaseView[]>(() => {
    const list = lifecycleQuery.data ?? [];
    return [...list].sort((a, b) => a.order - b.order);
  }, [lifecycleQuery.data]);

  const userRoles = user?.roles ?? [];
  const canApprove = canUserApproveGate(userRoles);

  const [selectedPhaseCode, setSelectedPhaseCode] = React.useState<
    number | null
  >(null);
  const [selectedGateCode, setSelectedGateCode] = React.useState<string | null>(
    null,
  );
  const [decision, setDecision] = React.useState<ApprovalDecision>("APPROVE");
  const [roleKey, setRoleKey] = React.useState("");
  const [comment, setComment] = React.useState("");
  const [formError, setFormError] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (!phases.length) {
      setSelectedPhaseCode(null);
      setSelectedGateCode(null);
      return;
    }

    setSelectedPhaseCode((current) => {
      if (
        current !== null &&
        phases.some((phase) => phase.phase_code === current)
      ) {
        return current;
      }
      return phases[0].phase_code;
    });
  }, [phases]);

  React.useEffect(() => {
    if (!phases.length) {
      setSelectedGateCode(null);
      return;
    }

    const phase =
      phases.find((candidate) => candidate.phase_code === selectedPhaseCode) ??
      phases[0];

    if (!phase) {
      setSelectedGateCode(null);
      return;
    }

    setSelectedGateCode((current) => {
      if (current && phase.gates.some((gate) => gate.gate_code === current)) {
        return current;
      }
      return phase.gates[0]?.gate_code ?? null;
    });
  }, [phases, selectedPhaseCode]);

  React.useEffect(() => {
    setDecision("APPROVE");
    setComment("");
    setFormError(null);
  }, [selectedPhaseCode, selectedGateCode]);

  const selectedPhase = React.useMemo(() => {
    if (selectedPhaseCode === null) {
      return null;
    }
    return (
      phases.find((phase) => phase.phase_code === selectedPhaseCode) ?? null
    );
  }, [phases, selectedPhaseCode]);

  const selectedGate = React.useMemo(() => {
    if (!selectedPhase) {
      return null;
    }
    if (!selectedGateCode) {
      return selectedPhase.gates[0] ?? null;
    }
    return (
      selectedPhase.gates.find((gate) => gate.gate_code === selectedGateCode) ??
      selectedPhase.gates[0] ??
      null
    );
  }, [selectedPhase, selectedGateCode]);

  const selectedGateMeta = selectedGate
    ? (gateStatusMeta[selectedGate.status] ?? gateStatusMeta.NOT_STARTED)
    : null;

  const SelectedGateIcon = selectedGateMeta?.icon;

  const selectedGateType = React.useMemo(() => {
    if (!selectedPhase || !selectedGate) {
      return null;
    }
    return selectedPhase.entry_gate_code === selectedGate.gate_code
      ? "entry"
      : "exit";
  }, [selectedPhase, selectedGate]);

  const approvalMutation = useMutation({
    mutationFn: (payload: {
      phase_code: number;
      gate_code: string;
      decision: ApprovalDecision;
      role_key: string;
      comment?: string;
    }) => apiClient.postGateApproval(projectId, payload),
    onSuccess: (updatedPhases) => {
      queryClient.setQueryData(["project-lifecycle", projectId], updatedPhases);
      setComment("");
      setDecision("APPROVE");
      setFormError(null);
    },
  });

  const handleGateSelect = React.useCallback(
    (phaseCode: number, gateCode: string) => {
      setSelectedPhaseCode(phaseCode);
      setSelectedGateCode(gateCode);
    },
    [],
  );

  const handleApprovalSubmit = async (
    event: React.FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();

    if (!selectedPhase || !selectedGate) {
      setFormError("Select a phase and gate before recording a decision.");
      return;
    }

    if (!roleKey.trim()) {
      setFormError("Role is required to record an approval decision.");
      return;
    }

    setFormError(null);
    try {
      await approvalMutation.mutateAsync({
        phase_code: selectedPhase.phase_code,
        gate_code: selectedGate.gate_code,
        decision,
        role_key: roleKey.trim(),
        comment: comment.trim() ? comment.trim() : undefined,
      });
    } catch (error) {
      if (error instanceof ApiError) {
        setFormError(error.message);
      } else if (error instanceof Error) {
        setFormError(error.message);
      } else {
        setFormError("Failed to submit approval. Please try again.");
      }
    }
  };

  if (lifecycleQuery.isLoading) {
    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" />
        Loading lifecycle...
      </div>
    );
  }

  if (lifecycleQuery.isError) {
    const message =
      lifecycleQuery.error instanceof Error
        ? lifecycleQuery.error.message
        : null;

    return (
      <div className="text-sm text-red-500">
        Failed to load lifecycle{message ? `: ${message}` : ""}.
      </div>
    );
  }

  if (!phases.length) {
    return (
      <div className="rounded-md border border-dashed p-6 text-center text-sm text-muted-foreground">
        No lifecycle phases available for this project yet.
      </div>
    );
  }

  if (!LIFECYCLE_V2_ENABLED) {
    return <LegacyLifecycleSummary phases={phases} projectId={projectId} />;
  }

  const currentRoles =
    selectedPhase && selectedGateType
      ? selectedGateType === "entry"
        ? selectedPhase.required_entry_roles
        : selectedPhase.required_exit_roles
      : [];

  const odlSections = selectedPhase?.odl_sd_sections ?? [];

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h3 className="text-lg font-semibold">Lifecycle Phases</h3>
        <p className="text-sm text-muted-foreground">
          Track phase gates, required roles, and ODL-SD references as the
          project advances through the lifecycle.
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
        <span className="font-medium text-foreground">Gate status legend</span>
        {gateStatusLegendEntries.map(([status, meta]) => {
          const Icon = meta.icon;
          return (
            <Badge
              key={status}
              variant={meta.variant}
              className="flex items-center gap-1"
              title={meta.description}
            >
              <Icon className={cn("h-3 w-3", meta.iconClassName)} />
              {meta.label}
            </Badge>
          );
        })}
      </div>

      <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
        <div className="grid gap-4">
          {phases.map((phase) => {
            const hasStructuredGates =
              Array.isArray(phase.gates) && phase.gates.length === 2;

            return (
              <Card
                key={`${phase.phase_code}-${phase.phase_key}`}
                className="flex flex-col gap-3"
              >
                <CardHeader className="space-y-2">
                  <div className="flex items-start justify-between gap-2">
                    <div className="space-y-1">
                      <CardTitle className="text-base font-semibold">
                        {`P${phase.phase_code + 1}: ${phase.title}`}
                      </CardTitle>
                      <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                        <Badge variant="outline">{phase.phase_key}</Badge>
                        {phase.name && phase.name !== phase.title ? (
                          <span>Legacy: {phase.name}</span>
                        ) : null}
                        {phase.status ? (
                          <Badge variant="outline">{phase.status}</Badge>
                        ) : null}
                      </div>
                    </div>
                    <div className="text-right text-xs text-muted-foreground">
                      <div>Entry {phase.entry_gate_code}</div>
                      <div>Exit {phase.exit_gate_code}</div>
                    </div>
                  </div>
                </CardHeader>

                <CardContent className="space-y-4">
                  {hasStructuredGates ? (
                    <>
                      <div className="space-y-2">
                        {phase.gates.map((gate, gateIndex) => {
                          const gateCode =
                            gate.gate_code ||
                            gate.key ||
                            `${phase.phase_code}-${gateIndex}`;
                          const meta =
                            gateStatusMeta[gate.status] ??
                            gateStatusMeta.NOT_STARTED;
                          const Icon = meta.icon;
                          const isSelected =
                            selectedPhase?.phase_code === phase.phase_code &&
                            selectedGate?.gate_code === gate.gate_code;

                          return (
                            <button
                              key={gateCode}
                              type="button"
                              title={meta.description}
                              onClick={() =>
                                handleGateSelect(
                                  phase.phase_code,
                                  gate.gate_code,
                                )
                              }
                              className={cn(
                                "w-full rounded-lg border p-3 text-left transition",
                                isSelected
                                  ? "border-primary bg-primary/5 shadow-sm"
                                  : "hover:border-primary/50",
                              )}
                            >
                              <div className="flex items-start justify-between gap-3">
                                <div className="flex items-center gap-3">
                                  <Badge
                                    variant="secondary"
                                    className="shrink-0"
                                  >
                                    {gateIndex === 0 ? "Entry" : "Exit"}
                                  </Badge>
                                  <div className="space-y-1">
                                    <div className="text-sm font-medium leading-none">
                                      {gate.name}
                                    </div>
                                    <div className="text-xs text-muted-foreground">
                                      {gate.gate_code}
                                    </div>
                                  </div>
                                </div>
                                <Badge
                                  variant={meta.variant}
                                  className="flex items-center gap-1"
                                >
                                  <Icon
                                    className={cn(
                                      "h-3.5 w-3.5",
                                      meta.iconClassName,
                                    )}
                                  />
                                  {meta.label}
                                </Badge>
                              </div>
                            </button>
                          );
                        })}
                      </div>

                      <div className="space-y-3">
                        <div>
                          <p className="text-xs font-semibold uppercase text-muted-foreground">
                            Entry roles
                          </p>
                          <RoleList roles={phase.required_entry_roles} />
                        </div>
                        <div>
                          <p className="text-xs font-semibold uppercase text-muted-foreground">
                            Exit roles
                          </p>
                          <RoleList roles={phase.required_exit_roles} />
                        </div>
                      </div>

                      <div>
                        <p className="text-xs font-semibold uppercase text-muted-foreground">
                          ODL-SD references
                        </p>
                        <OdlSectionList sections={phase.odl_sd_sections} />
                      </div>
                    </>
                  ) : (
                    <div className="text-sm text-muted-foreground">
                      Legacy lifecycle payload detected. Latest status:{" "}
                      <span className="font-medium">
                        {phase.status || "unknown"}
                      </span>
                      .
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>

        <Card className="h-full">
          <CardHeader className="space-y-2">
            <CardTitle className="text-base font-semibold">
              Gate approval
            </CardTitle>
            <p className="text-xs text-muted-foreground">
              Select a phase gate to record approval or rejection decisions with
              the required context.
            </p>
          </CardHeader>
          <CardContent className="space-y-4">
            {selectedPhase && selectedGate && selectedGateMeta ? (
              <>
                <div className="space-y-2 rounded-md border bg-muted/30 p-3">
                  <div className="text-sm font-medium">
                    {selectedPhase.title}
                  </div>
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span>
                      {selectedGateType === "entry"
                        ? "Entry gate"
                        : "Exit gate"}
                    </span>
                    <span>{selectedGate.gate_code}</span>
                  </div>
                  <Badge
                    variant={selectedGateMeta.variant}
                    className="mt-2 flex w-max items-center gap-1 text-xs"
                  >
                    {SelectedGateIcon ? (
                      <SelectedGateIcon
                        className={cn(
                          "h-3 w-3",
                          selectedGateMeta.iconClassName,
                        )}
                      />
                    ) : null}
                    {selectedGateMeta.label}
                  </Badge>
                </div>

                <div>
                  <p className="text-xs font-semibold uppercase text-muted-foreground">
                    Required {selectedGateType === "entry" ? "entry" : "exit"}{" "}
                    roles
                  </p>
                  <RoleList roles={currentRoles} />
                </div>

                <div>
                  <p className="text-xs font-semibold uppercase text-muted-foreground">
                    ODL-SD references
                  </p>
                  <OdlSectionList sections={odlSections} />
                </div>

                <form onSubmit={handleApprovalSubmit} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="gate-role">Role key</Label>
                    <Input
                      id="gate-role"
                      value={roleKey}
                      onChange={(event) => setRoleKey(event.target.value)}
                      placeholder="role.project_manager"
                      disabled={!canApprove || approvalMutation.isPending}
                    />
                    <p className="text-xs text-muted-foreground">
                      Use the approval role key recorded in the lifecycle
                      configuration.
                    </p>
                  </div>

                  <fieldset className="space-y-2">
                    <legend className="text-xs font-semibold uppercase text-muted-foreground">
                      Decision
                    </legend>
                    <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-4">
                      <div className="flex items-center gap-2">
                        <input
                          type="radio"
                          id="decision-approve"
                          name="decision"
                          value="APPROVE"
                          checked={decision === "APPROVE"}
                          onChange={() => setDecision("APPROVE")}
                          disabled={!canApprove || approvalMutation.isPending}
                          className="h-3.5 w-3.5"
                        />
                        <Label
                          htmlFor="decision-approve"
                          className="text-sm font-normal"
                        >
                          Approve
                        </Label>
                      </div>
                      <div className="flex items-center gap-2">
                        <input
                          type="radio"
                          id="decision-reject"
                          name="decision"
                          value="REJECT"
                          checked={decision === "REJECT"}
                          onChange={() => setDecision("REJECT")}
                          disabled={!canApprove || approvalMutation.isPending}
                          className="h-3.5 w-3.5"
                        />
                        <Label
                          htmlFor="decision-reject"
                          className="text-sm font-normal"
                        >
                          Reject
                        </Label>
                      </div>
                    </div>
                  </fieldset>

                  <div className="space-y-2">
                    <Label htmlFor="gate-comment">Comment</Label>
                    <Textarea
                      id="gate-comment"
                      value={comment}
                      onChange={(event) => setComment(event.target.value)}
                      placeholder="Add optional context for this decision"
                      rows={3}
                      disabled={!canApprove || approvalMutation.isPending}
                    />
                  </div>

                  {formError ? (
                    <p className="text-sm text-red-500">{formError}</p>
                  ) : null}

                  {!canApprove ? (
                    <p className="text-xs text-muted-foreground">
                      You do not have permission to submit lifecycle approvals
                      with the current role set.
                    </p>
                  ) : null}

                  <Button
                    type="submit"
                    className="w-full"
                    disabled={!canApprove || approvalMutation.isPending}
                  >
                    {approvalMutation.isPending ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Submitting...
                      </>
                    ) : (
                      "Submit decision"
                    )}
                  </Button>
                </form>
              </>
            ) : (
              <p className="text-sm text-muted-foreground">
                Select a phase gate to review its requirements and submit an
                approval decision.
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      <ProjectOrchestratorTasks projectId={projectId} />
    </div>
  );
}

function LegacyLifecycleSummary({
  phases,
  projectId,
}: {
  phases: LifecyclePhaseView[];
  projectId: string;
}) {
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h3 className="text-lg font-semibold">Lifecycle Phases</h3>
        <p className="text-sm text-muted-foreground">
          Lifecycle v2 flag is disabled; displaying the legacy summary view.
        </p>
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        {phases.map((phase) => {
          return (
            <Card
              key={`${phase.phase_code}-${phase.phase_key}`}
              className="flex flex-col gap-3"
            >
              <CardHeader className="space-y-1">
                <CardTitle className="text-base font-semibold">
                  {`P${phase.phase_code + 1}: ${phase.title}`}
                </CardTitle>
                <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                  <Badge variant="outline">{phase.phase_key}</Badge>
                  {phase.name && phase.name !== phase.title ? (
                    <span>Legacy: {phase.name}</span>
                  ) : null}
                  {phase.status ? (
                    <Badge variant="outline">{phase.status}</Badge>
                  ) : null}
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="text-xs text-muted-foreground">
                  Legacy status:{" "}
                  <span className="font-medium">
                    {phase.status || "unknown"}
                  </span>
                </div>
                <div className="space-y-1">
                  {phase.gates.map((gate) => {
                    const meta =
                      gateStatusMeta[gate.status] ?? gateStatusMeta.NOT_STARTED;
                    return (
                      <div
                        key={gate.gate_code}
                        className="flex items-center justify-between text-xs"
                      >
                        <span>{gate.name}</span>
                        <Badge variant={meta.variant}>{meta.label}</Badge>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
      <ProjectOrchestratorTasks projectId={projectId} />
    </div>
  );
}

function RoleList({ roles }: { roles: string[] }) {
  if (!roles?.length) {
    return (
      <p className="text-xs text-muted-foreground italic">
        No roles specified.
      </p>
    );
  }

  return (
    <div className="flex flex-wrap gap-2">
      {roles.map((role) => (
        <Badge key={role} variant="outline">
          {role}
        </Badge>
      ))}
    </div>
  );
}

function OdlSectionList({ sections }: { sections: string[] }) {
  if (!sections?.length) {
    return (
      <p className="text-xs text-muted-foreground italic">
        No references provided.
      </p>
    );
  }

  return (
    <div className="flex flex-wrap gap-2">
      {sections.map((section) => (
        <Link
          key={section}
          href={`/docs/odl/${section}`}
          className="text-xs text-primary underline-offset-2 hover:underline"
        >
          {section}
        </Link>
      ))}
    </div>
  );
}

export default LifecycleJourney;
