import * as React from "react";
import { act, cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import LifecycleJourney from "@/components/projects/lifecycle-journey";
import {
  apiClient,
  type GateStatus,
  type LifecyclePhaseView,
} from "@/lib/api-client";

vi.mock("next/link", () => ({
  __esModule: true,
  default: ({ children, href, ...props }: any) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

vi.mock("lucide-react", () => ({
  __esModule: true,
  AlertTriangle: (props: any) => <svg {...props} />,
  CheckCircle2: (props: any) => <svg {...props} />,
  CircleX: (props: any) => <svg {...props} />,
  Clock: (props: any) => <svg {...props} />,
  Loader2: (props: any) => <svg {...props} />,
}));

vi.mock("@/lib/auth/auth-provider", () => ({
  useAuth: () => ({
    user: {
      id: "user-1",
      email: "user@example.com",
      roles: ["role.project_manager"],
    },
    isAuthenticated: true,
    isLoading: false,
    login: vi.fn(),
    logout: vi.fn(),
    tokens: null,
  }),
}));

vi.mock("@/components/projects/project-orchestrator-tasks", () => ({
  ProjectOrchestratorTasks: () => (
    <div data-testid="project-orchestrator-tasks" />
  ),
}));

const projectId = "project-123";
const activeClients: QueryClient[] = [];

const buildPhase = (
  index: number,
  gateStatuses: [GateStatus, GateStatus] = ["NOT_STARTED", "NOT_STARTED"],
): LifecyclePhaseView => ({
  phase_code: index,
  phase_key: `phase.${index}`,
  title: `Phase ${index + 1}`,
  order: index,
  entry_gate_code: `G${index}E`,
  exit_gate_code: `G${index}X`,
  required_entry_roles: ["role.project_manager"],
  required_exit_roles: ["role.engineer"],
  odl_sd_sections: [`section-${index}`],
  name: `Legacy ${index + 1}`,
  status: "scheduled",
  gates: [
    {
      key: `G${index}E`,
      name: "Entry",
      gate_code: `G${index}E`,
      status: gateStatuses[0],
    },
    {
      key: `G${index}X`,
      name: "Exit",
      gate_code: `G${index}X`,
      status: gateStatuses[1],
    },
  ],
});

const renderLifecycle = async (phases: LifecyclePhaseView[]) => {
  const getLifecycleSpy = vi
    .spyOn(apiClient, "getProjectLifecycle")
    .mockResolvedValue(phases);

  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  activeClients.push(queryClient);

  await act(async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <LifecycleJourney projectId={projectId} />
      </QueryClientProvider>,
    );
  });

  await waitFor(() => expect(getLifecycleSpy).toHaveBeenCalled());

  return { queryClient };
};

const entryPattern = (gateCode: string, status?: string) =>
  new RegExp(
    `Entry[\\s\\S]*${gateCode}${status ? `[\\s\\S]*${status}` : ""}`,
    "i",
  );

const exitPattern = (gateCode: string, status?: string) =>
  new RegExp(
    `Exit[\\s\\S]*${gateCode}${status ? `[\\s\\S]*${status}` : ""}`,
    "i",
  );

describe("LifecycleJourney", () => {
  beforeEach(() => {
    process.env.NEXT_PUBLIC_LIFECYCLE_V2 = "1";
  });

  afterEach(() => {
    cleanup();
    activeClients.forEach((client) => client.clear());
    activeClients.length = 0;
    vi.restoreAllMocks();
  });

  it("renders 12 phases with entry and exit gates", async () => {
    const phases = Array.from({ length: 12 }, (_, index) => buildPhase(index));
    const { queryClient } = await renderLifecycle(phases);

    const headings = await screen.findAllByRole("heading", {
      name: /^P\d+: Phase \d+$/i,
    });
    expect(headings).toHaveLength(12);

    const gateButtons = (await screen.findAllByRole("button")).filter(
      (button) => {
        const label = button.textContent ?? "";
        return /Entry/i.test(label) || /Exit/i.test(label);
      },
    );
    expect(gateButtons).toHaveLength(24);

    for (const phase of phases) {
      await waitFor(() => {
        expect(
          screen.getAllByText(phase.entry_gate_code).length,
        ).toBeGreaterThan(0);
      });
      await waitFor(() => {
        expect(
          screen.getAllByText(phase.exit_gate_code).length,
        ).toBeGreaterThan(0);
      });
    }

    await waitFor(() => expect(queryClient.isFetching()).toBe(0));
  });

  it("shows status badges for in-progress and approved gates", async () => {
    const phases = [
      buildPhase(0, ["IN_PROGRESS", "APPROVED"]),
      ...Array.from({ length: 11 }, (_, index) => buildPhase(index + 1)),
    ];
    const { queryClient } = await renderLifecycle(phases);

    expect(
      await screen.findByRole("button", {
        name: entryPattern("G0E", "In Progress"),
      }),
    ).toBeInTheDocument();

    expect(
      await screen.findByRole("button", {
        name: exitPattern("G0X", "Approved"),
      }),
    ).toBeInTheDocument();

    await waitFor(() => expect(queryClient.isFetching()).toBe(0));
  });

  it("submits gate approvals with the new payload and refreshes gate status", async () => {
    const phases = Array.from({ length: 12 }, (_, index) => buildPhase(index));
    const { queryClient } = await renderLifecycle(phases);

    const updatedPhases = phases.map((phase, index) => {
      if (index === 0) {
        return {
          ...phase,
          gates: [
            { ...phase.gates[0], status: "APPROVED" },
            { ...phase.gates[1] },
          ],
        } satisfies LifecyclePhaseView;
      }
      return {
        ...phase,
        gates: phase.gates.map((gate) => ({ ...gate })),
      } satisfies LifecyclePhaseView;
    });

    const postSpy = vi
      .spyOn(apiClient, "postGateApproval")
      .mockResolvedValue(updatedPhases);

    const roleInput = await screen.findByLabelText(/Role key/i);
    const commentInput = screen.getByLabelText(/Comment/i);
    const user = userEvent.setup();

    await user.clear(roleInput);
    await user.type(roleInput, "role.project_manager");
    await user.type(commentInput, "Ready for launch");

    const submitButton = screen.getByRole("button", {
      name: /submit decision/i,
    });
    await act(async () => {
      await user.click(submitButton);
    });

    await waitFor(() =>
      expect(postSpy).toHaveBeenCalledWith(
        projectId,
        expect.objectContaining({
          phase_code: 0,
          gate_code: "G0E",
          decision: "APPROVE",
          role_key: "role.project_manager",
          comment: expect.any(String),
        }),
      ),
    );

    await waitFor(() =>
      expect(
        screen.getByRole("button", {
          name: entryPattern("G0E", "Approved"),
        }),
      ).toBeInTheDocument(),
    );

    await waitFor(() => expect(queryClient.isFetching()).toBe(0));
  });
});
