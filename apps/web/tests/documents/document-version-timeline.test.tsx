import { strict as assert } from "node:assert";
import test from "node:test";
import * as React from "react";
import { JSDOM } from "jsdom";
import {
  cleanup,
  fireEvent,
  render,
  waitFor,
  within,
} from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { DocumentVersion } from "@originfd/types-odl";

import { DocumentVersionTimeline } from "../../src/components/odl-sd/document-version-timeline";

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost",
});

globalThis.window = dom.window as unknown as Window & typeof globalThis;
globalThis.document = dom.window.document;
globalThis.navigator = dom.window.navigator as Navigator;
globalThis.HTMLElement = dom.window.HTMLElement;
globalThis.Node = dom.window.Node;
globalThis.MutationObserver = dom.window.MutationObserver;
// Silence act warnings in React 18 tests
// @ts-expect-error - this flag is used by React testing utilities
globalThis.IS_REACT_ACT_ENVIRONMENT = true;

test.afterEach(() => {
  cleanup();
});

interface TestClient {
  getDocumentVersions: (documentId: string) => Promise<DocumentVersion[]>;
  getDocument: (documentId: string, version: number) => Promise<any>;
}

const sampleVersions: DocumentVersion[] = [
  {
    version_number: 3,
    content_hash: "sha256:test-v3",
    change_summary: "Adjusted inverter specification",
    created_by: "alex.johnson",
    created_at: "2024-01-20T10:00:00Z",
    patch_operations_count: 5,
  },
  {
    version_number: 2,
    content_hash: "sha256:test-v2",
    change_summary: "Updated module counts",
    created_by: "maria.lopez",
    created_at: "2024-01-15T09:00:00Z",
    patch_operations_count: 8,
  },
  {
    version_number: 1,
    content_hash: "sha256:test-v1",
    change_summary: "Initial import",
    created_by: "alex.johnson",
    created_at: "2024-01-10T08:00:00Z",
    patch_operations_count: 0,
  },
];

const documentSnapshots: Record<number, any> = {
  1: {
    meta: {
      versioning: { document_version: "1.0" },
      timestamps: { updated_at: "2024-01-10T08:00:00Z" },
    },
    requirements: { functional: { capacity_kw: 95000 } },
  },
  2: {
    meta: {
      versioning: { document_version: "2.0" },
      timestamps: { updated_at: "2024-01-15T09:00:00Z" },
    },
    requirements: { functional: { capacity_kw: 98000 } },
  },
  3: {
    meta: {
      versioning: { document_version: "3.0" },
      timestamps: { updated_at: "2024-01-20T10:00:00Z" },
    },
    requirements: { functional: { capacity_kw: 100000 } },
  },
};

const renderTimeline = ({
  client,
  DiffViewer,
}: {
  client: TestClient;
  DiffViewer?: (props: { original: any; updated: any }) => JSX.Element;
}) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <DocumentVersionTimeline
        documentId="doc-1"
        client={client}
        DiffViewerComponent={DiffViewer}
      />
    </QueryClientProvider>,
  );
};

test("renders document versions in descending order", async () => {
  const client: TestClient = {
    getDocumentVersions: async () => sampleVersions,
    getDocument: async (_id, version) => documentSnapshots[version],
  };

  const view = renderTimeline({ client });

  await view.findByText("Version v3");
  const versionLabels = view
    .getAllByText(/Version v/)
    .map((node) => node.textContent);
  assert.deepEqual(versionLabels, ["Version v3", "Version v2", "Version v1"]);

  assert.ok(
    view.getByText(
      "Select two versions from the timeline to review a detailed diff.",
    ),
  );
});

test("selecting two versions loads diff viewer", async () => {
  const documentCalls: number[] = [];
  const client: TestClient = {
    getDocumentVersions: async () => sampleVersions,
    getDocument: async (_id, version) => {
      documentCalls.push(version);
      return documentSnapshots[version];
    },
  };

  const diffRenders: Array<{ original: any; updated: any }> = [];
  const DiffViewerStub = ({
    original,
    updated,
  }: {
    original: any;
    updated: any;
  }) => {
    diffRenders.push({ original, updated });
    return (
      <div data-testid="diff-output">
        {original.meta.versioning.document_version}→
        {updated.meta.versioning.document_version}
      </div>
    );
  };

  const view = renderTimeline({ client, DiffViewer: DiffViewerStub });

  const versionOne = await view.findByText("Version v1");
  const versionThree = await view.findByText("Version v3");

  const selectVersionOne = within(versionOne.closest("li")!).getByRole(
    "button",
    { name: /select/i },
  );
  const selectVersionThree = within(versionThree.closest("li")!).getByRole(
    "button",
    { name: /select/i },
  );

  fireEvent.click(selectVersionOne);
  fireEvent.click(selectVersionThree);

  await waitFor(() => {
    assert.equal(diffRenders.length, 1);
  });

  const diffOutput = await view.findByTestId("diff-output");
  assert.equal(diffOutput.textContent, "1.0→3.0");
  assert.deepEqual(
    documentCalls.sort((a, b) => a - b),
    [1, 3],
  );
});
