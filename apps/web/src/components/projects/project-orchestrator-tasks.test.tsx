import type { ReactNode } from "react";

import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, describe, expect, it, vi } from "vitest";

import { apiClient } from "@/lib/api-client";

import { ProjectOrchestratorTasks } from "./project-orchestrator-tasks";

const renderWithQueryClient = (ui: ReactNode) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>,
  );
};

describe("ProjectOrchestratorTasks", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders orchestrator task statuses and latest message", async () => {
    const getTasksSpy = vi
      .spyOn(apiClient, "getProjectTasks")
      .mockResolvedValue([
        {
          id: "task-1",
          status: "in_progress",
          created_at: "2024-01-01T10:00:00Z",
          updated_at: "2024-01-01T11:00:00Z",
          latest_message: "Latest update from orchestrator.",
        },
        {
          id: "task-2",
          status: "completed",
          created_at: "2024-01-01T08:00:00Z",
          updated_at: "2024-01-01T09:00:00Z",
          messages: [
            {
              id: "message-1",
              content: "Task finished successfully.",
              created_at: "2024-01-01T09:00:00Z",
            },
          ],
        },
      ]);

    renderWithQueryClient(
      <ProjectOrchestratorTasks projectId="proj-123" />,
    );

    expect(getTasksSpy).toHaveBeenCalledWith("proj-123");

    expect(await screen.findByText("In Progress")).toBeInTheDocument();
    expect(await screen.findByText("Completed")).toBeInTheDocument();
    expect(
      await screen.findByText("Latest update from orchestrator."),
    ).toBeInTheDocument();
    expect(
      await screen.findByText("Task finished successfully."),
    ).toBeInTheDocument();
  });

  it("renders an empty state when no tasks exist", async () => {
    vi.spyOn(apiClient, "getProjectTasks").mockResolvedValue([]);

    renderWithQueryClient(
      <ProjectOrchestratorTasks projectId="proj-empty" />,
    );

    expect(
      await screen.findByText(
        "No orchestrator tasks have been created for this project yet.",
      ),
    ).toBeInTheDocument();
  });
});
