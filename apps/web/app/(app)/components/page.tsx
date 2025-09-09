'use client'

import * as React from 'react'
import { useQuery } from '@tanstack/react-query'
import { 
  Plus, 
  Search, 
  Filter, 
  MoreHorizontal, 
  Grid3x3,
  List,
  Sun,
  Battery,
  Zap,
  Shield,
  Activity,
  Package,
  Eye,
  Edit,
  Archive,
  Download,
  Upload
} from 'lucide-react'
import { useRouter } from 'next/navigation'

import { 
  Button, 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle,
  Input,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Badge,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger
} from '@originfd/ui'
import { componentAPI } from '@/lib/api-client'
import { ComponentCreationWizard } from '@/components/components/component-creation-wizard'
import type { ComponentResponse, ComponentCategory, ComponentDomain, ComponentStatus } from '@/lib/types'

const categoryIcons = {
  generation: Sun,
  storage: Battery,
  conversion: Zap,
  protection: Shield,
  monitoring: Activity,
  structural: Package,
  other: Grid3x3
}

const categoryColors = {
  generation: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  storage: 'bg-green-100 text-green-800 border-green-200',
  conversion: 'bg-purple-100 text-purple-800 border-purple-200',
  protection: 'bg-red-100 text-red-800 border-red-200',
  monitoring: 'bg-blue-100 text-blue-800 border-blue-200',
  structural: 'bg-gray-100 text-gray-800 border-gray-200',
  other: 'bg-slate-100 text-slate-800 border-slate-200'
}

const statusColors = {
  draft: 'bg-gray-100 text-gray-800',
  parsed: 'bg-blue-100 text-blue-800',
  enriched: 'bg-indigo-100 text-indigo-800',
  approved: 'bg-green-100 text-green-800',
  available: 'bg-emerald-100 text-emerald-800',
  operational: 'bg-teal-100 text-teal-800',
  archived: 'bg-red-100 text-red-800'
}

