'use client'

import * as React from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { toast } from 'react-hot-toast'
import { Loader2, Sun, Battery, Zap, Grid3x3, Building, Home, Factory, Warehouse } from 'lucide-react'

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  Button,
  Input,
  Label,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Textarea,
} from '@originfd/ui'
import { apiClient } from '@/lib/api-client'
import type { DocumentCreateRequest, Domain, Scale } from '@/lib/api-client'

const newProjectSchema = z.object({
  project_name: z
    .string()
    .min(1, 'Project name is required')
    .max(255, 'Project name must be less than 255 characters')
    .regex(/^[a-zA-Z0-9\s\-_\.]+$/, 'Project name contains invalid characters'),
  domain: z.enum(['PV', 'BESS', 'HYBRID', 'GRID', 'MICROGRID'], {
    required_error: 'Please select a domain',
  }),
  scale: z.enum(['RESIDENTIAL', 'COMMERCIAL', 'INDUSTRIAL', 'UTILITY', 'HYPERSCALE'], {
    required_error: 'Please select a scale',
  }),
  description: z.string().optional(),
  location: z.string().optional(),
})

type NewProjectFormData = z.infer<typeof newProjectSchema>

interface NewProjectModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  defaultDomain?: string
}

const domainOptions = [
  {
    value: 'PV',
    label: 'Solar PV',
    description: 'Solar photovoltaic system',
    icon: Sun,
    color: 'text-yellow-600',
  },
  {
    value: 'BESS',
    label: 'Battery Storage',
    description: 'Battery energy storage system',
    icon: Battery,
    color: 'text-green-600',
  },
  {
    value: 'HYBRID',
    label: 'Hybrid System',
    description: 'Combined PV + BESS system',
    icon: Zap,
    color: 'text-purple-600',
  },
  {
    value: 'GRID',
    label: 'Grid Integration',
    description: 'Grid connection and compliance',
    icon: Grid3x3,
    color: 'text-blue-600',
  },
  {
    value: 'MICROGRID',
    label: 'Microgrid',
    description: 'Localized energy grid',
    icon: Grid3x3,
    color: 'text-indigo-600',
  },
]

const scaleOptions = [
  {
    value: 'RESIDENTIAL',
    label: 'Residential',
    description: 'Single-family homes, small buildings',
    icon: Home,
    range: '< 10 kW',
  },
  {
    value: 'COMMERCIAL',
    label: 'Commercial',
    description: 'Office buildings, retail spaces',
    icon: Building,
    range: '10 kW - 1 MW',
  },
  {
    value: 'INDUSTRIAL',
    label: 'Industrial',
    description: 'Factories, manufacturing facilities',
    icon: Factory,
    range: '1 MW - 10 MW',
  },
  {
    value: 'UTILITY',
    label: 'Utility Scale',
    description: 'Large-scale power generation',
    icon: Warehouse,
    range: '10 MW - 100 MW',
  },
  {
    value: 'HYPERSCALE',
    label: 'Hyperscale',
    description: 'Massive utility installations',
    icon: Warehouse,
    range: '> 100 MW',
  },
]

