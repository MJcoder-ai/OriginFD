'use client'

import * as React from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useParams, useRouter } from 'next/navigation'
import { 
  ArrowLeft, 
  Edit, 
  MoreHorizontal,
  Activity,
  FileText,
  Settings,
  History,
  Upload,
  Download,
  Eye,
  ExternalLink,
  Package,
  Zap
} from 'lucide-react'

import { 
  Button, 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle,
  Badge,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Separator
} from '@originfd/ui'
import { componentAPI } from '@/lib/api-client'
import type { ComponentResponse, ComponentStatus } from '@/lib/types'

const statusColors = {
  draft: 'bg-gray-100 text-gray-800',
  parsed: 'bg-blue-100 text-blue-800',
  enriched: 'bg-indigo-100 text-indigo-800',
  approved: 'bg-green-100 text-green-800',
  available: 'bg-emerald-100 text-emerald-800',
  operational: 'bg-teal-100 text-teal-800',
  archived: 'bg-red-100 text-red-800'
}

const statusTransitions = {
  draft: ['parsed'],
  parsed: ['enriched', 'draft'],
  enriched: ['approved', 'parsed'],
  approved: ['available'],
  available: ['operational'],
  operational: ['archived']
}

export default function ComponentDetailPage() {
  const params = useParams()
  const router = useRouter()
  const queryClient = useQueryClient()
  const componentId = params.id as string

  // Fetch component data
  const {
    data: component,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['component', componentId],
    queryFn: () => componentAPI.getComponent(componentId),
    enabled: !!componentId,
  })

  // Status transition mutation
  const transitionMutation = useMutation({
    mutationFn: ({ newStatus, comment }: { newStatus: string, comment?: string }) =>
      componentAPI.transitionStatus(componentId, newStatus, comment),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['component', componentId] })
    },
  })

  const getStatusColor = (status: ComponentStatus) => {
    return statusColors[status] || 'bg-gray-100 text-gray-800'
  }

  const getAvailableTransitions = (currentStatus: ComponentStatus) => {
    return statusTransitions[currentStatus] || []
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  if (error || !component) {
    return (
      <div className="flex flex-col items-center justify-center h-96 space-y-4">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900">Component Not Found</h2>
          <p className="text-gray-600 mt-2">
            The component you're looking for doesn't exist or you don't have access to it.
          </p>
        </div>
        <Button onClick={() => router.push('/components')} variant="outline">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Components
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
              onClick={() => router.push('/components')}
              className="hover:text-foreground transition-colors"
            >
              Components
            </button>
            <span>/</span>
            <span className="text-foreground">{component.brand} {component.part_number}</span>
          </div>

          {/* Component Title */}
          <div className="flex items-center space-x-4">
            <div className="p-3 rounded-lg bg-muted">
              <Package className="h-6 w-6" />
            </div>
            <div>
              <h1 className="text-3xl font-bold tracking-tight">
                {component.brand} {component.part_number}
              </h1>
              <div className="flex items-center gap-2 mt-2">
                <Badge variant="secondary" className={getStatusColor(component.status)}>
                  {component.status}
                </Badge>
                {component.category && (
                  <Badge variant="outline">
                    {component.category}
                  </Badge>
                )}
                {component.domain && (
                  <Badge variant="outline">
                    {component.domain}
                  </Badge>
                )}
                <span className="text-sm text-muted-foreground">
                  {component.rating_w}W
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

      {/* Component Details */}
      <div className="grid gap-6 md:grid-cols-3">
        <div className="md:col-span-2">
          <Tabs defaultValue="overview" className="space-y-6">
            <TabsList>
              <TabsTrigger value="overview" className="flex items-center gap-2">
                <Activity className="h-4 w-4" />
                Overview
              </TabsTrigger>
              <TabsTrigger value="specifications" className="flex items-center gap-2">
                <FileText className="h-4 w-4" />
                Specifications
              </TabsTrigger>
              <TabsTrigger value="documents" className="flex items-center gap-2">
                <FileText className="h-4 w-4" />
                Documents
              </TabsTrigger>
              <TabsTrigger value="history" className="flex items-center gap-2">
                <History className="h-4 w-4" />
                History
              </TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Component Information</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Component ID</p>
                      <p className="font-mono text-sm">{component.component_id}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Name</p>
                      <p className="font-mono text-sm">{component.name}</p>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Brand</p>
                      <p>{component.brand}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Part Number</p>
                      <p>{component.part_number}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Rating</p>
                      <p>{component.rating_w}W</p>
                    </div>
                  </div>

                  <Separator />

                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Category</p>
                      <p>{component.category || 'Not specified'}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Domain</p>
                      <p>{component.domain || 'Not specified'}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Scale</p>
                      <p>{component.scale || 'Not specified'}</p>
                    </div>
                  </div>

                  {component.classification && (
                    <>
                      <Separator />
                      <div>
                        <p className="text-sm font-medium text-muted-foreground mb-2">Classification</p>
                        <div className="grid grid-cols-2 gap-4">
                          {component.classification.unspsc && (
                            <div>
                              <p className="text-xs text-muted-foreground">UNSPSC</p>
                              <p className="font-mono text-sm">{component.classification.unspsc}</p>
                            </div>
                          )}
                          {component.classification.hs_code && (
                            <div>
                              <p className="text-xs text-muted-foreground">HS Code</p>
                              <p className="font-mono text-sm">{component.classification.hs_code}</p>
                            </div>
                          )}
                          {component.classification.eclass && (
                            <div>
                              <p className="text-xs text-muted-foreground">eCl@ss</p>
                              <p className="font-mono text-sm">{component.classification.eclass}</p>
                            </div>
                          )}
                          {component.classification.gtin && (
                            <div>
                              <p className="text-xs text-muted-foreground">GTIN</p>
                              <p className="font-mono text-sm">{component.classification.gtin}</p>
                            </div>
                          )}
                        </div>
                      </div>
                    </>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="specifications" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Technical Specifications</CardTitle>
                  <CardDescription>
                    Detailed technical specifications extracted from datasheets
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="text-center py-12">
                    <FileText className="mx-auto h-12 w-12 text-muted-foreground" />
                    <h3 className="mt-2 text-sm font-semibold text-gray-900">No specifications</h3>
                    <p className="mt-1 text-sm text-muted-foreground">
                      Upload a datasheet to extract technical specifications automatically.
                    </p>
                    <div className="mt-6">
                      <Button>
                        <Upload className="h-4 w-4 mr-2" />
                        Upload Datasheet
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="documents" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Documents & Media</CardTitle>
                  <CardDescription>
                    Datasheets, certificates, and media assets
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="text-center py-12">
                    <FileText className="mx-auto h-12 w-12 text-muted-foreground" />
                    <h3 className="mt-2 text-sm font-semibold text-gray-900">No documents</h3>
                    <p className="mt-1 text-sm text-muted-foreground">
                      Upload datasheets, certificates, and other documents.
                    </p>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="history" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Component History</CardTitle>
                  <CardDescription>
                    Track all changes and status transitions
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-start space-x-3">
                      <div className="w-2 h-2 bg-primary rounded-full mt-2"></div>
                      <div className="flex-1 space-y-1">
                        <p className="text-sm font-medium">Component created</p>
                        <p className="text-xs text-muted-foreground">
                          {formatDate(component.created_at)}
                        </p>
                      </div>
                    </div>
                    {component.updated_at !== component.created_at && (
                      <div className="flex items-start space-x-3">
                        <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                        <div className="flex-1 space-y-1">
                          <p className="text-sm font-medium">Component updated</p>
                          <p className="text-xs text-muted-foreground">
                            {formatDate(component.updated_at)}
                          </p>
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Status Actions */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Status</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Current Status</span>
                <Badge className={getStatusColor(component.status)}>
                  {component.status}
                </Badge>
              </div>
              
              {getAvailableTransitions(component.status).length > 0 && (
                <div className="space-y-2">
                  <p className="text-sm font-medium">Available Transitions</p>
                  {getAvailableTransitions(component.status).map((status) => (
                    <Button
                      key={status}
                      variant="outline"
                      size="sm"
                      className="w-full justify-start"
                      onClick={() => transitionMutation.mutate({ newStatus: status })}
                      disabled={transitionMutation.isPending}
                    >
                      <Zap className="h-4 w-4 mr-2" />
                      Transition to {status}
                    </Button>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button variant="outline" size="sm" className="w-full justify-start">
                <Upload className="h-4 w-4 mr-2" />
                Upload Datasheet
              </Button>
              <Button variant="outline" size="sm" className="w-full justify-start">
                <Download className="h-4 w-4 mr-2" />
                Export Data
              </Button>
              <Button variant="outline" size="sm" className="w-full justify-start">
                <ExternalLink className="h-4 w-4 mr-2" />
                Add to Project
              </Button>
            </CardContent>
          </Card>

          {/* Metadata */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Metadata</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Created</p>
                <p className="text-sm">{formatDate(component.created_at)}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Last Updated</p>
                <p className="text-sm">{formatDate(component.updated_at)}</p>
              </div>
              {component.created_by && (
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Created By</p>
                  <p className="text-sm">{component.created_by}</p>
                </div>
              )}
              <div>
                <p className="text-sm font-medium text-muted-foreground">Active</p>
                <Badge variant={component.is_active ? "default" : "secondary"}>
                  {component.is_active ? "Yes" : "No"}
                </Badge>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
