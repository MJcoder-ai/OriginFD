"use client";

import Editor from "@monaco-editor/react";
import {
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@originfd/ui";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useRef, useState } from "react";
import { toast } from "react-hot-toast";

import { ApiError, apiClient } from "@/lib/api-client";
import type { OdlDocument } from "@/lib/types";

interface DocumentTabProps {
  documentId?: string;
  document?: OdlDocument | null;
  projectId: string;
}

const parseErrorMessage = (error: unknown): string => {
  if (error instanceof ApiError) {
    if (typeof error.response === "string") {
      try {
        const parsed = JSON.parse(error.response);
        if (typeof parsed?.detail === "string") {
          return parsed.detail;
        }
      } catch {
        // Ignore parsing issues and fall back to error.message
      }
    }
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Failed to save document";
};

export function DocumentTab({
  documentId,
  document,
  projectId,
}: DocumentTabProps) {
  const queryClient = useQueryClient();
  const originalValueRef = useRef<string>("");
  const [editorValue, setEditorValue] = useState<string>("");
  const [isDirty, setIsDirty] = useState(false);
  const [parseError, setParseError] = useState<string | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);

  const serializedDocument = useMemo(
    () => (document ? JSON.stringify(document, null, 2) : ""),
    [document],
  );

  useEffect(() => {
    if (!documentId || !document) {
      originalValueRef.current = "";
      setEditorValue("");
      setIsDirty(false);
      setParseError(null);
      setValidationError(null);
      return;
    }

    originalValueRef.current = serializedDocument;
    setEditorValue(serializedDocument);
    setIsDirty(false);
    setParseError(null);
    setValidationError(null);
  }, [document, documentId, serializedDocument]);

  const mutation = useMutation({
    mutationFn: async (value: string) => {
      const parsed = JSON.parse(value);
      return apiClient.updateDocument(documentId as string, parsed);
    },
    onMutate: async (value: string) => {
      const parsed = JSON.parse(value);
      setValidationError(null);

      const documentKey = ["project-document", projectId];
      const documentsKey = ["project-documents", projectId];

      await queryClient.cancelQueries({ queryKey: documentKey });
      await queryClient.cancelQueries({ queryKey: documentsKey });

      const previousDocument = queryClient.getQueryData(documentKey);
      const previousDocuments = queryClient.getQueryData(documentsKey);

      queryClient.setQueryData(documentKey, parsed);
      queryClient.setQueryData(documentsKey, (docs: any) => {
        if (!Array.isArray(docs)) {
          return docs;
        }

        const updatedAt = new Date().toISOString();
        return docs.map((doc) =>
          doc?.id === documentId ? { ...doc, updated_at: updatedAt } : doc,
        );
      });

      return { previousDocument, previousDocuments, parsed };
    },
    onError: (error, _value, context) => {
      const documentKey = ["project-document", projectId];
      const documentsKey = ["project-documents", projectId];

      if (context?.previousDocument !== undefined) {
        queryClient.setQueryData(documentKey, context.previousDocument);
      }
      if (context?.previousDocuments !== undefined) {
        queryClient.setQueryData(documentsKey, context.previousDocuments);
      }

      const message = parseErrorMessage(error);
      setValidationError(message);
      toast.error(message);
    },
    onSuccess: (response: any, value: string, context) => {
      const documentKey = ["project-document", projectId];
      const documentsKey = ["project-documents", projectId];

      const parsedValue = context?.parsed ?? JSON.parse(value);
      const nextDocument =
        (response && (response.document ?? response)) || parsedValue;

      queryClient.setQueryData(documentKey, nextDocument);
      queryClient.setQueryData(documentsKey, (docs: any) => {
        if (!Array.isArray(docs)) {
          return docs;
        }

        const updatedAt =
          (response && typeof response.updated_at === "string"
            ? response.updated_at
            : new Date().toISOString());

        return docs.map((doc) =>
          doc?.id === documentId
            ? {
                ...doc,
                updated_at: updatedAt,
                current_version:
                  response?.current_version ?? doc?.current_version ?? 1,
                content_hash: response?.content_hash ?? doc?.content_hash,
              }
            : doc,
        );
      });

      const formatted = JSON.stringify(nextDocument, null, 2);
      originalValueRef.current = formatted;
      setEditorValue(formatted);
      setIsDirty(false);
      setParseError(null);
      setValidationError(null);
      toast.success("Document saved");
    },
    onSettled: () => {
      const documentKey = ["project-document", projectId];
      const documentsKey = ["project-documents", projectId];

      queryClient.invalidateQueries({ queryKey: documentKey });
      queryClient.invalidateQueries({ queryKey: documentsKey });
    },
  });

  const handleEditorChange = (value?: string) => {
    const nextValue = value ?? "";
    setEditorValue(nextValue);
    setIsDirty(nextValue !== originalValueRef.current);
    setValidationError(null);

    if (!nextValue.trim()) {
      setParseError("Document content cannot be empty");
      return;
    }

    try {
      JSON.parse(nextValue);
      setParseError(null);
    } catch {
      setParseError("Invalid JSON syntax");
    }
  };

  const handleSave = () => {
    if (!documentId || parseError || !isDirty || mutation.isPending) {
      return;
    }

    mutation.mutate(editorValue);
  };

  if (!documentId || !document) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Document Editor</CardTitle>
          <CardDescription>
            Load a project document to edit its JSON representation.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            No document is currently available for editing.
          </p>
        </CardContent>
      </Card>
    );
  }

  const disableSave =
    !isDirty || !!parseError || mutation.isPending || !editorValue.trim();

  return (
    <Card>
      <CardHeader className="flex flex-col gap-2 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <CardTitle>Document JSON</CardTitle>
          <CardDescription>
            Edit the raw ODL-SD document and apply changes to the project.
          </CardDescription>
        </div>
        <div className="flex gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => {
              setEditorValue(originalValueRef.current);
              setIsDirty(false);
              setParseError(null);
              setValidationError(null);
            }}
            disabled={mutation.isPending || (!isDirty && !parseError)}
          >
            Reset
          </Button>
          <Button
            type="button"
            size="sm"
            onClick={handleSave}
            disabled={disableSave}
          >
            {mutation.isPending ? "Saving..." : "Save"}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {(parseError || validationError) && (
          <div
            role="alert"
            className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700"
          >
            {parseError || validationError}
          </div>
        )}
        <div className="border border-border rounded-md overflow-hidden">
          <Editor
            data-testid="document-json-editor"
            height="480px"
            language="json"
            value={editorValue}
            theme="vs-dark"
            onChange={handleEditorChange}
            options={{
              minimap: { enabled: false },
              scrollBeyondLastLine: false,
              tabSize: 2,
              automaticLayout: true,
            }}
          />
        </div>
      </CardContent>
    </Card>
  );
}

export default DocumentTab;
