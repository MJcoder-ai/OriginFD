'use client'

import * as React from 'react'
import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'
import {
  FolderOpen,
  Loader2,
  ChevronRight,
  FileText,
  Layers,
  Database,
  CheckSquare,
  Sun,
  Battery,
  Zap
} from 'lucide-react'

import { cn } from '@/lib/utils'
import { apiClient } from '@/lib/api-client'

interface ProjectExplorerProps {
  level?: number
}

interface ProjectSubItem {
  name: string
  href: string
  icon: React.ElementType
}

const projectSubItems: ProjectSubItem[] = [
  { name: 'Canvases', href: '/canvases', icon: Layers },
  { name: 'Models', href: '/models', icon: Database },
  { name: 'Documents', href: '/documents', icon: FileText },
  { name: 'Reviews & Approvals', href: '/reviews', icon: CheckSquare },
]

export function ProjectExplorer({ level = 0 }: ProjectExplorerProps) {
  const [expandedProjects, setExpandedProjects] = React.useState<string[]>([])

  const {
    data: projects = [],
    isLoading,
  } = useQuery({
    queryKey: ['projects'],
    queryFn: () => apiClient.listProjects(),
  })

  const toggleProject = (projectId: string, e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setExpandedProjects(prev =>
      prev.includes(projectId)
        ? prev.filter(id => id !== projectId)
        : [...prev, projectId]
    )
  }

  const getDomainIcon = (domain: string) => {
    switch (domain) {
      case 'PV':
        return Sun
      case 'BESS':
        return Battery
      case 'HYBRID':
        return Zap
      default:
        return FolderOpen
    }
  }

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

  // Filter out legacy projects to avoid duplicates
  const uniqueProjects = projects.filter((project: any) =>
    !project.project_name.includes('(Legacy)')
  )

  return (
    <div className="space-y-1">
      {uniqueProjects.map((project: any) => {
        const isExpanded = expandedProjects.includes(project.id)
        const DomainIcon = getDomainIcon(project.domain)

        return (
          <div key={project.id}>
            {/* Project Header */}
            <div
              className={cn(
                'group flex items-center justify-between px-3 py-2 text-sm font-medium rounded-lg transition-colors cursor-pointer',
                level > 0 && 'ml-6',
                'text-muted-foreground hover:text-foreground hover:bg-muted'
              )}
              onClick={(e) => toggleProject(project.id, e)}
            >
              <div className="flex items-center gap-2">
                <ChevronRight
                  className={cn(
                    'h-3 w-3 flex-shrink-0 transition-transform',
                    isExpanded && 'rotate-90'
                  )}
                />
                <DomainIcon className="h-3 w-3 flex-shrink-0" />
                <span className="truncate">{project.project_name}</span>
              </div>
            </div>

            {/* Project Sub-items */}
            {isExpanded && (
              <div className="ml-6 space-y-1">
                {projectSubItems.map((subItem) => {
                  const SubIcon = subItem.icon
                  return (
                    <Link
                      key={subItem.name}
                      href={`/projects/${project.id}${subItem.href}`}
                      className={cn(
                        'group flex items-center gap-2 px-3 py-1.5 text-xs font-medium rounded-lg transition-colors',
                        'text-muted-foreground hover:text-foreground hover:bg-muted/50'
                      )}
                    >
                      <SubIcon className="h-3 w-3 flex-shrink-0" />
                      <span className="truncate">{subItem.name}</span>
                    </Link>
                  )
                })}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

export default ProjectExplorer