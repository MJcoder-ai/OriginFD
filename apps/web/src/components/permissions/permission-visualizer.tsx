"use client";

import React from "react";
import { Card, CardHeader, CardTitle, CardContent, Badge } from "@originfd/ui";
import { Check, X } from "lucide-react";

// Sample data structures representing the entity tree and permissions
interface PermissionNode {
  id: string;
  name: string;
  type: "project" | "document" | "node";
  children?: PermissionNode[];
}

interface RightDetail {
  allowed: boolean;
  source: string; // e.g. role/group/system
}

const entityTree: PermissionNode[] = [
  {
    id: "project-1",
    name: "Project Alpha",
    type: "project",
    children: [
      {
        id: "doc-1",
        name: "Design Document",
        type: "document",
        children: [
          { id: "node-1", name: "Node A", type: "node" },
          { id: "node-2", name: "Node B", type: "node" },
        ],
      },
    ],
  },
];

const rightsData: Record<string, Record<string, RightDetail>> = {
  "project-1": {
    create: { allowed: true, source: "role:admin" },
    read: { allowed: true, source: "role:viewer" },
    update: { allowed: false, source: "system" },
    delete: { allowed: false, source: "system" },
  },
  "doc-1": {
    create: { allowed: false, source: "group:editors" },
    read: { allowed: true, source: "group:readers" },
    update: { allowed: true, source: "group:editors" },
    delete: { allowed: false, source: "system" },
  },
  "node-1": {
    create: { allowed: false, source: "system" },
    read: { allowed: true, source: "role:viewer" },
    update: { allowed: false, source: "role:viewer" },
    delete: { allowed: false, source: "system" },
  },
  "node-2": {
    create: { allowed: true, source: "role:engineer" },
    read: { allowed: true, source: "role:engineer" },
    update: { allowed: true, source: "role:engineer" },
    delete: { allowed: false, source: "system" },
  },
};

const phaseLocks = [
  {
    phase: "Draft",
    locked: false,
    explanation: "Content can be edited freely.",
  },
  {
    phase: "Review",
    locked: true,
    explanation: "Edits require reviewer approval and are temporarily locked.",
  },
  {
    phase: "Approved",
    locked: true,
    explanation:
      "The item is locked after approval and cannot be changed without reverting.",
  },
];

const approverMatrix = [
  { phase: "Review", approvers: ["Alice", "Bob"] },
  { phase: "Approved", approvers: ["Project Manager"] },
];

function Tree({
  nodes,
  selectedId,
  onSelect,
}: {
  nodes: PermissionNode[];
  selectedId: string;
  onSelect: (id: string) => void;
}) {
  return (
    <ul className="ml-4 list-disc">
      {nodes.map((node) => (
        <li key={node.id}>
          <button
            className={`text-left hover:underline ${selectedId === node.id ? "font-semibold" : ""}`}
            onClick={() => onSelect(node.id)}
          >
            {node.name}
          </button>
          {node.children && node.children.length > 0 && (
            <Tree
              nodes={node.children}
              selectedId={selectedId}
              onSelect={onSelect}
            />
          )}
        </li>
      ))}
    </ul>
  );
}

export function PermissionVisualizer() {
  const [selectedId, setSelectedId] = React.useState("project-1");

  const rights = rightsData[selectedId] || {};

  return (
    <div className="grid gap-6 md:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Entity Tree</CardTitle>
        </CardHeader>
        <CardContent>
          <Tree
            nodes={entityTree}
            selectedId={selectedId}
            onSelect={setSelectedId}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Rights for Selected Node</CardTitle>
        </CardHeader>
        <CardContent>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left">
                <th className="py-1">Operation</th>
                <th className="py-1">Access</th>
                <th className="py-1">Source</th>
              </tr>
            </thead>
            <tbody>
              {["create", "read", "update", "delete"].map((op) => (
                <tr key={op} className="border-t">
                  <td className="py-1 capitalize">{op}</td>
                  <td className="py-1">
                    {rights[op]?.allowed ? (
                      <Check className="h-4 w-4 text-green-600" />
                    ) : (
                      <X className="h-4 w-4 text-red-600" />
                    )}
                  </td>
                  <td className="py-1 text-muted-foreground">
                    {rights[op]?.source || "-"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Inheritance Trail</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="text-sm space-y-1">
            {["create", "read", "update", "delete"].map((op) => (
              <li key={op} className="flex items-center gap-2">
                <span className="w-20 capitalize">{op}:</span>
                <Badge
                  variant={rights[op]?.allowed ? "default" : "destructive"}
                >
                  {rights[op]?.source || "unknown"}
                </Badge>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      <Card className="md:col-span-2">
        <CardHeader>
          <CardTitle>Phase Locks & Approvals</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div>
            <h4 className="font-medium mb-2">Phase Locks</h4>
            <ul className="space-y-2 text-sm">
              {phaseLocks.map((p) => (
                <li key={p.phase} className="flex items-start gap-2">
                  {p.locked ? (
                    <X className="h-4 w-4 text-red-600 mt-0.5" />
                  ) : (
                    <Check className="h-4 w-4 text-green-600 mt-0.5" />
                  )}
                  <div>
                    <span className="font-medium">{p.phase}</span> –{" "}
                    {p.explanation}
                  </div>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h4 className="font-medium mb-2">Approver Matrix</h4>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left">
                  <th className="py-1">Phase</th>
                  <th className="py-1">Required Approvers</th>
                </tr>
              </thead>
              <tbody>
                {approverMatrix.map((row) => (
                  <tr key={row.phase} className="border-t">
                    <td className="py-1">{row.phase}</td>
                    <td className="py-1">{row.approvers.join(", ")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default PermissionVisualizer;
