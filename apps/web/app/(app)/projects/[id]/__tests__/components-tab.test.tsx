import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  afterEach,
  beforeAll,
  beforeEach,
  describe,
  expect,
  test,
  vi,
} from "vitest";

import { apiClient, componentAPI } from "@/lib/api-client";

const projectId = "proj_test";

vi.mock("next/navigation", () => ({
  useParams: () => ({ id: projectId }),
  useRouter: () => ({ push: vi.fn(), back: vi.fn() }),
}));

vi.mock("@/lib/auth/auth-provider", () => ({
  useAuth: () => ({
    user: { id: "user-1", email: "user@example.com" },
    isAuthenticated: true,
    tokens: null,
    login: vi.fn(),
    logout: vi.fn(),
    isLoading: false,
  }),
}));

vi.mock("@/components/odl-sd", () => ({
  DocumentViewer: () => <div data-testid="document-viewer" />,
  SystemDiagram: () => <div data-testid="system-diagram" />,
}));

let ProjectDetailPage: typeof import("../page").default;

beforeAll(async () => {
  ProjectDetailPage = (await import("../page")).default;
});

const MOCK_COMPONENT = {
  id: "comp_200",
  component_management: {
    status: "available",
    version: "1.0",
    component_identity: {
      component_id: "CMP:GENERIC:INV-50:50KW:V1.0",
      brand: "InverterCo",
      part_number: "INV-50",
      rating_w: 50000,
      name: "InverterCo 50kW",
      classification: {
        unspsc: "26111705",
      },
    },
    compliance: {
      certificates: [],
    },
    inventory: {
      stocks: [
        {
          location: { name: "Main" },
          status: "in_stock",
          uom: "pcs",
          on_hand_qty: 8,
          lots: [],
          serials: [],
        },
      ],
    },
    warranty: {
      terms: {
        duration_years: 5,
      },
    },
  },
};

const MOCK_PROJECT = {
  id: projectId,
  project_name: "Demo Project",
  name: "Demo Project",
  description: "A sample project",
  domain: "PV",
  scale: "UTILITY",
  status: "draft",
  display_status: "draft",
  completion_percentage: 0,
  location_name: "Test Site",
  total_capacity_kw: 1000,
  tags: [],
  owner_id: "user-1",
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

const MOCK_DOCUMENT = {
  $schema: "https://odl-sd.org/schemas/v4.1/document.json",
  schema_version: "4.1",
  meta: {
    project: MOCK_PROJECT.project_name,
    domain: MOCK_PROJECT.domain,
    scale: MOCK_PROJECT.scale,
    units: {
      system: "SI",
      currency: "USD",
      coordinate_system: "EPSG:4326",
    },
    timestamps: {
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
    versioning: {
      document_version: "4.1.0",
      content_hash: "hash",
    },
  },
  hierarchy: {
    type: "PORTFOLIO",
    id: `portfolio-${projectId}`,
    children: [],
    portfolio: {
      id: `portfolio-${projectId}`,
      name: MOCK_PROJECT.project_name,
      total_capacity_gw: 0,
      description: "",
      location: "",
      regions: {},
    },
  },
  requirements: {
    functional: { capacity_kw: 0, annual_generation_kwh: 0 },
    technical: { grid_connection: true },
  },
  libraries: {
    components: [],
  },
  instances: [],
  connections: [],
};

const MOCK_DOCUMENT_LIST = [
  {
    id: `${projectId}-main`,
    project_id: projectId,
    document_type: "ODL_SD",
    is_primary: true,
    name: "Main System Document",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

describe("Project components tab", () => {
  let spies: Array<vi.SpyInstance>;

  beforeEach(() => {
    spies = [];
    vi.clearAllMocks();

    spies.push(
      vi.spyOn(apiClient, "getProject").mockResolvedValue(MOCK_PROJECT),
    );
    spies.push(
      vi
        .spyOn(apiClient, "getPrimaryProjectDocument")
        .mockResolvedValue(MOCK_DOCUMENT),
    );
    spies.push(
      vi
        .spyOn(apiClient, "getProjectDocuments")
        .mockResolvedValue(MOCK_DOCUMENT_LIST),
    );
    spies.push(
      vi
        .spyOn(componentAPI, "listComponents")
        .mockImplementation(async () => ({ components: [MOCK_COMPONENT] })),
    );
    spies.push(
      vi
        .spyOn(apiClient, "addComponentsToProject")
        .mockResolvedValue({ ok: true }),
    );
  });

  afterEach(() => {
    cleanup();
    spies.forEach((spy) => spy.mockRestore());
    spies = [];
    vi.clearAllMocks();
  });

  test("adds selected components to the project", async () => {
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });
    const invalidateSpy = vi.spyOn(queryClient, "invalidateQueries");

    const user = userEvent.setup();

    render(
      <QueryClientProvider client={queryClient}>
        <ProjectDetailPage />
      </QueryClientProvider>,
    );

    await waitFor(() =>
      expect(apiClient.getPrimaryProjectDocument).toHaveBeenCalledWith(
        projectId,
      ),
    );

    await waitFor(() =>
      expect(screen.getByText("Project Components")).toBeInTheDocument(),
    );

    await user.click(screen.getByRole("button", { name: /Add Components/i }));

    await screen.findByText(/InverterCo INV-50/);

    await user.click(screen.getByText(/InverterCo INV-50/));

    const confirmButton = await screen.findByRole("button", {
      name: /Add 1 Component/i,
    });

    await user.click(confirmButton);

    await waitFor(() => {
      expect(apiClient.addComponentsToProject).toHaveBeenCalledWith(
        projectId,
        expect.objectContaining({
          components: [
            expect.objectContaining({
              component_id:
                MOCK_COMPONENT.component_management.component_identity
                  .component_id,
              quantity: 1,
            }),
          ],
        }),
      );
    });

    await waitFor(() => {
      expect(
        invalidateSpy.mock.calls.filter((call: any) => {
          const arg = call[0];
          return (
            arg?.queryKey?.[0] === "project-document" ||
            arg?.queryKey?.[0] === "project-documents"
          );
        }).length,
      ).toBeGreaterThanOrEqual(2);
    });

    queryClient.clear();
  });
});
