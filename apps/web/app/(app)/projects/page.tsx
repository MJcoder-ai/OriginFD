'use client'

import * as React from 'react'
import { useQuery } from '@tanstack/react-query'
import { Plus, Search, Filter, MoreHorizontal, Zap, Battery, Sun, Grid3x3 } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { apiClient } from '@/lib/api-client'
import { useAuth } from '@/lib/auth/auth-provider'
import { Button, Card, CardContent, CardDescription, CardHeader, CardTitle } from '@originfd/ui'
import { NewProjectModal } from '@/components/projects/new-project-modal'
import type { DocumentResponse } from '@originfd/types-odl'

export default function ProjectsPage() {
  const router = useRouter()
  const { user } = useAuth()
  const [newProjectModalOpen, setNewProjectModalOpen] = React.useState(false)
  // Debug: trigger recompilation

  // Fetch projects/documents
  const {
    data: projects = [],
    isLoading,
    error,
  } = useQuery({
    queryKey: ['projects'],
    queryFn: () => apiClient.listProjects(),
  })

  const displayProjects = projects

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

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Projects</h1>
          <p className="text-muted-foreground">
            Manage your energy system projects
          </p>
        </div>
        <Button onClick={() => {
          console.log('New Project button clicked!')
          console.log('Current modal state:', newProjectModalOpen)
          setNewProjectModalOpen(true)
          console.log('Modal state set to true')
        }} className="gap-2">
          <Plus className="h-4 w-4" />
          New Project
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

      {/* Projects Grid */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      ) : error ? (
        <div className="text-center py-12">
          <div className="max-w-md mx-auto">
            <div className="text-red-500 mb-4">
              <svg className="h-12 w-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Failed to load projects</h3>
            <p className="text-muted-foreground mb-4">
              There was an error connecting to the server. Please check your connection and try again.
            </p>
            <Button 
              onClick={() => window.location.reload()} 
              variant="outline"
            >
              Try Again
            </Button>
          </div>
        </div>
      ) : displayProjects?.length > 0 ? (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {displayProjects.map((project) => (
            <Card
              key={project.id}
              className="cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => router.push(`/projects/${project.id}`)}
            >
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 rounded-lg bg-muted">
                      {getDomainIcon(project.domain)}
                    </div>
                    <div className="flex-1">
                      <CardTitle className="text-lg">{project.project_name}</CardTitle>
                      <div className="flex items-center gap-2 mt-1">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${getDomainColor(project.domain)}`}>
                          {project.domain}
                        </span>
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${getScaleBadgeColor(project.scale)}`}>
                          {project.scale}
                        </span>
                      </div>
                    </div>
                  </div>
                  <Button 
                    variant="ghost" 
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation()
                      // Handle menu actions
                    }}
                  >
                    <MoreHorizontal className="h-4 w-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Version</span>
                    <span>v{project.current_version}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Status</span>
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                      project.is_active
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {project.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Updated</span>
                    <span>{formatDate(project.updated_at)}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <div className="max-w-md mx-auto">
            <div className="text-muted-foreground mb-4">
              <svg className="h-12 w-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No projects yet</h3>
            <p className="text-muted-foreground mb-4">
              Get started by creating your first energy system project.
            </p>
            <Button onClick={() => setNewProjectModalOpen(true)} className="gap-2">
              <Plus className="h-4 w-4" />
              Create Project
            </Button>
          </div>
        </div>
      )}

      {/* New Project Modal */}
      <NewProjectModal
        open={newProjectModalOpen}
        onOpenChange={setNewProjectModalOpen}
      />
    </div>
  )
}
