
import type { ReactElement } from "react";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { DocumentTab } from "../../app/(app)/projects/[id]/DocumentTab";
import { ApiError, apiClient } from "@/lib/api-client";
import type { OdlDocument } from "@/lib/types";
import { toast } from "react-hot-toast";

vi.mock("@monaco-editor/react", () => ({
  __esModule: true,
  default: ({ value, onChange, ...props }: any) => (
    <textarea
      {...props}
      value={value ?? ""}
      onChange={(event) => onChange?.(event.target.value)}
    />
  ),
}));

vi.mock("react-hot-toast", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

describe("DocumentTab", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  const renderWithClient = (
    ui: ReactElement,
    client?: QueryClient,
  ) => {
    const queryClient =
      client ??
      new QueryClient({
        defaultOptions: { queries: { retry: false } },
      });

    const view = render(
      <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>,
    );

    return { queryClient, ...view };
  };

  const createDeferred = <T,>() => {
    let resolve!: (value: T | PromiseLike<T>) => void;
    let reject!: (reason?: unknown) => void;
    const promise = new Promise<T>((res, rej) => {
      resolve = res;
      reject = rej;
    });
    return { promise, resolve, reject };
  };

  const baseDocument: OdlDocument = {
    $schema: "https://odl-sd.org/schemas/v4.1/document.json",
    schema_version: "4.1",
    meta: {
      project: "Test Project",
      domain: "PV",
      scale: "UTILITY",
      units: {
        system: "SI",
        currency: "USD",
        coordinate_system: "EPSG:4326",
      },
      timestamps: {
        created_at: "2024-01-01T00:00:00Z",
        updated_at: "2024-01-02T00:00:00Z",
      },
      versioning: {
        document_version: "4.1.0",
        content_hash: "sha256:initial",
      },
    },
    hierarchy: { type: "PORTFOLIO", id: "portfolio-1", children: [] },
    requirements: { functional: {}, technical: {} },
    libraries: { components: [] },
    instances: [],
    connections: [],
    analysis: [],
    audit: [],
    data_management: {
      partitioning_enabled: false,
      external_refs_enabled: false,
      streaming_enabled: false,
      max_document_size_mb: 100,
    },
  } as unknown as OdlDocument;

  it("applies optimistic updates while saving", async () => {
    const user = userEvent.setup();
    const projectId = "project-123";
    const documentId = "project-123-main";

    const deferred = createDeferred<any>();
    const updateSpy = vi
      .spyOn(apiClient, "updateDocument")
      .mockReturnValue(deferred.promise);

    const updatedDocument = JSON.parse(
      JSON.stringify(baseDocument),
    ) as OdlDocument;
    updatedDocument.meta!.project = "Updated Project";
    if (updatedDocument.meta?.versioning) {
      updatedDocument.meta.versioning.content_hash = "sha256:updated";
    }

    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    queryClient.setQueryData(["project-document", projectId], baseDocument);
    queryClient.setQueryData(["project-documents", projectId], [
      { id: documentId, updated_at: "2024-01-02T00:00:00Z" },
    ]);

    renderWithClient(
      <DocumentTab
        documentId={documentId}
        document={baseDocument}
        projectId={projectId}
      />,
      queryClient,
    );

    const editor = screen.getByTestId("document-json-editor");
    await user.clear(editor);
    fireEvent.change(editor, {
      target: { value: JSON.stringify(updatedDocument, null, 2) },
    });

    const saveButton = screen.getByRole("button", { name: /save/i });
    await user.click(saveButton);

    expect(updateSpy).toHaveBeenCalledWith(
      documentId,
      expect.objectContaining({
        meta: expect.objectContaining({ project: "Updated Project" }),
      }),
    );
    expect(
      queryClient.getQueryData(["project-document", projectId]),
    ).toEqual(
      expect.objectContaining({
        meta: expect.objectContaining({ project: "Updated Project" }),
      }),
    );

    deferred.resolve({
      document: updatedDocument,
      updated_at: "2024-01-03T00:00:00Z",
      current_version: 2,
      content_hash: "sha256:updated",
    });

    await waitFor(() =>
      expect(
        queryClient.getQueryData(["project-document", projectId]),
      ).toEqual(
        expect.objectContaining({
          meta: expect.objectContaining({ project: "Updated Project" }),
        }),
      ),
    );

    expect(toast.success).toHaveBeenCalledWith("Document saved");
  });

  it("shows validation errors and rolls back optimistic updates on failure", async () => {
    const user = userEvent.setup();
    const projectId = "project-123";
    const documentId = "project-123-main";

    const error = new ApiError(
      "HTTP 400: Bad Request",
      400,
      JSON.stringify({ detail: "Document failed validation" }),
    );
    vi.spyOn(apiClient, "updateDocument").mockRejectedValue(error);

    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    queryClient.setQueryData(["project-document", projectId], baseDocument);
    queryClient.setQueryData(["project-documents", projectId], [
      { id: documentId, updated_at: "2024-01-02T00:00:00Z" },
    ]);

    renderWithClient(
      <DocumentTab
        documentId={documentId}
        document={baseDocument}
        projectId={projectId}
      />,
      queryClient,
    );

    const editor = screen.getByTestId("document-json-editor");
    await user.clear(editor);
    const invalidDocument = JSON.parse(JSON.stringify(baseDocument)) as OdlDocument;
    invalidDocument.meta!.project = "Invalid Project";
    fireEvent.change(editor, {
      target: { value: JSON.stringify(invalidDocument, null, 2) },
    });

    const saveButton = screen.getByRole("button", { name: /save/i });
    await user.click(saveButton);

    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent(
        "Document failed validation",
      ),
    );

    expect(
      queryClient.getQueryData(["project-document", projectId]),
    ).toEqual(baseDocument);
    expect(toast.error).toHaveBeenCalledWith("Document failed validation");
  });
});
