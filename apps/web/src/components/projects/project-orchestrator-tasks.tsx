"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Loader2, AlertCircle, MessageSquareText } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Badge,
  Separator,
} from "@originfd/ui";

import { apiClient } from "@/lib/api-client";

interface OrchestratorTaskMessage {
  id?: string;
  content: string;
  created_at?: string | null;
}

export interface OrchestratorTask {
  id: string;
  status: string;
  created_at?: string | null;
  updated_at?: string | null;
  latest_message?: string | null;
  messages?: OrchestratorTaskMessage[];
}

interface ProjectOrchestratorTasksProps {
  projectId: string;
}

const statusVariants: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  completed: "default",
  success: "default",
  done: "default",
  in_progress: "secondary",
  running: "secondary",
  queued: "secondary",
  pending: "secondary",
  failed: "destructive",
  error: "destructive",
  cancelled: "outline",
};

const toTitleCase = (value: string): string =>
  value
    .split(/[_\s]+/)
    .map((segment) =>
      segment.length > 0
        ? segment.charAt(0).toUpperCase() + segment.slice(1).toLowerCase()
        : "",
    )
    .join(" ");

const formatTimestamp = (value?: string | null): string => {
  if (!value) {
    return "—";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
};

const resolveLatestMessage = (task: OrchestratorTask): string => {
  if (task.latest_message && task.latest_message.trim().length > 0) {
    return task.latest_message;
  }

  if (task.messages && task.messages.length > 0) {
    const lastMessage = [...task.messages].sort((a, b) => {
      const timeA = a.created_at ? new Date(a.created_at).getTime() : 0;
      const timeB = b.created_at ? new Date(b.created_at).getTime() : 0;
      return timeB - timeA;
    })[0];

    if (lastMessage && lastMessage.content.trim().length > 0) {
      return lastMessage.content;
    }
  }

  return "No updates yet.";
};

export function ProjectOrchestratorTasks({
  projectId,
}: ProjectOrchestratorTasksProps) {
  const { data, isLoading, isError, error } = useQuery<OrchestratorTask[]>({
    queryKey: ["project", projectId, "tasks"],
    queryFn: () => apiClient.getProjectTasks(projectId),
  });

  const tasks = useMemo(() => data ?? [], [data]);

  const renderBody = () => {
    if (isLoading) {
      return (
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading orchestrator tasks...
        </div>
      );
    }

    if (isError) {
      return (
        <div className="flex items-center gap-2 text-sm text-red-500">
          <AlertCircle className="h-4 w-4" />
          {error instanceof Error
            ? error.message
            : "Failed to load orchestrator tasks"}
        </div>
      );
    }

    if (!tasks.length) {
      return (
        <CardDescription>
          No orchestrator tasks have been created for this project yet.
        </CardDescription>
      );
    }

    return (
      <div className="space-y-4">
        {tasks.map((task) => {
          const statusValue = task.status ?? "unknown";
          const variant =
            statusVariants[statusValue.toLowerCase()] ?? "outline";
          const latestMessage = resolveLatestMessage(task);
          const statusLabel = toTitleCase(statusValue);

          return (
            <div key={task.id} className="space-y-3 rounded-lg border p-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <Badge variant={variant}>{statusLabel}</Badge>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Created: {formatTimestamp(task.created_at)}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Updated: {formatTimestamp(task.updated_at)}
                  </div>
                </div>
              </div>
              <Separator />
              <div className="flex items-start gap-2 text-sm">
                <MessageSquareText className="mt-0.5 h-4 w-4 text-muted-foreground" />
                <p className="leading-relaxed text-muted-foreground">
                  {latestMessage}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Orchestrator Tasks</CardTitle>
        <CardDescription>
          Track the latest orchestration activity, status changes, and
          messages for this project.
        </CardDescription>
      </CardHeader>
      <CardContent>{renderBody()}</CardContent>
    </Card>
  );
}

export default ProjectOrchestratorTasks;
