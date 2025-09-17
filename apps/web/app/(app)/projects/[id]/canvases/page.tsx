"use client";

import * as React from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  Plus,
  Search,
  Filter,
  Grid3x3,
  Eye,
  MoreHorizontal,
  Layers,
  Map,
} from "lucide-react";
import { apiClient } from "@/lib/api-client";
import {
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  LoadingSpinner,
} from "@originfd/ui";

export default function ProjectCanvasesPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id as string;

  // Fetch project details
  const { data: project, isLoading: projectLoading } = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => apiClient.getProject(projectId),
  });

  // Real canvas data based on existing implementation
  const canvases = [
    {
      id: "sld-mv",
      name: "Medium Voltage SLD",
      description:
        "Medium voltage single-line diagram with protection and control",
      lastModified: "2024-01-20T15:45:00Z",
      status: "Active",
      type: "Single Line Diagram",
      icon: Layers,
    },
    {
      id: "sld-lv",
      name: "Low Voltage SLD",
      description: "Low voltage distribution and load connections",
      lastModified: "2024-01-19T10:30:00Z",
      status: "Active",
      type: "Single Line Diagram",
      icon: Layers,
    },
    {
      id: "site-layout",
      name: "Site Layout Plan",
      description: "Overall site layout with equipment positioning and routing",
      lastModified: "2024-01-18T14:20:00Z",
      status: "Active",
      type: "Site Plan",
      icon: Map,
    },
  ];

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "Active":
        return "bg-green-100 text-green-800 border-green-200";
      case "Draft":
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  if (projectLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Canvases</h1>
          <p className="text-muted-foreground">
            Design and layout canvases for {project?.project_name}
          </p>
        </div>
        <Button className="gap-2">
          <Plus className="h-4 w-4" />
          New Canvas
        </Button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-2">
        <Button variant="outline" size="sm">
          <Search className="h-4 w-4 mr-2" />
          Search
        </Button>
        <Button variant="outline" size="sm">
          <Filter className="h-4 w-4 mr-2" />
          Filter
        </Button>
      </div>

      {/* Canvases Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {canvases.map((canvas) => (
          <Card
            key={canvas.id}
            className="cursor-pointer hover:shadow-md transition-shadow"
          >
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-3">
                  <div className="p-2 rounded-lg bg-muted">
                    <Grid3x3 className="h-5 w-5 text-blue-600" />
                  </div>
                  <div className="flex-1">
                    <CardTitle className="text-lg">{canvas.name}</CardTitle>
                    <div className="flex items-center gap-2 mt-1">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${getStatusColor(canvas.status)}`}
                      >
                        {canvas.status}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {canvas.type}
                      </span>
                    </div>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    // Handle menu actions
                  }}
                >
                  <MoreHorizontal className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <p className="text-sm text-muted-foreground">
                  {canvas.description}
                </p>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Last modified</span>
                  <span>{formatDate(canvas.lastModified)}</span>
                </div>
                <div className="flex gap-2 pt-2">
                  <Button
                    size="sm"
                    variant="outline"
                    className="flex-1"
                    onClick={() =>
                      router.push(
                        `/projects/${projectId}/canvases/${canvas.id}`,
                      )
                    }
                  >
                    <Eye className="h-3 w-3 mr-1" />
                    Open Canvas
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Empty state if no canvases */}
      {canvases.length === 0 && (
        <div className="text-center py-12">
          <div className="max-w-md mx-auto">
            <div className="text-muted-foreground mb-4">
              <Grid3x3 className="h-12 w-12 mx-auto" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              No canvases yet
            </h3>
            <p className="text-muted-foreground mb-4">
              Create your first canvas to start designing your system layout.
            </p>
            <Button className="gap-2">
              <Plus className="h-4 w-4" />
              Create Canvas
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
