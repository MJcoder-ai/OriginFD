"use client";

import * as React from "react";
import { useParams } from "next/navigation";
import { useQuery, useMutation } from "@tanstack/react-query";
import {
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Input,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@originfd/ui";
import { componentAPI } from "@/lib/api-client";
import { AICopilotService } from "@/components/ai/ai-copilot";

export default function ComponentWorkbenchPage() {
  const params = useParams();
  const componentId = params.id as string;
  const [parsedAttrs, setParsedAttrs] = React.useState<Record<string, string>>(
    {},
  );
  const [aiSummary, setAiSummary] = React.useState("");

  const { data: component } = useQuery({
    queryKey: ["component", componentId],
    queryFn: () => componentAPI.getComponent(componentId),
    enabled: !!componentId,
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => componentAPI.parseDatasheet(file),
    onSuccess: (data) => {
      setParsedAttrs(data.attributes || {});
    },
  });

  const analyzeMutation = useMutation({
    mutationFn: async () => {
      const service = new AICopilotService();
      const response = await service.sendMessage(
        `Compare existing component ${JSON.stringify(component)} with new attributes ${JSON.stringify(parsedAttrs)} and summarize differences`,
      );
      return response.content;
    },
    onSuccess: (content) => setAiSummary(content),
  });

  const proposeMutation = useMutation({
    mutationFn: () =>
      componentAPI.updateComponent(componentId, {
        classification: parsedAttrs,
      }),
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      uploadMutation.mutate(file);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Component Workbench</h1>

      <div className="space-y-4">
        <Input type="file" onChange={handleFileChange} />
        {Object.keys(parsedAttrs).length > 0 && (
          <Button
            variant="secondary"
            onClick={() => analyzeMutation.mutate()}
            disabled={analyzeMutation.isPending}
          >
            Analyze with Copilot
          </Button>
        )}
      </div>

      {aiSummary && (
        <Card>
          <CardHeader>
            <CardTitle>Copilot Analysis</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="whitespace-pre-wrap text-sm">{aiSummary}</p>
          </CardContent>
        </Card>
      )}

      {component && Object.keys(parsedAttrs).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Comparison</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Attribute</TableHead>
                  <TableHead>Current</TableHead>
                  <TableHead>Parsed</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {Object.entries(parsedAttrs).map(([key, value]) => (
                  <TableRow key={key}>
                    <TableCell className="font-medium">{key}</TableCell>
                    <TableCell>{(component as any)[key] ?? "-"}</TableCell>
                    <TableCell>{value}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            <Button
              className="mt-4"
              onClick={() => proposeMutation.mutate()}
              disabled={proposeMutation.isPending}
            >
              Propose Change
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
