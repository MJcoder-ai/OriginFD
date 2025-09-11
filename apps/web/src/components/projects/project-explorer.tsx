'use client'

import * as React from 'react'
import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'
import { FolderOpen, Loader2 } from 'lucide-react'

import { cn } from '@/lib/utils'
import { apiClient } from '@/lib/api-client'

interface ProjectExplorerProps {
  level?: number
}

export function ProjectExplorer({ level = 1 }: ProjectExplorerProps) {
  const {
    data: projects = [],
    isLoading,
  } = useQuery({
    queryKey: ['projects'],
    queryFn: () => apiClient.listProjects(),
  })

  if (isLoading) {
    return (
      <div
        className={cn(
          'flex items-center gap-2 text-sm text-muted-foreground',
          level > 0 && 'ml-6'
        )}
      >
        <Loader2 className="h-4 w-4 animate-spin" />
        Loading projects...
      </div>
    )
  }

  if (projects.length === 0) {
    return (
      <div
        className={cn(
          'text-sm text-muted-foreground',
          level > 0 && 'ml-6 px-3 py-2'
        )}
      >
        No projects
      </div>
    )
  }

  return (
    <div className="space-y-1">
      {projects.map((project: any) => (
        <Link
          key={project.id}
          href={`/projects/${project.id}`}
          className={cn(
            'group flex items-center justify-between px-3 py-2 text-sm font-medium rounded-lg transition-colors',
            level > 0 && 'ml-6',
            'text-muted-foreground hover:text-foreground hover:bg-muted'
          )}
        >
          <div className="flex items-center gap-3">
            <FolderOpen className="h-3 w-3 flex-shrink-0" />
            <span className="truncate">{project.project_name}</span>
          </div>
        </Link>
      ))}
    </div>
  )
}

export default ProjectExplorer

