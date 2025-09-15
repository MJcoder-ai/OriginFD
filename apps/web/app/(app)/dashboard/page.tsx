'use client'

import * as React from 'react'
import { useQuery } from '@tanstack/react-query'
import { Plus, Search, Filter, MoreHorizontal, Zap, Battery, Sun, Grid3x3 } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { apiClient } from '@/lib/api-client'
import { useAuth } from '@/lib/auth/auth-provider'
import { Button, Card, CardContent, CardDescription, CardHeader, CardTitle, LoadingSpinner, ErrorBoundary } from '@originfd/ui'
import { NewProjectModal } from '@/components/projects/new-project-modal'
import type { DocumentResponse } from '@/lib/types'

export default function DashboardPage() {
  const router = useRouter()
  const { user } = useAuth()
  const [newProjectModalOpen, setNewProjectModalOpen] = React.useState(false)
  const [selectedDomain, setSelectedDomain] = React.useState<string | undefined>()


  // Fetch projects/documents
  const {
    data: projects = [],
    isLoading,
    error,
  } = useQuery({
    queryKey: ['projects'],
    queryFn: () => apiClient.listProjects(),
  })

  // Mock data for demo
  const mockProjects: DocumentResponse[] = [
    {
      id: '1',
      project_name: 'Solar Farm Arizona Phase 1',
      domain: 'PV',
      scale: 'UTILITY',
      current_version: 3,
      content_hash: 'sha256:abc123',
      is_active: true,
      created_at: '2024-01-15T10:30:00Z',
      updated_at: '2024-01-20T15:45:00Z',
    },
    {
      id: '2',
      project_name: 'Commercial BESS Installation',
      domain: 'BESS',
      scale: 'COMMERCIAL',
      current_version: 1,
      content_hash: 'sha256:def456',
      is_active: true,
      created_at: '2024-01-18T09:15:00Z',
      updated_at: '2024-01-18T09:15:00Z',
    },
    {
      id: '3',
      project_name: 'Hybrid Microgrid Campus',
      domain: 'HYBRID',
      scale: 'INDUSTRIAL',
      current_version: 2,
      content_hash: 'sha256:ghi789',
      is_active: true,
      created_at: '2024-01-22T14:20:00Z',
      updated_at: '2024-01-23T11:30:00Z',
    },
  ]

  const displayProjects = React.useMemo(() => {
    if (projects.length > 0) {
      console.log('Dashboard: Using API data -', projects.length, 'projects loaded')
      return projects
    } else {
      if (error) {
        console.warn('Dashboard: API failed, falling back to mock data. Error:', error)
      } else {
        console.log('Dashboard: No API data available, using mock data -', mockProjects.length, 'projects')
      }
      return mockProjects
    }
  }, [projects, error])

  const getDomainIcon = (domain: string) => {
    switch (domain) {
      case 'PV':
        return <Sun className="h-5 w-5 text-yellow-600" />
      case 'BESS':
        return <Battery className="h-5 w-5 text-green-600" />
      case 'HYBRID':
        return <Zap className="h-5 w-5 text-purple-600" />
      case 'GRID':
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
        return 'bg-blue-100 text-blue-800 border-blue-200'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const getScaleBadgeColor = (scale: string) => {
    switch (scale) {
      case 'UTILITY':
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

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  const stats = [
    {
      name: 'Total Projects',
      value: displayProjects.length,
      icon: Grid3x3,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
    },
    {
      name: 'Active Projects',
      value: displayProjects.filter(p => p.is_active).length,
      icon: Zap,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
    },
    {
      name: 'PV Projects',
      value: displayProjects.filter(p => p.domain === 'PV').length,
      icon: Sun,
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-100',
    },
    {
      name: 'BESS Projects',
      value: displayProjects.filter(p => p.domain === 'BESS').length,
      icon: Battery,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
    },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Welcome back, {user?.full_name || user?.email}
          </p>
        </div>
        <Button onClick={(e) => {
          e.preventDefault()
          e.stopPropagation()
          setTimeout(() => {
            setNewProjectModalOpen(true)
          }, 0)
        }} className="gap-2">
          <Plus className="h-4 w-4" />
          New Project
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => {
          const Icon = stat.icon
          return (
            <Card key={stat.name}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  {stat.name}
                </CardTitle>
                <div className={`p-2 rounded-full ${stat.bgColor}`}>
                  <Icon className={`h-4 w-4 ${stat.color}`} />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stat.value}</div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Projects Section */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Recent Projects</CardTitle>
              <CardDescription>
                Manage your energy system projects
              </CardDescription>
            </div>
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
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex items-center justify-center h-32">
              <LoadingSpinner />
            </div>
          ) : error ? (
            <div className="flex items-center justify-center h-32 text-muted-foreground">
              <p>Error loading projects. Using demo data.</p>
            </div>
          ) : (
            <div className="divide-y">
              {displayProjects.map((project) => (
                <div
                  key={project.id}
                  className="p-6 hover:bg-muted/50 transition-colors cursor-pointer"
                  onClick={() => router.push(`/projects/${project.id}`)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className="p-2 rounded-lg bg-muted">
                        {getDomainIcon(project.domain)}
                      </div>
                      <div>
                        <h3 className="font-medium text-foreground">
                          {project.project_name}
                        </h3>
                        <div className="flex items-center gap-2 mt-1">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getDomainColor(project.domain)}`}>
                            {project.domain}
                          </span>
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getScaleBadgeColor(project.scale)}`}>
                            {project.scale}
                          </span>
                          <span className="text-xs text-muted-foreground">
                            v{project.current_version}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-4">
                      <div className="text-right">
                        <p className="text-sm text-muted-foreground">
                          Updated {formatDate(project.updated_at)}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          Created {formatDate(project.created_at)}
                        </p>
                      </div>
                      <Button variant="ghost" size="sm">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card
          className="cursor-pointer hover:shadow-md transition-shadow"
          onClick={(e) => {
            e.preventDefault()
            e.stopPropagation()
            setSelectedDomain('PV')
            setTimeout(() => {
              setNewProjectModalOpen(true)
            }, 0)
          }}
        >
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Sun className="h-5 w-5 text-yellow-600" />
              Create PV System
            </CardTitle>
            <CardDescription>
              Design a new solar photovoltaic system
            </CardDescription>
          </CardHeader>
        </Card>

        <Card
          className="cursor-pointer hover:shadow-md transition-shadow"
          onClick={(e) => {
            e.preventDefault()
            e.stopPropagation()
            setSelectedDomain('BESS')
            setTimeout(() => {
              setNewProjectModalOpen(true)
            }, 0)
          }}
        >
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Battery className="h-5 w-5 text-green-600" />
              Create BESS
            </CardTitle>
            <CardDescription>
              Design a battery energy storage system
            </CardDescription>
          </CardHeader>
        </Card>

        <Card
          className="cursor-pointer hover:shadow-md transition-shadow"
          onClick={(e) => {
            e.preventDefault()
            e.stopPropagation()
            setSelectedDomain('HYBRID')
            setTimeout(() => {
              setNewProjectModalOpen(true)
            }, 0)
          }}
        >
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Zap className="h-5 w-5 text-purple-600" />
              Create Hybrid System
            </CardTitle>
            <CardDescription>
              Design a combined PV + BESS system
            </CardDescription>
          </CardHeader>
        </Card>
      </div>

      {/* New Project Modal */}
      <NewProjectModal
        open={newProjectModalOpen}
        onOpenChange={(open) => {
          setNewProjectModalOpen(open)
          if (!open) {
            setSelectedDomain(undefined)
          }
        }}
        defaultDomain={selectedDomain}
      />
    </div>
  )
}