'use client'

import * as React from 'react'
import { useQuery } from '@tanstack/react-query'
import { useParams, useRouter } from 'next/navigation'
import { 
  ArrowLeft, 
  Settings, 
  FileText, 
  Activity, 
  Users, 
  Calendar,
  MapPin,
  Zap,
  Battery,
  Sun,
  Grid3x3,
  Edit,
  MoreHorizontal
} from 'lucide-react'

import { 
  Button, 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger
} from '@originfd/ui'
import { apiClient } from '@/lib/api-client'
import { useAuth } from '@/lib/auth/auth-provider'
import { ComponentSelector } from '@/components/components/component-selector'
import type { DocumentResponse, OdlDocument } from '@/lib/types'
import { DocumentViewer, SystemDiagram } from '@/components/odl-sd'

export default function ProjectDetailPage() {
  const params = useParams()
  const router = useRouter()
  const { user } = useAuth()
  const projectId = params.id as string
  const [componentSelectorOpen, setComponentSelectorOpen] = React.useState(false)

  // Fetch project metadata
  const {
    data: project,
    isLoading: isProjectLoading,
    error: projectError,
  } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => apiClient.getProject(projectId),
    enabled: !!projectId,
  })

  // Fetch project document (primary document for the project)
  const {
    data: document,
    isLoading: isDocumentLoading,
    error: documentError,
  } = useQuery({
    queryKey: ['project-document', projectId],
    queryFn: () => apiClient.getPrimaryProjectDocument(projectId),
    enabled: !!projectId,
  })

  // Fetch all project documents for the documents tab
  const {
    data: projectDocuments = [],
    isLoading: isProjectDocumentsLoading,
    error: projectDocumentsError,
  } = useQuery({
    queryKey: ['project-documents', projectId],
    queryFn: () => apiClient.getProjectDocuments(projectId),
    enabled: !!projectId,
  })

  const getDomainIcon = (domain: string) => {
    switch (domain) {
      case 'PV':
        return <Sun className="h-5 w-5 text-yellow-600" />
      case 'BESS':
        return <Battery className="h-5 w-5 text-green-600" />
      case 'HYBRID':
        return <Zap className="h-5 w-5 text-purple-600" />
      case 'GRID':
      case 'MICROGRID':
        return <Grid3x3 className="h-5 w-5 text-blue-600" />
      default:
        return <Grid3x3 className="h-5 w-5 text-gray-600" />
    }
  }

  const getDomainColor = (domain: string) => {
    switch (domain) {
      case 'PV':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'BESS':
        return 'bg-green-100 text-green-800 border-green-200'
      case 'HYBRID':
        return 'bg-purple-100 text-purple-800 border-purple-200'
      case 'GRID':
      case 'MICROGRID':
        return 'bg-blue-100 text-blue-800 border-blue-200'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const getScaleBadgeColor = (scale: string) => {
    switch (scale) {
      case 'UTILITY':
      case 'HYPERSCALE':
        return 'bg-red-100 text-red-800 border-red-200'
      case 'INDUSTRIAL':
        return 'bg-orange-100 text-orange-800 border-orange-200'
      case 'COMMERCIAL':
        return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'RESIDENTIAL':
        return 'bg-green-100 text-green-800 border-green-200'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  if (isProjectLoading || isDocumentLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  if (projectError || documentError) {
    // Helper function to get error status
    const getErrorStatus = (error: any) => {
      return error?.status || error?.response?.status || 500
    }

    // Helper function to check if error is forbidden (403)
    const isForbidden = (error: any) => getErrorStatus(error) === 403
    
    // Helper function to check if error is not found (404)
    const isNotFound = (error: any) => getErrorStatus(error) === 404

    // Determine error type for better user messaging
    let title = "Error Loading Project"
    let message = "An unexpected error occurred."
    
    const projectStatus = projectError ? getErrorStatus(projectError) : null
    const documentStatus = documentError ? getErrorStatus(documentError) : null
    
    if (projectError && documentError) {
      if (isForbidden(projectError) || isForbidden(documentError)) {
        title = "Access Denied"
        message = "You don't have permission to access this project or its documents. Please contact your administrator."
      } else if (isNotFound(projectError) && isNotFound(documentError)) {
        title = "Project and Document Not Found"
        message = "The project and its associated document could not be found."
      } else {
        title = "Project and Document Error"
        message = "There was an issue loading both the project and its document."
      }
    } else if (projectError) {
      if (isForbidden(projectError)) {
        title = "Project Access Denied"
        message = "You don't have permission to view this project. Please contact your administrator."
      } else if (isNotFound(projectError)) {
        title = "Project Not Found"
        message = "The project you're looking for doesn't exist or has been deleted."
      } else {
        title = "Project Loading Error"
        message = "There was an issue loading this project. Please try again."
      }
    } else if (documentError) {
      if (isForbidden(documentError)) {
        title = "Document Access Denied"
        message = "You don't have permission to view this project's document."
      } else if (isNotFound(documentError)) {
        title = "Project Document Missing"
        message = "The project exists but its document could not be found. The document may not have been created yet."
      } else {
        title = "Document Loading Error"
        message = "There was an issue loading the project document. You can still view project information."
      }
    }
    
    // Log errors for debugging
    if (projectError) {
      console.error('Project loading error:', projectError, 'Status:', projectStatus)
    }
    if (documentError) {
      console.error('Document loading error:', documentError, 'Status:', documentStatus)
    }
    
    return (
      <div className="flex flex-col items-center justify-center h-96 space-y-4">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900">{title}</h2>
          <p className="text-gray-600 mt-2">{message}</p>
          {documentError && !projectError && (
            <p className="text-sm text-muted-foreground mt-2">
              You can still view project information, but document features will be unavailable.
            </p>
          )}
        </div>
        <div className="flex gap-2">
          <Button onClick={() => router.push('/dashboard')} variant="outline">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Dashboard
          </Button>
          {documentError && !projectError && (
            <Button onClick={() => window.location.reload()} variant="default">
              Retry Loading
            </Button>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="space-y-4">
          {/* Breadcrumb */}
          <div className="flex items-center space-x-2 text-sm text-muted-foreground">
            <button 
              onClick={() => router.push('/dashboard')}
              className="hover:text-foreground transition-colors"
            >
              Dashboard
            </button>
            <span>/</span>
            <button 
              onClick={() => router.push('/projects')}
              className="hover:text-foreground transition-colors"
            >
              Projects
            </button>
            <span>/</span>
            <span className="text-foreground">{project?.project_name || document?.meta?.project}</span>
          </div>

          {/* Project Title */}
          <div className="flex items-center space-x-4">
            <div className="p-2 rounded-lg bg-muted">
              {getDomainIcon(project?.domain || document?.meta?.domain || 'GRID')}
            </div>
            <div>
              <h1 className="text-3xl font-bold tracking-tight">
                {project?.project_name || document?.meta?.project}
              </h1>
              <div className="flex items-center gap-2 mt-2">
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getDomainColor(project?.domain || document?.meta?.domain || 'GRID')}`}>
                  {project?.domain || document?.meta?.domain}
                </span>
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getScaleBadgeColor(project?.scale || document?.meta?.scale || 'COMMERCIAL')}`}>
                  {project?.scale || document?.meta?.scale}
                </span>
                <span className="text-sm text-muted-foreground">
                  v{project?.current_version || document?.meta?.versioning?.document_version}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm">
            <Edit className="mr-2 h-4 w-4" />
            Edit
          </Button>
          <Button variant="outline" size="sm">
            <MoreHorizontal className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Project Tabs */}
      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList>
          <TabsTrigger value="overview" className="flex items-center gap-2">
            <Activity className="h-4 w-4" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="documents" className="flex items-center gap-2">
            <FileText className="h-4 w-4" />
            Documents
          </TabsTrigger>
          <TabsTrigger value="components" className="flex items-center gap-2">
            <Grid3x3 className="h-4 w-4" />
            Components
          </TabsTrigger>
          <TabsTrigger value="team" className="flex items-center gap-2">
            <Users className="h-4 w-4" />
            Team
          </TabsTrigger>
          <TabsTrigger value="settings" className="flex items-center gap-2">
            <Settings className="h-4 w-4" />
            Settings
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* System Architecture Diagram */}
          {document && document.instances && document.instances.length > 0 && (
            <SystemDiagram 
              instances={document.instances}
              connections={document.connections || []}
              className="mb-6"
            />
          )}
          
          {/* Project Overview */}
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {/* Project Info */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MapPin className="h-5 w-5" />
                  Project Details
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Location</p>
                  <p className="text-sm">{document?.hierarchy?.portfolio?.location || 'Not specified'}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Description</p>
                  <p className="text-sm">{document?.hierarchy?.portfolio?.description || 'No description available'}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Created</p>
                  <p className="text-sm">
                    {document?.meta?.timestamps?.created_at 
                      ? new Date(document.meta.timestamps.created_at).toLocaleDateString()
                      : project?.created_at 
                        ? new Date(project.created_at).toLocaleDateString()
                        : 'Unknown'
                    }
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* System Requirements */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Zap className="h-5 w-5" />
                  System Requirements
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Capacity</p>
                  <p className="text-sm">
                    {document?.requirements?.functional?.capacity_kw 
                      ? document.requirements.functional.capacity_kw >= 1000
                        ? `${(document.requirements.functional.capacity_kw / 1000).toFixed(1)} MW`
                        : `${document.requirements.functional.capacity_kw.toFixed(0)} kW`
                      : 'TBD'
                    }
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Annual Generation</p>
                  <p className="text-sm">
                    {document?.requirements?.functional?.annual_generation_kwh 
                      ? `${(document.requirements.functional.annual_generation_kwh / 1000).toFixed(0)} MWh`
                      : 'TBD'
                    }
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Grid Connection</p>
                  <p className="text-sm">
                    {document?.requirements?.technical?.grid_connection ? 'Yes' : 'No'}
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Recent Activity */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Calendar className="h-5 w-5" />
                  Recent Activity
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <p className="text-sm text-muted-foreground">No recent activity</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="documents" className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold">Project Documents</h3>
              <p className="text-sm text-muted-foreground">
                ODL-SD documents and related files for this project
              </p>
            </div>
            <Button variant="outline" size="sm">
              <FileText className="h-4 w-4 mr-2" />
              New Document
            </Button>
          </div>

          {isProjectDocumentsLoading ? (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : projectDocuments.length > 0 ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {projectDocuments.map((doc: any) => (
                <Card key={doc.id} className="cursor-pointer hover:shadow-md transition-shadow">
                  <CardHeader className="pb-3">
                    <div className="flex items-center space-x-2">
                      <div className="p-2 rounded-lg bg-muted">
                        <FileText className="h-4 w-4" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <CardTitle className="text-sm font-medium truncate">
                          {doc.name}
                        </CardTitle>
                        <CardDescription className="text-xs">
                          {doc.document_type} • {doc.is_primary ? 'Primary' : 'Secondary'}
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
                        <span className="text-muted-foreground">ID</span>
                        <span className="truncate font-mono text-xs">{doc.id.split('-').pop()}</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <FileText className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">No Documents</h3>
                <p className="text-sm text-muted-foreground text-center mb-4">
                  No ODL-SD documents found for this project. Create your first document to get started.
                </p>
                <Button variant="outline">
                  <FileText className="h-4 w-4 mr-2" />
                  Create First Document
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Primary Document Viewer - if available */}
          {document && (
            <Card>
              <CardHeader>
                <CardTitle>Primary System Document</CardTitle>
                <CardDescription>
                  Main ODL-SD document with full system specification
                </CardDescription>
              </CardHeader>
              <CardContent>
                <DocumentViewer document={document} projectId={projectId} />
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="components" className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold">Project Components</h3>
              <p className="text-sm text-muted-foreground">
                Manage components used in this project
              </p>
            </div>
            <Button onClick={() => setComponentSelectorOpen(true)}>
              <Grid3x3 className="h-4 w-4 mr-2" />
              Add Components
            </Button>
          </div>

          {/* Components Library from Document */}
          {document?.libraries?.components && document.libraries.components.length > 0 ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {document.libraries.components.map((component: any, index: number) => (
                <Card key={index}>
                  <CardHeader className="pb-3">
                    <div className="flex items-center space-x-2">
                      <div className="p-2 rounded-lg bg-muted">
                        <Grid3x3 className="h-4 w-4" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <CardTitle className="text-sm font-medium truncate">
                          {component.brand} {component.part_number}
                        </CardTitle>
                        <CardDescription className="text-xs">
                          {component.rating_w}W • {component.category}
                        </CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="pt-0">
                    <div className="space-y-2">
                      {component.quantity && (
                        <div className="flex justify-between text-xs">
                          <span className="text-muted-foreground">Quantity</span>
                          <span>{component.quantity}</span>
                        </div>
                      )}
                      {component.placement?.location && (
                        <div className="flex justify-between text-xs">
                          <span className="text-muted-foreground">Location</span>
                          <span className="truncate">{component.placement.location}</span>
                        </div>
                      )}
                      {component.status && (
                        <div className="flex justify-between text-xs">
                          <span className="text-muted-foreground">Status</span>
                          <span className="capitalize">{component.status}</span>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Grid3x3 className="h-12 w-12 text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">No Components Added</h3>
                <p className="text-sm text-muted-foreground text-center mb-4">
                  Start building your project by adding components from the library
                </p>
                <Button onClick={() => setComponentSelectorOpen(true)}>
                  <Grid3x3 className="h-4 w-4 mr-2" />
                  Add Your First Component
                </Button>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="team" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Project Team</CardTitle>
              <CardDescription>
                Manage team members and their access permissions
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-12">
                <Users className="mx-auto h-12 w-12 text-muted-foreground" />
                <h3 className="mt-2 text-sm font-semibold text-gray-900">No team members</h3>
                <p className="mt-1 text-sm text-muted-foreground">
                  Team management features are coming soon.
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="settings" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Project Settings</CardTitle>
              <CardDescription>
                Configure project preferences and permissions
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-12">
                <Settings className="mx-auto h-12 w-12 text-muted-foreground" />
                <h3 className="mt-2 text-sm font-semibold text-gray-900">Settings</h3>
                <p className="mt-1 text-sm text-muted-foreground">
                  Project settings are coming soon.
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Component Selector Modal */}
      <ComponentSelector
        open={componentSelectorOpen}
        onOpenChange={setComponentSelectorOpen}
        onComponentsSelected={async (selectedComponents) => {
          try {
            // TODO: Implement API call to add components to project
            console.log('Adding components to project:', selectedComponents)
            
            // For now, just show success message
            // In real implementation, this would call the component integration API
            // await componentIntegrationAPI.addComponentsToProject({
            //   project_document_id: projectId,
            //   components: selectedComponents.map(sc => ({
            //     component_id: sc.component.id,
            //     quantity: sc.quantity,
            //     placement: sc.placement,
            //     configuration: sc.configuration,
            //     notes: sc.notes
            //   }))
            // })
            
            // Refetch project data to show updated components
            // refetch()
            
          } catch (error) {
            console.error('Failed to add components:', error)
          }
        }}
        projectDomain={project?.domain}
        projectScale={project?.scale}
        title="Add Components to Project"
        description={`Select components to add to ${project?.project_name || 'this project'}`}
      />
    </div>
  )
}