export function NewProjectModal({ open, onOpenChange, defaultDomain }: NewProjectModalProps) {
  const queryClient = useQueryClient()
  const router = useRouter()
  
  const form = useForm<NewProjectFormData>({
    resolver: zodResolver(newProjectSchema),
    defaultValues: {
      project_name: '',
      domain: defaultDomain as Domain || undefined,
      scale: undefined,
      description: '',
      location: '',
    },
  })

  const createProjectMutation = useMutation({
    mutationFn: async (data: NewProjectFormData) => {
      // Create a basic ODL document structure
      const documentData = {
        $schema: 'https://odl-sd.org/schemas/v4.1/document.json',
        schema_version: '4.1',
        meta: {
          project: data.project_name,
          domain: data.domain,
          scale: data.scale,
          units: {
            system: 'SI' as const,
            currency: 'USD',
            coordinate_system: 'EPSG:4326',
          },
          timestamps: {
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
          versioning: {
            document_version: '4.1.0',
            content_hash: 'initial',
          },
        },
        hierarchy: {
          type: 'PORTFOLIO' as const,
          id: 'portfolio-1',
          children: [],
          portfolio: {
            id: 'portfolio-1',
            name: data.project_name,
            total_capacity_gw: 0,
            regions: {},
          }
        },
        libraries: {},
        instances: [],
        connections: [],
        analysis: [],
        audit: [],
        data_management: {
          partitioning_enabled: false,
          external_refs_enabled: false,
          streaming_enabled: false,
          max_document_size_mb: 100,
        },
      }

      const request: DocumentCreateRequest = {
        project_name: data.project_name,
        domain: data.domain,
        scale: data.scale,
        document_data: documentData,
      }

      return apiClient.createDocument(request)
    },
    onSuccess: (data) => {
      toast.success('Project created successfully!')
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      onOpenChange(false)
      form.reset()
      // Navigate SPA-style
      router.push(`/projects/${data.id}`)
    },
    onError: (error: any) => {
      console.error('Failed to create project:', error)
      toast.error(error.message || 'Failed to create project')
    },
  })

  const onSubmit = (data: NewProjectFormData) => {
    createProjectMutation.mutate(data)
  }

  const selectedDomain = form.watch('domain')
  const selectedScale = form.watch('scale')


  return (
    <Dialog 
      open={open} 
      onOpenChange={onOpenChange}
    >
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>Create New Project</DialogTitle>
            <DialogDescription>
              Set up a new energy system project. Choose the domain and scale that best fits your requirements.
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            {/* Project Name */}
            <div className="space-y-2">
              <Label htmlFor="project_name">Project Name *</Label>
              <Input
                id="project_name"
                placeholder="Enter project name"
                {...form.register('project_name')}
              />
              {form.formState.errors.project_name && (
                <p className="text-sm text-red-600">
                  {form.formState.errors.project_name.message}
                </p>
              )}
            </div>

            {/* Domain Selection */}
            <div className="space-y-3">
              <Label>Domain *</Label>
              <Select
                value={selectedDomain}
                onValueChange={(value) => form.setValue('domain', value as any)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select system domain" />
                </SelectTrigger>
                <SelectContent>
                  {domainOptions.map((option) => {
                    const Icon = option.icon
                    return (
                      <SelectItem key={option.value} value={option.value}>
                        <div className="flex items-center space-x-2">
                          <Icon className={`h-4 w-4 ${option.color}`} />
                          <div>
                            <div className="font-medium">{option.label}</div>
                            <div className="text-xs text-muted-foreground">
                              {option.description}
                            </div>
                          </div>
                        </div>
                      </SelectItem>
                    )
                  })}
                </SelectContent>
              </Select>
              {form.formState.errors.domain && (
                <p className="text-sm text-red-600">
                  {form.formState.errors.domain.message}
                </p>
              )}
            </div>

            {/* Scale Selection */}
            <div className="space-y-3">
              <Label>Scale *</Label>
              <Select
                value={selectedScale}
                onValueChange={(value) => form.setValue('scale', value as any)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select project scale" />
                </SelectTrigger>
                <SelectContent>
                  {scaleOptions.map((option) => {
                    const Icon = option.icon
                    return (
                      <SelectItem key={option.value} value={option.value}>
                        <div className="flex items-center justify-between w-full">
                          <div className="flex items-center space-x-2">
                            <Icon className="h-4 w-4 text-muted-foreground" />
                            <div>
                              <div className="font-medium">{option.label}</div>
                              <div className="text-xs text-muted-foreground">
                                {option.description}
                              </div>
                            </div>
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {option.range}
                          </div>
                        </div>
                      </SelectItem>
                    )
                  })}
                </SelectContent>
              </Select>
              {form.formState.errors.scale && (
                <p className="text-sm text-red-600">
                  {form.formState.errors.scale.message}
                </p>
              )}
            </div>

            {/* Location */}
            <div className="space-y-2">
              <Label htmlFor="location">Location</Label>
              <Input
                id="location"
                placeholder="Enter project location (optional)"
                {...form.register('location')}
              />
            </div>

            {/* Description */}
            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                placeholder="Enter project description (optional)"
                rows={3}
                {...form.register('description')}
              />
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={createProjectMutation.isPending}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={createProjectMutation.isPending}
              >
                {createProjectMutation.isPending && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                Create Project
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
  )
}