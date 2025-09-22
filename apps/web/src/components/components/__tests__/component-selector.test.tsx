import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, describe, expect, test, vi } from "vitest";

import { ComponentSelector } from "../component-selector";
import { componentAPI } from "@/lib/api-client";

const MOCK_COMPONENT = {
  id: "comp_100",
  component_management: {
    status: "available",
    version: "1.0",
    component_identity: {
      component_id: "CMP:GENERIC:PV-400:400W:V1.0",
      brand: "Generic",
      part_number: "PV-400",
      rating_w: 400,
      name: "Generic PV 400W",
      classification: {
        unspsc: "26111704",
      },
    },
    compliance: {
      certificates: [],
    },
    inventory: {
      stocks: [
        {
          location: { name: "Warehouse" },
          status: "in_stock",
          uom: "pcs",
          on_hand_qty: 12,
          lots: [],
          serials: [],
        },
      ],
    },
    warranty: {
      terms: {
        duration_years: 10,
      },
    },
  },
};

function renderSelector() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  const utils = render(
    <QueryClientProvider client={queryClient}>
      <ComponentSelector
        open
        onOpenChange={() => {}}
        onComponentsSelected={() => {}}
      />
    </QueryClientProvider>,
  );

  return { ...utils, queryClient };
}

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("ComponentSelector", () => {
  test("queries components endpoint when searching", async () => {
    const listComponentsSpy = vi
      .spyOn(componentAPI, "listComponents")
      .mockImplementation(async () => ({ components: [MOCK_COMPONENT] }));

    const { queryClient } = renderSelector();

    try {
      await waitFor(() => expect(listComponentsSpy).toHaveBeenCalled());

      const user = userEvent.setup();
      const searchInput = screen.getByPlaceholderText("Search components...");
      await user.type(searchInput, "Inverter");

      await waitFor(() => {
        expect(
          listComponentsSpy.mock.calls.some(([params]) => {
            return params?.search === "Inverter";
          }),
        ).toBe(true);
      });
    } finally {
      queryClient.clear();
    }
  });
});
