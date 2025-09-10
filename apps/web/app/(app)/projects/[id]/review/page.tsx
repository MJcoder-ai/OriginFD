
'use client'

import React from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useQuery, useMutation } from '@tanstack/react-query'
import { apiClient } from '@/lib/api-client'
import { Button, Card, CardContent, CardHeader, CardTitle } from '@originfd/ui'

export default function ProjectReviewPage() {
  const params = useParams()
  const router = useRouter()
  const projectId = params.id as string

  const { data, isLoading, error } = useQuery({
    queryKey: ['project-review', projectId],
    queryFn: () => apiClient.getProjectReview(projectId),
    enabled: !!projectId,
  })

  const approval = useMutation({
    mutationFn: (approved: boolean) => apiClient.submitApproval(projectId, approved),
    onSuccess: () => router.push(`/projects/${projectId}`),
  })

  if (isLoading) return <div>Loading review...</div>
  if (error) return <div>Failed to load review.</div>

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Review Changes</h1>
      {data &&
        Object.entries<any>(data.diff).map(([section, ops]) => (
          <Card key={section}>
            <CardHeader>
              <CardTitle className="capitalize">{section}</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="list-disc pl-4 space-y-1">
                {ops.map((op: any, i: number) => (
                  <li key={i}>
                    {op.op} {op.path}{' '}
                    {op.value !== undefined ? `-> ${JSON.stringify(op.value)}` : ''}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        ))}
      {data && data.kpi_deltas && (
        <Card>
          <CardHeader>
            <CardTitle>KPI Deltas</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="list-disc pl-4 space-y-1">
              {Object.entries<any>(data.kpi_deltas).map(([k, v]) => (
                <li key={k}>
                  {k}: {v}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
      <div className="flex gap-2">
        <Button onClick={() => approval.mutate(true)} disabled={approval.isLoading}>
          Approve
        </Button>
        <Button
          onClick={() => approval.mutate(false)}
          variant="destructive"
          disabled={approval.isLoading}
        >
          Reject
        </Button>
      </div>
    </div>
  )
}
