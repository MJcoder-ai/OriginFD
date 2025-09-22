"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import type { DocumentVersion } from "@originfd/types-odl";
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@originfd/ui";
import { Loader2 } from "lucide-react";

import JsonPatchViewer from "@/components/diff/json-patch-viewer";
import { apiClient } from "@/lib/api-client";

type DiffViewerProps = React.ComponentProps<typeof JsonPatchViewer>;

type DiffViewerComponent = (props: DiffViewerProps) => JSX.Element;

interface TimelineClient {
  getDocumentVersions: (documentId: string) => Promise<DocumentVersion[]>;
  getDocument: (documentId: string, version: number) => Promise<any>;
}

interface DocumentVersionTimelineProps {
  documentId: string;
  client?: TimelineClient;
  DiffViewerComponent?: DiffViewerComponent;
}

const defaultClient: TimelineClient = {
  getDocumentVersions: (documentId) => apiClient.getDocumentVersions(documentId),
  getDocument: (documentId, version) => apiClient.getDocument(documentId, version),
};

const defaultDiffViewer: DiffViewerComponent = (props) => (
  <JsonPatchViewer {...props} />
);

const formatDateTime = (value: string) => {
  try {
    const date = new Date(value);
    return new Intl.DateTimeFormat("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }).format(date);
  } catch (error) {
    return value;
  }
};

export function DocumentVersionTimeline({
  documentId,
  client,
  DiffViewerComponent,
}: DocumentVersionTimelineProps) {
  const resolvedClient = React.useMemo(() => client ?? defaultClient, [client]);
  const DiffViewer = DiffViewerComponent ?? defaultDiffViewer;

  const { data: versions = [], isLoading, isError } = useQuery({
    queryKey: ["document-versions", documentId],
    queryFn: () => resolvedClient.getDocumentVersions(documentId),
    enabled: Boolean(documentId),
    staleTime: 5 * 60 * 1000,
  });

  const sortedVersions = React.useMemo(
    () => [...versions].sort((a, b) => b.version_number - a.version_number),
    [versions],
  );

  const [selectedVersions, setSelectedVersions] = React.useState<number[]>([]);

  const toggleVersion = (versionNumber: number) => {
    setSelectedVersions((previous) => {
      if (previous.includes(versionNumber)) {
        return previous.filter((item) => item !== versionNumber);
      }

      if (previous.length === 0) {
        return [versionNumber];
      }

      if (previous.length === 1) {
        const next = [...previous, versionNumber];
        if (next[0] > next[1]) {
          return [next[1], next[0]];
        }
        return next;
      }

      const next = [previous[1], versionNumber];
      if (next[0] > next[1]) {
        return [next[1], next[0]];
      }
      return next;
    });
  };

  const baseVersionNumber = selectedVersions[0];
  const compareVersionNumber = selectedVersions[1];

  const baseQuery = useQuery({
    queryKey: ["document-version", documentId, baseVersionNumber],
    queryFn: () =>
      resolvedClient.getDocument(documentId, baseVersionNumber as number),
    enabled: Boolean(documentId && baseVersionNumber !== undefined),
    staleTime: 5 * 60 * 1000,
  });

  const compareQuery = useQuery({
    queryKey: ["document-version", documentId, compareVersionNumber],
    queryFn: () =>
      resolvedClient.getDocument(documentId, compareVersionNumber as number),
    enabled: Boolean(documentId && compareVersionNumber !== undefined),
    staleTime: 5 * 60 * 1000,
  });

  const baseVersion = sortedVersions.find(
    (version) => version.version_number === baseVersionNumber,
  );
  const compareVersion = sortedVersions.find(
    (version) => version.version_number === compareVersionNumber,
  );

  const diffLoading = baseQuery.isLoading || compareQuery.isLoading;
  const diffError = baseQuery.error || compareQuery.error;
  const diffReady =
    Boolean(baseQuery.data && compareQuery.data) &&
    selectedVersions.length === 2;

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Version History</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading document versions…
            </div>
          ) : isError ? (
            <p className="text-sm text-destructive">
              Unable to load version history. Please try again later.
            </p>
          ) : sortedVersions.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No version history is available for this document yet.
            </p>
          ) : (
            <ul className="space-y-3">
              {sortedVersions.map((version) => {
                const isSelected = selectedVersions.includes(
                  version.version_number,
                );
                const selectionIndex = selectedVersions.indexOf(
                  version.version_number,
                );
                const selectionBadge =
                  selectionIndex === 0
                    ? "Base"
                    : selectionIndex === 1
                    ? "Compare"
                    : null;

                const buttonLabel = isSelected
                  ? "Deselect"
                  : selectedVersions.length >= 2
                  ? "Swap in"
                  : "Select";

                return (
                  <li key={version.version_number} className="relative pl-4">
                    <span className="absolute left-0 top-4 h-2 w-2 -translate-x-1 rounded-full bg-muted-foreground/70" />
                    <div
                      className={`rounded-lg border p-4 transition-colors ${
                        isSelected
                          ? "border-primary bg-primary/5"
                          : "border-border"
                      }`}
                    >
                      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                        <div>
                          <div className="flex items-center gap-2">
                            <p className="font-medium">
                              Version v{version.version_number}
                            </p>
                            {selectionBadge && (
                              <Badge variant="secondary">{selectionBadge}</Badge>
                            )}
                          </div>
                          <p className="text-xs text-muted-foreground">
                            {formatDateTime(version.created_at)} • {version.created_by}
                          </p>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge variant="outline">
                            {version.patch_operations_count} patch ops
                          </Badge>
                          <Button
                            size="sm"
                            variant={isSelected ? "default" : "outline"}
                            onClick={() => toggleVersion(version.version_number)}
                          >
                            {buttonLabel}
                          </Button>
                        </div>
                      </div>
                      {version.change_summary && (
                        <p className="mt-2 text-sm text-muted-foreground">
                          {version.change_summary}
                        </p>
                      )}
                      <p className="mt-2 text-xs text-muted-foreground">
                        Hash: <span className="font-mono">{version.content_hash}</span>
                      </p>
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Comparison</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {selectedVersions.length < 2 ? (
            <p className="text-sm text-muted-foreground">
              Select two versions from the timeline to review a detailed diff.
            </p>
          ) : diffLoading ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Building diff…
            </div>
          ) : diffError ? (
            <p className="text-sm text-destructive">
              Unable to load the selected versions. Please try selecting them
              again.
            </p>
          ) : diffReady ? (
            <div className="space-y-3">
              <div className="flex flex-col gap-2 text-sm text-muted-foreground md:flex-row md:items-center md:justify-between">
                <div>
                  <span className="font-medium text-foreground">
                    Comparing v{baseVersion?.version_number}
                  </span>{" "}
                  → v{compareVersion?.version_number}
                </div>
                <div className="flex gap-2 text-xs text-muted-foreground">
                  <span>Base hash: {baseVersion?.content_hash}</span>
                  <span>Compare hash: {compareVersion?.content_hash}</span>
                </div>
              </div>
              <DiffViewer
                original={baseQuery.data}
                updated={compareQuery.data}
              />
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              Unable to prepare the diff for the selected versions.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default DocumentVersionTimeline;
