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
import type { DocumentResponse, OdlDocument } from '@/lib/types'
import { DocumentViewer, SystemDiagram } from '@/components/odl-sd'

export default function ProjectDetailPage() {
  const params = useParams()
  const router = useRouter()
  const { user } = useAuth()
  const projectId = params.id as string

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

  // Fetch project document
  const {
    data: document,
    isLoading: isDocumentLoading,
    error: documentError,
  } = useQuery({
    queryKey: ['document', projectId],
    queryFn: () => apiClient.getDocument(projectId),
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
    return (
      <div className="flex flex-col items-center justify-center h-96 space-y-4">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900">Project Not Found</h2>
          <p className="text-gray-600 mt-2">
            The project you're looking for doesn't exist or you don't have access to it.
          </p>
        </div>
        <Button onClick={() => router.push('/dashboard')} variant="outline">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Dashboard
        </Button>
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
          {document ? (
            <DocumentViewer document={document} projectId={projectId} />
          ) : (
            <Card>
              <CardHeader>
                <CardTitle>Project Documents</CardTitle>
                <CardDescription>
                  ODL-SD documents and related files for this project
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-center py-12">
                  <FileText className="mx-auto h-12 w-12 text-muted-foreground" />
                  <h3 className="mt-2 text-sm font-semibold text-gray-900">No documents</h3>
                  <p className="mt-1 text-sm text-muted-foreground">
                    No ODL-SD document found for this project.
                  </p>
                </div>
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
    </div>
  )
}
