"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@originfd/ui";

interface ToolMetadata {
  name: string;
  description: string;
  category: string;
}

interface ToolResult {
  success: boolean;
  outputs: Record<string, any>;
  execution_time_ms: number;
  errors: string[];
}

// Use environment variable for tools API base URL in production
const apiBase =
  typeof window !== "undefined"
    ? (window as any).__ORIGINFD_TOOLS_API_BASE__ ||
      "http://localhost:8001/tools"
    : process.env.NEXT_PUBLIC_TOOLS_API_BASE_URL ||
      "http://localhost:8001/tools";

async function fetchTools(): Promise<ToolMetadata[]> {
  const res = await fetch(apiBase);
  if (!res.ok) throw new Error("Failed to load tools");
  return res.json();
}

async function runSample(name: string): Promise<ToolResult> {
  const res = await fetch(`${apiBase}/${name}/sample`, { method: "POST" });
  if (!res.ok) throw new Error("Tool execution failed");
  return res.json();
}

export default function ToolRegistryPage() {
  const { data: tools } = useQuery({
    queryKey: ["tools"],
    queryFn: fetchTools,
  });
  const [results, setResults] = React.useState<Record<string, ToolResult>>({});

  const handleRun = async (name: string) => {
    const result = await runSample(name);
    setResults((prev) => ({ ...prev, [name]: result }));
  };

  return (
    <div className="space-y-4 p-4">
      <div className="flex gap-4">
        <a
          href={`${apiBase.replace("/tools", "")}/tools/sdk/typescript`}
          className="underline text-blue-600"
          target="_blank"
        >
          Download TypeScript SDK
        </a>
        <a
          href={`${apiBase.replace("/tools", "")}/tools/sdk/python`}
          className="underline text-blue-600"
          target="_blank"
        >
          Download Python SDK
        </a>
      </div>
      {tools?.map((tool) => (
        <Card key={tool.name} className="mb-4">
          <CardHeader>
            <CardTitle>{tool.name}</CardTitle>
            <CardDescription>{tool.description}</CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={() => handleRun(tool.name)}>Run Sample</Button>
            {results[tool.name] && (
              <pre className="mt-2 whitespace-pre-wrap text-sm bg-muted p-2 rounded">
                {JSON.stringify(results[tool.name], null, 2)}
              </pre>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