export default function ComponentsPage() {
  const router = useRouter()
  const [newComponentModalOpen, setNewComponentModalOpen] = React.useState(false)
  const [viewMode, setViewMode] = React.useState<'grid' | 'list'>('grid')
  const [searchQuery, setSearchQuery] = React.useState('')
  const [categoryFilter, setCategoryFilter] = React.useState<string>('')
  const [domainFilter, setDomainFilter] = React.useState<string>('')
  const [statusFilter, setStatusFilter] = React.useState<string>('')
  const [page, setPage] = React.useState(1)

  // Fetch components
  const {
    data: componentsData,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['components', page, searchQuery, categoryFilter, domainFilter, statusFilter],
    queryFn: () => componentAPI.listComponents({
      page,
      page_size: 20,
      search: searchQuery || undefined,
      category: categoryFilter === 'all' ? undefined : categoryFilter || undefined,
      domain: domainFilter === 'all' ? undefined : domainFilter || undefined,
      status: statusFilter === 'all' ? undefined : statusFilter || undefined
    }),
  })

  // Fetch component stats
  const { data: stats } = useQuery({
    queryKey: ['component-stats'],
    queryFn: () => componentAPI.getStats(),
  })

  const components = componentsData?.components || []
  const totalComponents = componentsData?.total || 0

  const getCategoryIcon = (category?: ComponentCategory) => {
    if (!category) return Grid3x3
    return categoryIcons[category] || Grid3x3
  }

  const getCategoryColor = (category?: ComponentCategory) => {
    if (!category) return categoryColors.other
    return categoryColors[category] || categoryColors.other
  }

  const getStatusColor = (status: ComponentStatus) => {
    return statusColors[status] || 'bg-gray-100 text-gray-800'
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  const handleComponentClick = (component: ComponentResponse) => {
    router.push(`/components/${component.id}`)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Component Library</h1>
          <p className="text-muted-foreground">
            Manage your component catalog following ODL-SD v4.1 standards
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm">
            <Upload className="h-4 w-4 mr-2" />
            Import
          </Button>
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
          <Button onClick={() => setNewComponentModalOpen(true)} className="gap-2">
            <Plus className="h-4 w-4" />
            New Component
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Components</CardTitle>
              <Package className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_components}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Components</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.active_components}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Draft Components</CardTitle>
              <Edit className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.draft_components}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Categories</CardTitle>
              <Grid3x3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{Object.keys(stats.categories).length}</div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters and Search */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className="relative">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search components..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8 w-[300px]"
            />
          </div>
          <Select value={categoryFilter} onValueChange={setCategoryFilter}>
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="Category" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Categories</SelectItem>
              <SelectItem value="generation">Generation</SelectItem>
              <SelectItem value="storage">Storage</SelectItem>
              <SelectItem value="conversion">Conversion</SelectItem>
              <SelectItem value="protection">Protection</SelectItem>
              <SelectItem value="monitoring">Monitoring</SelectItem>
              <SelectItem value="structural">Structural</SelectItem>
              <SelectItem value="other">Other</SelectItem>
            </SelectContent>
          </Select>
          <Select value={domainFilter} onValueChange={setDomainFilter}>
            <SelectTrigger className="w-[120px]">
              <SelectValue placeholder="Domain" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Domains</SelectItem>
              <SelectItem value="PV">PV</SelectItem>
              <SelectItem value="BESS">BESS</SelectItem>
              <SelectItem value="HYBRID">Hybrid</SelectItem>
              <SelectItem value="GRID">Grid</SelectItem>
              <SelectItem value="MICROGRID">Microgrid</SelectItem>
            </SelectContent>
          </Select>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-[120px]">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="draft">Draft</SelectItem>
              <SelectItem value="approved">Approved</SelectItem>
              <SelectItem value="available">Available</SelectItem>
              <SelectItem value="operational">Operational</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant={viewMode === 'grid' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setViewMode('grid')}
          >
            <Grid3x3 className="h-4 w-4" />
          </Button>
          <Button
            variant={viewMode === 'list' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setViewMode('list')}
          >
            <List className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Components Display */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      ) : error ? (
        <div className="text-center py-12">
          <p className="text-muted-foreground">Error loading components. Please try again.</p>
        </div>
      ) : components.length === 0 ? (
        <div className="text-center py-12">
          <Package className="mx-auto h-12 w-12 text-muted-foreground" />
          <h3 className="mt-2 text-sm font-semibold text-gray-900">No components</h3>
          <p className="mt-1 text-sm text-muted-foreground">
            Get started by creating your first component.
          </p>
          <div className="mt-6">
            <Button onClick={() => setNewComponentModalOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              New Component
            </Button>
          </div>
        </div>
      ) : (
        <div className={
          viewMode === 'grid' 
            ? 'grid gap-6 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4'
            : 'space-y-4'
        }>
          {components.map((component) => {
            const CategoryIcon = getCategoryIcon(component.category)
            
            if (viewMode === 'grid') {
              return (
                <Card
                  key={component.id}
                  className="cursor-pointer hover:shadow-md transition-shadow"
                  onClick={() => handleComponentClick(component)}
                >
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center space-x-2">
                        <div className="p-2 rounded-lg bg-muted">
                          <CategoryIcon className="h-4 w-4" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <CardTitle className="text-sm font-medium truncate">
                            {component.brand} {component.part_number}
                          </CardTitle>
                          <CardDescription className="text-xs">
                            {component.rating_w}W
                          </CardDescription>
                        </div>
                      </div>
                      <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                        <MoreHorizontal className="h-3 w-3" />
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent className="pt-0">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-muted-foreground">Status</span>
                        <Badge variant="secondary" className={getStatusColor(component.status)}>
                          {component.status}
                        </Badge>
                      </div>
                      {component.category && (
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-muted-foreground">Category</span>
                          <Badge variant="outline" className={getCategoryColor(component.category)}>
                            {component.category}
                          </Badge>
                        </div>
                      )}
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-muted-foreground">Updated</span>
                        <span>{formatDate(component.updated_at)}</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )
            } else {
              return (
                <Card
                  key={component.id}
                  className="cursor-pointer hover:shadow-sm transition-shadow"
                  onClick={() => handleComponentClick(component)}
                >
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className="p-2 rounded-lg bg-muted">
                          <CategoryIcon className="h-4 w-4" />
                        </div>
                        <div>
                          <div className="font-medium">
                            {component.brand} {component.part_number}
                          </div>
                          <div className="text-sm text-muted-foreground">
                            {component.rating_w}W • {component.component_id}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-4">
                        {component.category && (
                          <Badge variant="outline" className={getCategoryColor(component.category)}>
                            {component.category}
                          </Badge>
                        )}
                        <Badge variant="secondary" className={getStatusColor(component.status)}>
                          {component.status}
                        </Badge>
                        <div className="text-sm text-muted-foreground">
                          {formatDate(component.updated_at)}
                        </div>
                        <Button variant="ghost" size="sm">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )
            }
          })}
        </div>
      )}

      {/* Pagination */}
      {totalComponents > 20 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Showing {((page - 1) * 20) + 1} to {Math.min(page * 20, totalComponents)} of {totalComponents} components
          </p>
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(page - 1)}
              disabled={page === 1}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(page + 1)}
              disabled={page * 20 >= totalComponents}
            >
              Next
            </Button>
          </div>
        </div>
      )}

      {/* New Component Modal */}
      <ComponentCreationWizard
        open={newComponentModalOpen}
        onOpenChange={setNewComponentModalOpen}
      />
    </div>
  )
}
