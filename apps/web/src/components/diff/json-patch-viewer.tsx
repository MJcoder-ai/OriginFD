"use client";

import * as React from "react";
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Textarea,
} from "@originfd/ui";
import {
  computeJsonPatch,
  groupDiffsBySection,
  getValueByPath,
  type PatchOperation,
} from "./utils";

interface JsonPatchViewerProps {
  original: Record<string, any>;
  updated: Record<string, any>;
  onApprove?: (args: { patch: PatchOperation[]; rationale: string }) => void;
  onReject?: (args: { patch: PatchOperation[]; rationale: string }) => void;
}

export default function JsonPatchViewer({
  original,
  updated,
  onApprove,
  onReject,
}: JsonPatchViewerProps) {
  const patch = React.useMemo(
    () => computeJsonPatch(original, updated),
    [original, updated],
  );
  const sections = React.useMemo(() => groupDiffsBySection(patch), [patch]);
  const [rationale, setRationale] = React.useState("");

  const copyPatch = () => {
    navigator.clipboard.writeText(JSON.stringify(patch, null, 2));
  };

  const approve = () => onApprove?.({ patch, rationale });
  const reject = () => onReject?.({ patch, rationale });

  return (
    <div>
      <div className="flex flex-col gap-2 mb-4 md:flex-row">
        <Textarea
          placeholder="Rationale"
          value={rationale}
          onChange={(e) => setRationale(e.target.value)}
          className="flex-1"
        />
        <div className="flex gap-2">
          <Button variant="secondary" onClick={copyPatch}>
            Copy Patch
          </Button>
          <Button onClick={approve}>Approve</Button>
          <Button variant="destructive" onClick={reject}>
            Reject
          </Button>
        </div>
      </div>
      {Object.entries(sections).map(([section, ops]) => (
        <Card key={section} className="mb-4">
          <CardHeader>
            <CardTitle>{section}</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {ops.map((op, idx) => {
                const oldVal = getValueByPath(original, op.path);
                const newVal = op.value;
                const isNumeric =
                  typeof oldVal === "number" && typeof newVal === "number";
                const delta = isNumeric ? newVal - oldVal : null;
                return (
                  <li key={idx} className="flex items-center gap-2">
                    <span className="text-sm flex-1">
                      {op.path.split("/").slice(2).join("/")}
                    </span>
                    <Badge variant="outline">{String(oldVal)}</Badge>
                    <span>→</span>
                    <Badge
                      variant={
                        delta !== null
                          ? delta >= 0
                            ? "default"
                            : "destructive"
                          : "default"
                      }
                    >
                      {String(newVal)}
                      {delta !== null && (
                        <span className="ml-1 text-xs">
                          ({delta >= 0 ? "+" : ""}
                          {delta})
                        </span>
                      )}
                    </Badge>
                  </li>
                );
              })}
            </ul>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
