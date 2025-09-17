"use client";

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Button,
  Badge,
  Dialog,
  DialogTrigger,
  DialogContent,
} from "@originfd/ui";
import { Copy, Check } from "lucide-react";

interface PlannerTraceProps {
  runId: string;
}

interface PlannerTraceStep {
  id: string;
  tool: string;
  params: Record<string, any>;
  cached?: boolean;
  psu_cost?: number;
  latency_ms?: number;
  evidence?: string[];
  patch?: any;
}

interface PlannerTraceData {
  run_id: string;
  steps: PlannerTraceStep[];
}

export function PlannerTrace({ runId }: PlannerTraceProps) {
  const { data, isLoading, error } = useQuery<PlannerTraceData>({
    queryKey: ["planner-trace", runId],
    queryFn: () => apiClient.getPlannerTrace(runId),
    enabled: !!runId,
  });

  const [copied, setCopied] = useState(false);

  const copyRunId = async () => {
    try {
      await navigator.clipboard.writeText(runId);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (e) {
      console.error("Failed to copy run id", e);
    }
  };

  if (isLoading) return <div>Loading trace...</div>;
  if (error || !data) return <div>Failed to load trace.</div>;

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <h2 className="text-xl font-semibold">Run {data.run_id}</h2>
        <Button
          variant="ghost"
          size="icon"
          onClick={copyRunId}
          aria-label="Copy run id"
        >
          {copied ? (
            <Check className="h-4 w-4" />
          ) : (
            <Copy className="h-4 w-4" />
          )}
        </Button>
      </div>
      <ol className="relative border-l pl-4">
        {data.steps.map((step, idx) => (
          <li key={step.id} className="mb-10 ml-4">
            <span className="absolute flex items-center justify-center w-6 h-6 rounded-full -left-3 ring-4 ring-background bg-primary text-primary-foreground text-xs">
              {idx + 1}
            </span>
            <Card>
              <CardHeader className="pb-2">
                <div className="flex items-center gap-2">
                  <CardTitle className="text-sm font-medium">
                    {step.tool}
                  </CardTitle>
                  {step.cached && <Badge variant="secondary">cache</Badge>}
                </div>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <pre className="bg-muted p-2 rounded text-xs overflow-x-auto">
                  {JSON.stringify(step.params, null, 2)}
                </pre>
                <div className="flex gap-4 text-xs text-muted-foreground">
                  <span>Cost: {step.psu_cost ?? 0} PSU</span>
                  <span>Latency: {step.latency_ms ?? 0} ms</span>
                </div>
                <div className="flex gap-4 text-xs">
                  {step.evidence && step.evidence.length > 0 && (
                    <a
                      href={step.evidence[0]}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary underline"
                    >
                      open evidence
                    </a>
                  )}
                  {step.patch && step.patch.length > 0 && (
                    <Dialog>
                      <DialogTrigger asChild>
                        <Button
                          variant="link"
                          className="p-0 h-auto text-xs font-normal"
                        >
                          view diff
                        </Button>
                      </DialogTrigger>
                      <DialogContent className="max-h-[80vh] overflow-y-auto">
                        <pre className="text-xs whitespace-pre-wrap">
                          {JSON.stringify(step.patch, null, 2)}
                        </pre>
                      </DialogContent>
                    </Dialog>
                  )}
                </div>
              </CardContent>
            </Card>
          </li>
        ))}
      </ol>
    </div>
  );
}

export default PlannerTrace;
