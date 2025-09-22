"use client";

import * as React from "react";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  Plus,
  Search,
  Filter,
  FileText,
  Download,
  MoreHorizontal,
  Eye,
} from "lucide-react";
import { apiClient } from "@/lib/api-client";
import {
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@originfd/ui";
import { DocumentViewer, DocumentVersionTimeline } from "@/components/odl-sd";

export default function ProjectDocumentsPage() {
  const params = useParams();
  const projectId = params.id as string;

  // Fetch project details
  const { data: project, isLoading: projectLoading } = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => apiClient.getProject(projectId),
  });

  // Fetch project documents from API
  const { data: projectDocuments = [], isLoading: isProjectDocumentsLoading } =
    useQuery({
      queryKey: ["project-documents", projectId],
      queryFn: () => apiClient.getProjectDocuments(projectId),
      enabled: !!projectId,
    });

  // Fetch primary document for viewer
  const { data: primaryDocument, isLoading: isPrimaryDocLoading } = useQuery({
    queryKey: ["project-document", projectId],
    queryFn: () => apiClient.getPrimaryProjectDocument(projectId),
    enabled: !!projectId,
  });

  const primaryDocumentId = React.useMemo(() => {
    const projectDoc = projectDocuments.find((doc: any) => doc.is_primary);
    if (projectDoc?.id) {
      return projectDoc.id as string;
    }
    if (projectId) {
      return `${projectId}-main`;
    }
    return undefined;
  }, [projectDocuments, projectId]);

  // Mock documents data for now
  const documents = [
    {
      id: "doc-1",
      name: "System Specifications",
      description: "Technical specifications and requirements document",
      type: "PDF",
      size: "3.2 MB",
      lastModified: "2024-01-20T15:45:00Z",
      status: "Final",
      category: "Technical",
      version: "1.2",
    },
    {
      id: "doc-2",
      name: "Installation Manual",
      description: "Step-by-step installation procedures and guidelines",
      type: "PDF",
      size: "8.7 MB",
      lastModified: "2024-01-19T10:30:00Z",
      status: "Draft",
      category: "Operational",
      version: "0.9",
    },
    {
      id: "doc-3",
      name: "Safety Compliance Report",
      description: "Safety analysis and regulatory compliance documentation",
      type: "DOCX",
      size: "1.5 MB",
      lastModified: "2024-01-18T14:20:00Z",
      status: "Final",
      category: "Compliance",
      version: "2.0",
    },
    {
      id: "doc-4",
      name: "Site Survey Results",
      description: "Detailed site assessment and environmental analysis",
      type: "PDF",
      size: "15.3 MB",
      lastModified: "2024-01-17T09:15:00Z",
      status: "Final",
      category: "Assessment",
      version: "1.0",
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
      case "Final":
        return "bg-green-100 text-green-800 border-green-200";
      case "Draft":
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
      case "Review":
        return "bg-blue-100 text-blue-800 border-blue-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case "Technical":
        return "bg-blue-100 text-blue-800 border-blue-200";
      case "Operational":
        return "bg-purple-100 text-purple-800 border-purple-200";
      case "Compliance":
        return "bg-red-100 text-red-800 border-red-200";
      case "Assessment":
        return "bg-orange-100 text-orange-800 border-orange-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const getFileTypeIcon = (type: string) => {
    return <FileText className="h-5 w-5 text-blue-600" />;
  };

  if (projectLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Documents</h1>
          <p className="text-muted-foreground">
            Project documentation and files for {project?.project_name}
          </p>
        </div>
        <Button className="gap-2">
          <Plus className="h-4 w-4" />
          Upload Document
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

      {/* Real Project Documents from API */}
      {isProjectDocumentsLoading ? (
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      ) : projectDocuments.length > 0 ? (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {projectDocuments.map((doc: any) => (
            <Card
              key={doc.id}
              className="cursor-pointer hover:shadow-md transition-shadow"
            >
              <CardHeader className="pb-3">
                <div className="flex items-center space-x-2">
                  <div className="p-2 rounded-lg bg-muted">
                    <FileText className="h-4 w-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <CardTitle className="text-sm font-medium truncate">
                      {doc.name || doc.project_name}
                    </CardTitle>
                    <CardDescription className="text-xs">
                      {doc.document_type || "ODL-SD"} •{" "}
                      {doc.is_primary ? "Primary" : "Secondary"}
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="pt-0">
                <div className="space-y-2">
                  <div className="flex justify-between text-xs">
                    <span className="text-muted-foreground">Created</span>
                    <span>{new Date(doc.created_at).toLocaleDateString()}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-muted-foreground">Updated</span>
                    <span>{new Date(doc.updated_at).toLocaleDateString()}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-muted-foreground">Version</span>
                    <span>v{doc.current_version}</span>
                  </div>
                  <div className="flex gap-2 pt-2">
                    <Button size="sm" variant="outline" className="flex-1">
                      <Eye className="h-3 w-3 mr-1" />
                      View
                    </Button>
                    <Button size="sm" variant="outline" className="flex-1">
                      <Download className="h-3 w-3 mr-1" />
                      Download
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {documents.map((document) => (
            <Card
              key={document.id}
              className="cursor-pointer hover:shadow-md transition-shadow"
            >
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 rounded-lg bg-muted">
                      {getFileTypeIcon(document.type)}
                    </div>
                    <div className="flex-1">
                      <CardTitle className="text-lg">{document.name}</CardTitle>
                      <div className="flex items-center gap-2 mt-1">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${getStatusColor(document.status)}`}
                        >
                          {document.status}
                        </span>
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${getCategoryColor(document.category)}`}
                        >
                          {document.category}
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
                    {document.description}
                  </p>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Version</span>
                    <span>v{document.version}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Size</span>
                    <span>{document.size}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Type</span>
                    <span>{document.type}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Last modified</span>
                    <span>{formatDate(document.lastModified)}</span>
                  </div>
                  <div className="flex gap-2 pt-2">
                    <Button size="sm" variant="outline" className="flex-1">
                      <Eye className="h-3 w-3 mr-1" />
                      View
                    </Button>
                    <Button size="sm" variant="outline" className="flex-1">
                      <Download className="h-3 w-3 mr-1" />
                      Download
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Empty state if no documents */}
      {documents.length === 0 && (
        <div className="text-center py-12">
          <div className="max-w-md mx-auto">
            <div className="text-muted-foreground mb-4">
              <FileText className="h-12 w-12 mx-auto" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              No documents yet
            </h3>
            <p className="text-muted-foreground mb-4">
              Upload your first document to start building your project
              documentation.
            </p>
            <Button className="gap-2">
              <Plus className="h-4 w-4" />
              Upload Document
            </Button>
          </div>
        </div>
      )}

      {/* Primary Document Viewer */}
      {primaryDocument && (
        <Card>
          <CardHeader>
            <CardTitle>Primary System Document</CardTitle>
            <CardDescription>
              Main ODL-SD document with full system specification
            </CardDescription>
          </CardHeader>
          <CardContent>
            <DocumentViewer document={primaryDocument} projectId={projectId} />
          </CardContent>
        </Card>
      )}

      {primaryDocumentId && (
        <Card>
          <CardHeader>
            <CardTitle>Version History &amp; Diffs</CardTitle>
            <CardDescription>
              Review previous revisions and compare document changes side by
              side.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <DocumentVersionTimeline documentId={primaryDocumentId} />
          </CardContent>
        </Card>
      )}
    </div>
  );
}
