'use client'

import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ComponentLifecycleManager, getStatusBadgeProps, getProgressColor } from '@/lib/component-lifecycle'
import { ComponentResponse, ODLComponentStatus } from '@/lib/types'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Progress,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Input,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  Textarea,
  Label
} from '@originfd/ui'
import {
  ArrowRight,
  Clock,
  Users,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Play,
  Pause,
  Settings,
  Filter,
  Search,
  BarChart3,
  Activity,
  Workflow,
  FileText
} from 'lucide-react'

interface LifecycleDashboardProps {
  userRole?: string
  components?: ComponentResponse[]
}

export default function LifecycleDashboard({ userRole = 'admin', components = [] }: LifecycleDashboardProps) {
  const queryClient = useQueryClient()
  const [selectedComponent, setSelectedComponent] = useState<ComponentResponse | null>(null)
  const [transitionDialogOpen, setTransitionDialogOpen] = useState(false)
  const [selectedStatus, setSelectedStatus] = useState<ODLComponentStatus>('draft')
  const [transitionReason, setTransitionReason] = useState('')
  const [stageFilter, setStageFilter] = useState<string>('all')
  const [searchQuery, setSearchQuery] = useState('')

  // Fetch components with lifecycle data
  const { data: lifecycleData, isLoading } = useQuery({
    queryKey: ['components-lifecycle', stageFilter, searchQuery],
    queryFn: async () => {
      const response = await fetch('/api/bridge/components')
      if (!response.ok) throw new Error('Failed to fetch components')
      return response.json()
    }
  })

  // Fetch component statistics
  const { data: stats } = useQuery({
    queryKey: ['component-stats'],
    queryFn: async () => {
      const response = await fetch('/api/bridge/components/stats')
      if (!response.ok) throw new Error('Failed to fetch stats')
      return response.json()
    }
  })

  // Lifecycle transition mutation
  const transitionMutation = useMutation({
    mutationFn: async (data: {
      componentId: string
      newStatus: ODLComponentStatus
      reason: string
    }) => {
      const response = await fetch(`/api/bridge/components/${data.componentId}/lifecycle`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          new_status: data.newStatus,
          transition_reason: data.reason,
          updated_by: 'current_user'
        })
      })
      if (!response.ok) throw new Error('Failed to transition component')
      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['components-lifecycle'] })
      queryClient.invalidateQueries({ queryKey: ['component-stats'] })
      setTransitionDialogOpen(false)
      setSelectedComponent(null)
      setTransitionReason('')
    }
  })

  const handleTransition = () => {
    if (!selectedComponent) return

    transitionMutation.mutate({
      componentId: selectedComponent.id,
      newStatus: selectedStatus,
      reason: transitionReason
    })
  }

  // Get lifecycle stages overview
  const getLifecycleOverview = () => {
    if (!lifecycleData) return []

    const stageGroups = ComponentLifecycleManager.getLifecycleStages()
    return stageGroups.map(stage => {
      const stageStatuses = ComponentLifecycleManager.getStatusesByStage(stage.stage)
      const count = lifecycleData.filter((comp: ComponentResponse) =>
        stageStatuses.includes(comp.component_management?.status as ODLComponentStatus)
      ).length

      return {
        ...stage,
        count,
        percentage: lifecycleData.length > 0 ? (count / lifecycleData.length) * 100 : 0
      }
    })
  }

  const lifecycleOverview = getLifecycleOverview()

  // Filter components based on current filters
  const filteredComponents = lifecycleData?.filter((comp: ComponentResponse) => {
    if (stageFilter !== 'all') {
      const stageStatuses = ComponentLifecycleManager.getStatusesByStage(stageFilter)
      if (!stageStatuses.includes(comp.component_management?.status as ODLComponentStatus)) {
        return false
      }
    }

    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      return (
        comp.component_management?.component_identity?.name?.toLowerCase().includes(query) ||
        comp.component_management?.component_identity?.brand?.toLowerCase().includes(query) ||
        comp.component_management?.component_identity?.part_number?.toLowerCase().includes(query)
      )
    }

    return true
  }) || []

  const getStatusDisplay = (status: ODLComponentStatus) => {
    return ComponentLifecycleManager.getStatusDisplay(status)
  }

  const getValidTransitions = (currentStatus: ODLComponentStatus) => {
    return ComponentLifecycleManager.getValidTransitions(currentStatus)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Component Lifecycle Management</h1>
          <p className="text-muted-foreground">
            Manage components through all 19 ODL-SD v4.1 lifecycle stages
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm">
            <BarChart3 className="h-4 w-4 mr-2" />
            Analytics
          </Button>
          <Button variant="outline" size="sm">
            <FileText className="h-4 w-4 mr-2" />
            Reports
          </Button>
          <Button size="sm">
            <Settings className="h-4 w-4 mr-2" />
            Configure
          </Button>
        </div>
      </div>

      {/* Lifecycle Overview Cards */}
      <div className="grid gap-4 md:grid-cols-4 lg:grid-cols-6">
        {lifecycleOverview.map((stage) => (
          <Card key={stage.stage} className="relative overflow-hidden">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">{stage.label}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="text-2xl font-bold">{stage.count}</div>
                <Progress value={stage.percentage} className="h-1" />
                <div className="text-xs text-muted-foreground">
                  {stage.percentage.toFixed(1)}% of total
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="components" className="space-y-4">
        <TabsList>
          <TabsTrigger value="components">Components</TabsTrigger>
          <TabsTrigger value="workflow">Workflow</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
          <TabsTrigger value="transitions">Pending Transitions</TabsTrigger>
        </TabsList>

        <TabsContent value="components" className="space-y-4">
          {/* Filters */}
          <div className="flex items-center space-x-4">
            <div className="relative">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search components..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8 w-[300px]"
              />
            </div>
            <Select value={stageFilter} onValueChange={setStageFilter}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="Filter by stage" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Stages</SelectItem>
                {ComponentLifecycleManager.getLifecycleStages().map((stage) => (
                  <SelectItem key={stage.stage} value={stage.stage}>
                    {stage.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button variant="outline" size="sm">
              <Filter className="h-4 w-4 mr-2" />
              More Filters
            </Button>
          </div>

          {/* Components Grid */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {filteredComponents.map((component: ComponentResponse) => {
              const currentStatus = component.component_management?.status as ODLComponentStatus
              const statusDisplay = getStatusDisplay(currentStatus)
              const progress = ComponentLifecycleManager.getProgressPercentage(currentStatus)
              const validTransitions = getValidTransitions(currentStatus)
              const identity = component.component_management?.component_identity

              return (
                <Card key={component.id} className="relative">
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <CardTitle className="text-sm font-medium truncate">
                          {identity?.brand} {identity?.part_number}
                        </CardTitle>
                        <div className="text-xs text-muted-foreground">
                          {identity?.name}
                        </div>
                      </div>
                      <Badge
                        variant="outline"
                        className={`text-xs ${statusDisplay.color}`}
                      >
                        {statusDisplay.label}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {/* Progress Bar */}
                    <div className="space-y-1">
                      <div className="flex justify-between text-xs">
                        <span>Lifecycle Progress</span>
                        <span>{progress}%</span>
                      </div>
                      <Progress value={progress} className="h-1" />
                      <div className="text-xs text-muted-foreground">
                        Stage: {statusDisplay.stage}
                      </div>
                    </div>

                    {/* Quick Actions */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-1">
                        {validTransitions.length > 0 && (
                          <Dialog open={transitionDialogOpen && selectedComponent?.id === component.id}>
                            <DialogTrigger asChild>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => setSelectedComponent(component)}
                              >
                                <ArrowRight className="h-3 w-3 mr-1" />
                                Transition
                              </Button>
                            </DialogTrigger>
                            <DialogContent>
                              <DialogHeader>
                                <DialogTitle>Transition Component</DialogTitle>
                              </DialogHeader>
                              <div className="space-y-4">
                                <div>
                                  <Label>Current Status</Label>
                                  <div className="text-sm text-muted-foreground">
                                    {statusDisplay.label} - {statusDisplay.description}
                                  </div>
                                </div>

                                <div>
                                  <Label htmlFor="newStatus">New Status</Label>
                                  <Select value={selectedStatus} onValueChange={(value) => setSelectedStatus(value as ODLComponentStatus)}>
                                    <SelectTrigger>
                                      <SelectValue placeholder="Select new status" />
                                    </SelectTrigger>
                                    <SelectContent>
                                      {validTransitions.map((status) => {
                                        const display = getStatusDisplay(status)
                                        return (
                                          <SelectItem key={status} value={status}>
                                            {display.label} - {display.description}
                                          </SelectItem>
                                        )
                                      })}
                                    </SelectContent>
                                  </Select>
                                </div>

                                <div>
                                  <Label htmlFor="reason">Transition Reason</Label>
                                  <Textarea
                                    id="reason"
                                    placeholder="Explain why this transition is being made..."
                                    value={transitionReason}
                                    onChange={(e) => setTransitionReason(e.target.value)}
                                  />
                                </div>

                                <div className="flex justify-end space-x-2">
                                  <Button
                                    variant="outline"
                                    onClick={() => {
                                      setTransitionDialogOpen(false)
                                      setSelectedComponent(null)
                                    }}
                                  >
                                    Cancel
                                  </Button>
                                  <Button
                                    onClick={handleTransition}
                                    disabled={!selectedStatus || !transitionReason.trim() || transitionMutation.isPending}
                                  >
                                    {transitionMutation.isPending ? 'Processing...' : 'Confirm Transition'}
                                  </Button>
                                </div>
                              </div>
                            </DialogContent>
                          </Dialog>
                        )}
                      </div>

                      <div className="flex items-center space-x-1">
                        <Button size="sm" variant="ghost">
                          <Activity className="h-3 w-3" />
                        </Button>
                        <Button size="sm" variant="ghost">
                          <FileText className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>

                    {/* Component Details */}
                    <div className="text-xs space-y-1">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Rating:</span>
                        <span>{identity?.rating_w}W</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Updated:</span>
                        <span>{new Date(component.component_management?.audit?.updated_at || '').toLocaleDateString()}</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </TabsContent>

        <TabsContent value="workflow">
          <Card>
            <CardHeader>
              <CardTitle>Workflow Visualization</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center text-muted-foreground">
                <Workflow className="mx-auto h-12 w-12 mb-4" />
                <p>Interactive workflow diagram coming soon...</p>
                <p className="text-sm">This will show the complete ODL-SD v4.1 lifecycle flow</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="analytics">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Processing Times</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center text-muted-foreground">
                  <TrendingUp className="mx-auto h-8 w-8 mb-2" />
                  <p>Analytics dashboard coming soon...</p>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Bottleneck Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center text-muted-foreground">
                  <BarChart3 className="mx-auto h-8 w-8 mb-2" />
                  <p>Bottleneck detection coming soon...</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="transitions">
          <Card>
            <CardHeader>
              <CardTitle>Pending Transitions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center text-muted-foreground">
                <Clock className="mx-auto h-8 w-8 mb-2" />
                <p>No pending transitions</p>
                <p className="text-sm">All components are in stable states</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}