"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient, ModelInfo } from "@/lib/api-client";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  Badge,
} from "@originfd/ui";

export default function ModelRegistryPage() {
  const { data: models = [], error } = useQuery<ModelInfo[]>({
    queryKey: ["model-registry"],
    queryFn: () => apiClient.listModels(),
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Model Registry</h1>
      {error && <p className="text-sm text-red-600">Failed to load models</p>}
      <Card>
        <CardHeader>
          <CardTitle>Registered Models</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Provider</TableHead>
                <TableHead>Region</TableHead>
                <TableHead>Cost/1k tokens</TableHead>
                <TableHead>Latency (ms)</TableHead>
                <TableHead>Eval Score</TableHead>
                <TableHead>Routing Rules</TableHead>
                <TableHead>CAG Hit%</TableHead>
                <TableHead>CAG Drift</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {models.map((m) => (
                <TableRow key={m.id}>
                  <TableCell className="font-medium">{m.name}</TableCell>
                  <TableCell>{m.provider}</TableCell>
                  <TableCell>{m.region}</TableCell>
                  <TableCell>{m.cost_per_1k_tokens.toFixed(2)}</TableCell>
                  <TableCell>{m.latency_ms}</TableCell>
                  <TableCell>{m.eval_score.toFixed(2)}</TableCell>
                  <TableCell>
                    {Object.keys(m.routing_rules || {}).length}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant={m.cag_hit_rate > 0.8 ? "default" : "secondary"}
                    >
                      {(m.cag_hit_rate * 100).toFixed(1)}%
                    </Badge>
                  </TableCell>
                  <TableCell>{m.cag_drift.toFixed(2)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
