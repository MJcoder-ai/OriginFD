"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { Loader2, Check, AlertTriangle } from "lucide-react";

import { Card, CardHeader, CardTitle, CardContent, Badge } from "@originfd/ui";
import { apiClient } from "@/lib/api-client";

import { ProjectOrchestratorTasks } from "./project-orchestrator-tasks";

interface LifecycleJourneyProps {
  projectId: string;
}

export function LifecycleJourney({ projectId }: LifecycleJourneyProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["project-lifecycle", projectId],
    queryFn: () => apiClient.getProject(projectId),
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

  const phases = data?.phases || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        {phases.map((phase: any, idx: number) => (
          <React.Fragment key={phase.id}>
            <div className="flex flex-col items-center flex-1">
              <div
                className={`flex h-8 w-8 items-center justify-center rounded-full border ${
                  phase.status === "completed"
                    ? "bg-green-600 text-white"
                    : phase.status === "current"
                      ? "bg-blue-600 text-white"
                      : "bg-muted text-muted-foreground"
                }`}
              >
                {phase.status === "completed" ? (
                  <Check className="h-4 w-4" />
                ) : (
                  idx + 1
                )}
              </div>
              <span className="mt-2 text-xs font-medium text-center">
                {phase.name}
              </span>
            </div>
            {idx < phases.length - 1 && (
              <div className="h-0.5 flex-1 bg-border" />
            )}
          </React.Fragment>
        ))}
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        {phases.map((phase: any) => (
          <Card key={phase.id}>
            <CardHeader>
              <CardTitle>{phase.name}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col gap-2">
                {phase.gates?.map((gate: any) => (
                  <div key={gate.id} className="flex items-center gap-2">
                    {gate.status === "completed" ? (
                      <Check className="h-4 w-4 text-green-600" />
                    ) : gate.bottleneck ? (
                      <AlertTriangle className="h-4 w-4 text-red-600" />
                    ) : (
                      <Loader2 className="h-4 w-4 text-muted-foreground" />
                    )}
                    <span className="text-sm">{gate.name}</span>
                    {gate.bottleneck && (
                      <Badge variant="destructive" className="ml-auto">
                        {gate.bottleneck}
                      </Badge>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
      <ProjectOrchestratorTasks projectId={projectId} />
    </div>
  );
}

export default LifecycleJourney;
