'use client'

import * as React from 'react'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Button
} from '@originfd/ui'
import {
  ChevronDown,
  ChevronRight,
  Download,
  Copy,
  Check,
  Sun,
  Battery,
  Zap,
  Power,
  Grid3x3,
  Cable,
  CheckCircle,
  Info,
  Calendar,
  User,
  Hash
} from 'lucide-react'
import { OdlDocument, ComponentInstance, Connection } from '@/lib/types'
import { apiClient } from '@/lib/api-client'

// Simple inline components since they're not in the UI library yet
const Badge = ({ children, variant = "secondary", className = "" }: {
  children: React.ReactNode;
  variant?: "secondary" | "outline";
  className?: string;
}) => (
  <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${
    variant === "outline" ? "bg-transparent" : "bg-gray-100"
  } ${className}`}>
    {children}
  </span>
)

const Collapsible = ({ children, open, onOpenChange }: {
  children: React.ReactNode;
  open?: boolean;
  onOpenChange?: () => void;
}) => <div>{children}</div>

const CollapsibleTrigger = ({ children, onClick, asChild }: {
  children: React.ReactNode;
  onClick?: () => void;
  asChild?: boolean;
}) => (
  asChild ? <div className="cursor-pointer">{children}</div> :
  <button onClick={onClick} className="flex items-center w-full text-left">{children}</button>
)

const CollapsibleContent = ({ isOpen, children }: { isOpen: boolean; children: React.ReactNode }) => (
  isOpen ? <div>{children}</div> : null
)

interface DocumentViewerProps {
  document: OdlDocument
  projectId?: string
  className?: string
}

export function DocumentViewer({ document, projectId, className }: DocumentViewerProps) {
  const [copiedTab, setCopiedTab] = React.useState<string | null>(null)
  const [expandedComponents, setExpandedComponents] = React.useState<Set<string>>(new Set())
  const [expandedConnections, setExpandedConnections] = React.useState<Set<string>>(new Set())

  const copyToClipboard = async (content: string, tabName: string) => {
    try {
      await navigator.clipboard.writeText(content)
      setCopiedTab(tabName)
      setTimeout(() => setCopiedTab(null), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const toggleComponent = (componentId: string) => {
    const newExpanded = new Set(expandedComponents)
    if (newExpanded.has(componentId)) {
      newExpanded.delete(componentId)
    } else {
      newExpanded.add(componentId)
    }
    setExpandedComponents(newExpanded)
  }

  const toggleConnection = (connectionId: string) => {
    const newExpanded = new Set(expandedConnections)
    if (newExpanded.has(connectionId)) {
      newExpanded.delete(connectionId)
    } else {
      newExpanded.add(connectionId)
    }
    setExpandedConnections(newExpanded)
  }

  const getComponentIcon = (type: string) => {
    switch (type) {
      case 'pv_array':
        return <Sun className="h-4 w-4 text-yellow-600" />
      case 'inverter':
        return <Power className="h-4 w-4 text-blue-600" />
      case 'battery':
        return <Battery className="h-4 w-4 text-green-600" />
      case 'power_conversion_system':
        return <Zap className="h-4 w-4 text-purple-600" />
      default:
        return <Grid3x3 className="h-4 w-4 text-gray-600" />
    }
  }

  const getComponentTypeName = (type: string) => {
    switch (type) {
      case 'pv_array':
        return 'PV Array'
      case 'inverter':
        return 'Inverter'
      case 'battery':
        return 'Battery'
      case 'power_conversion_system':
        return 'Power Conversion System'
      default:
        return type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())
    }
  }

  const getConnectionTypeColor = (type: string) => {
    switch (type) {
      case 'dc_electrical':
        return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'ac_electrical':
        return 'bg-green-100 text-green-800 border-green-200'
      case 'communication':
        return 'bg-purple-100 text-purple-800 border-purple-200'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const formatCapacity = (value: number | null | undefined): string => {
    if (value === null || value === undefined) return 'Not specified'
    if (value >= 1000) {
      return `${(value / 1000).toFixed(1)} MW`
    }
    return `${value.toFixed(0)} kW`
  }

  const formatCurrency = (value: number, currency = 'USD'): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(value)
  }

  const downloadDocument = async (format: 'json' | 'yaml') => {
    if (!projectId) {
      // Fallback: download current document as JSON
      const content = format === 'json'
        ? JSON.stringify(document, null, 2)
        : JSON.stringify(document, null, 2) // Would need yaml library for proper YAML conversion

      const blob = new Blob([content], { type: `application/${format}` })
      const url = URL.createObjectURL(blob)
      const a = window.document.createElement('a')
      a.href = url
      a.download = `${document.meta?.project?.replace(/\s+/g, '-').toLowerCase() || 'document'}.${format}`
      window.document.body.appendChild(a)
      a.click()
      window.document.body.removeChild(a)
      URL.revokeObjectURL(url)
      return
    }

    try {
      const content = await apiClient.exportDocument(projectId, format)
      const blob = new Blob([content], { type: `application/${format}` })
      const url = URL.createObjectURL(blob)
      const a = window.document.createElement('a')
      a.href = url
      a.download = `${document.meta?.project?.replace(/\s+/g, '-').toLowerCase() || 'document'}.${format}`
      window.document.body.appendChild(a)
      a.click()
      window.document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Failed to download document:', error)
    }
  }

  return (
    <div className={className}>
      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="components">Components</TabsTrigger>
          <TabsTrigger value="connections">Connections</TabsTrigger>
          <TabsTrigger value="requirements">Requirements</TabsTrigger>
          <TabsTrigger value="audit">Audit Trail</TabsTrigger>
          <TabsTrigger value="raw">Raw JSON</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {/* Project Metadata */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Info className="h-5 w-5" />
                  Project Information
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Project Name</p>
                  <p className="text-sm">{document.meta.project}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Domain & Scale</p>
                  <div className="flex gap-2 mt-1">
                    <Badge variant="outline">{document.meta.domain}</Badge>
                    <Badge variant="outline">{document.meta.scale}</Badge>
                  </div>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Location</p>
                  <p className="text-sm">{document.hierarchy.portfolio?.location || 'Not specified'}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Schema Version</p>
                  <p className="text-sm">ODL-SD v{document.schema_version}</p>
                </div>
              </CardContent>
            </Card>

            {/* System Overview */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Zap className="h-5 w-5" />
                  System Overview
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Total Capacity</p>
                  <p className="text-lg font-semibold">
                    {formatCapacity(document.requirements?.functional?.capacity_kw)}
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Components</p>
                  <p className="text-sm">{document.instances.length} total</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Connections</p>
                  <p className="text-sm">{document.connections.length} total</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Grid Connected</p>
                  <div className="flex items-center gap-2">
                    {document.requirements?.technical?.grid_connection ? (
                      <CheckCircle className="h-4 w-4 text-green-600" />
                    ) : (
                      <div className="h-4 w-4 rounded-full bg-red-200" />
                    )}
                    <span className="text-sm">
                      {document.requirements?.technical?.grid_connection ? 'Yes' : 'No'}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Document Status */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Hash className="h-5 w-5" />
                  Document Status
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Version</p>
                  <p className="text-sm">{document.meta?.versioning?.document_version || 'Not specified'}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Content Hash</p>
                  <p className="text-xs font-mono bg-muted px-2 py-1 rounded">
                    {document.meta?.versioning?.content_hash?.substring(7, 19) || 'N/A'}...
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Last Updated</p>
                  <p className="text-sm">
                    {document.meta?.timestamps?.updated_at ? new Date(document.meta.timestamps.updated_at).toLocaleDateString() : 'Not available'}
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Units</p>
                  <p className="text-sm">{document.meta?.units?.system || 'N/A'} / {document.meta?.units?.currency || 'N/A'}</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Components Tab */}
        <TabsContent value="components" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>System Components ({document.instances.length})</CardTitle>
              <CardDescription>
                Detailed view of all components in the system
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {document.instances.map((component: any) => (
                  <Card key={component.id} className="border-l-4 border-l-blue-200">
                        <CardHeader className="pb-2 cursor-pointer hover:bg-muted/50" onClick={() => toggleComponent(component.id)}>
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                              {getComponentIcon(component.type)}
                              <div>
                                <CardTitle className="text-base">{component.id}</CardTitle>
                                <CardDescription>{getComponentTypeName(component.type)}</CardDescription>
                              </div>
                            </div>
                            {expandedComponents.has(component.id) ? (
                              <ChevronDown className="h-4 w-4" />
                            ) : (
                              <ChevronRight className="h-4 w-4" />
                            )}
                          </div>
                        </CardHeader>
                        {expandedComponents.has(component.id) && (
                        <CardContent className="pt-0">
                          <div className="grid gap-4 md:grid-cols-2">
                            <div>
                              <h4 className="font-medium text-sm mb-2">Parameters</h4>
                              <div className="space-y-2">
                                {Object.entries(component.parameters).map(([key, value]) => (
                                  <div key={key} className="flex justify-between">
                                    <span className="text-sm text-muted-foreground capitalize">
                                      {key.replace('_', ' ')}:
                                    </span>
                                    <span className="text-sm font-mono">
                                      {typeof value === 'number' && key.includes('kw')
                                        ? formatCapacity(value)
                                        : String(value)
                                      }
                                    </span>
                                  </div>
                                ))}
                              </div>
                            </div>
                            <div>
                              <h4 className="font-medium text-sm mb-2">Metadata</h4>
                              <div className="space-y-2">
                                {Object.entries(component.metadata).map(([key, value]) => (
                                  <div key={key} className="flex justify-between">
                                    <span className="text-sm text-muted-foreground capitalize">
                                      {key.replace('_', ' ')}:
                                    </span>
                                    <span className="text-sm">{String(value)}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          </div>
                        </CardContent>
                        )}
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Connections Tab */}
        <TabsContent value="connections" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>System Connections ({document.connections.length})</CardTitle>
              <CardDescription>
                Electrical and communication connections between components
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {document.connections.map((connection: any) => (
                  <Card key={connection.id} className="border-l-4 border-l-green-200">
                        <CardHeader className="pb-2 cursor-pointer hover:bg-muted/50" onClick={() => toggleConnection(connection.id)}>
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                              <Cable className="h-4 w-4 text-green-600" />
                              <div>
                                <CardTitle className="text-base">{connection.id}</CardTitle>
                                <CardDescription>
                                  {connection.from_component} → {connection.to_component}
                                </CardDescription>
                              </div>
                              <Badge
                                variant="outline"
                                className={getConnectionTypeColor(connection.connection_type)}
                              >
                                {connection.connection_type.replace('_', ' ').toUpperCase()}
                              </Badge>
                            </div>
                            {expandedConnections.has(connection.id) ? (
                              <ChevronDown className="h-4 w-4" />
                            ) : (
                              <ChevronRight className="h-4 w-4" />
                            )}
                          </div>
                        </CardHeader>
                        {expandedConnections.has(connection.id) && (
                        <CardContent className="pt-0">
                          <div>
                            <h4 className="font-medium text-sm mb-2">Connection Parameters</h4>
                            <div className="space-y-2">
                              {Object.entries(connection.parameters).map(([key, value]) => (
                                <div key={key} className="flex justify-between">
                                  <span className="text-sm text-muted-foreground capitalize">
                                    {key.replace('_', ' ')}:
                                  </span>
                                  <span className="text-sm font-mono">{String(value)}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        </CardContent>
                        )}
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Requirements Tab */}
        <TabsContent value="requirements" className="space-y-6">
          <div className="grid gap-6 md:grid-cols-3">
            {/* Functional Requirements */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Zap className="h-5 w-5" />
                  Functional
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">System Capacity</p>
                  <p className="text-sm">
                    {formatCapacity(document.requirements?.functional?.capacity_kw)}
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Annual Generation</p>
                  <p className="text-sm">
                    {document.requirements?.functional?.annual_generation_kwh
                      ? `${(document.requirements.functional.annual_generation_kwh / 1000).toFixed(0)} MWh`
                      : 'Not specified'
                    }
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Performance Requirements</p>
                  <p className="text-sm">
                    {document.requirements?.functional?.performance_requirements
                      ? Object.keys(document.requirements.functional.performance_requirements).length
                      : 0
                    } defined
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Technical Requirements */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Grid3x3 className="h-5 w-5" />
                  Technical
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Grid Connection</p>
                  <div className="flex items-center gap-2">
                    {document.requirements?.technical?.grid_connection ? (
                      <CheckCircle className="h-4 w-4 text-green-600" />
                    ) : (
                      <div className="h-4 w-4 rounded-full bg-red-200" />
                    )}
                    <span className="text-sm">
                      {document.requirements?.technical?.grid_connection ? 'Required' : 'Not required'}
                    </span>
                  </div>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Voltage Level</p>
                  <p className="text-sm">{document.requirements?.technical?.voltage_level || 'Not specified'}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Frequency</p>
                  <p className="text-sm">
                    {document.requirements?.technical?.frequency_hz
                      ? `${document.requirements.technical.frequency_hz} Hz`
                      : 'Not specified'
                    }
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Regulatory Requirements */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <CheckCircle className="h-5 w-5" />
                  Regulatory
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Grid Codes</p>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {document.requirements?.regulatory?.grid_codes?.map((code: any) => (
                      <Badge key={code} variant="outline" className="text-xs">
                        {code}
                      </Badge>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Safety Standards</p>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {document.requirements?.regulatory?.safety_standards?.map((standard: any) => (
                      <Badge key={standard} variant="outline" className="text-xs">
                        {standard}
                      </Badge>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Environmental Permits</p>
                  <p className="text-sm">
                    {document.requirements?.regulatory?.environmental_permits?.length
                      ? `${document.requirements.regulatory.environmental_permits.length} required`
                      : 'None required'
                    }
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Audit Trail Tab */}
        <TabsContent value="audit" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="h-5 w-5" />
                Audit Trail ({document.audit.length})
              </CardTitle>
              <CardDescription>
                Complete history of changes to this document
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {document.audit.map((entry: any, index: number) => (
                  <div key={index} className="flex items-start gap-3 pb-4 border-b last:border-b-0">
                    <div className="mt-1">
                      <User className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge variant="outline" className="text-xs">
                          {entry.action.replace('_', ' ')}
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          {new Date(entry.timestamp).toLocaleString()}
                        </span>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        User: {entry.user_id.substring(0, 8)}...
                      </p>
                      {Object.keys(entry.changes).length > 0 && (
                        <div className="mt-2 text-xs">
                          <pre className="bg-muted p-2 rounded text-xs">
                            {JSON.stringify(entry.changes, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Raw JSON Tab */}
        <TabsContent value="raw" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Raw ODL-SD Document</CardTitle>
                  <CardDescription>
                    Complete JSON representation of the ODL-SD document
                  </CardDescription>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => copyToClipboard(JSON.stringify(document, null, 2), 'json')}
                  >
                    {copiedTab === 'json' ? (
                      <Check className="h-4 w-4 mr-2" />
                    ) : (
                      <Copy className="h-4 w-4 mr-2" />
                    )}
                    {copiedTab === 'json' ? 'Copied!' : 'Copy JSON'}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => downloadDocument('json')}
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Download JSON
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="relative">
                <pre className="bg-muted p-4 rounded-lg text-xs overflow-auto max-h-96 font-mono">
                  {JSON.stringify(document, null, 2)}
                </pre>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
