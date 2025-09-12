'use client'

import * as React from 'react'
import { useParams } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { Plus, Search, Filter, CheckSquare, Clock, User, MoreHorizontal, Eye } from 'lucide-react'
import { apiClient } from '@/lib/api-client'
import { Button, Card, CardContent, CardDescription, CardHeader, CardTitle } from '@originfd/ui'
import ReviewActions from '@/components/projects/review-actions'
import { LifecycleJourney } from '@/components/projects/lifecycle-journey'

export default function ProjectReviewsPage() {
  const params = useParams()
  const projectId = params.id as string

  // Fetch project details
  const { data: project, isLoading: projectLoading } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => apiClient.getProject(projectId),
  })

  // Mock reviews data for now
  const reviews = [
    {
      id: 'review-1',
      title: 'Design Review - Phase 1',
      description: 'Initial system design and layout review',
      status: 'Completed',
      priority: 'High',
      assignee: 'Sarah Johnson',
      reviewer: 'Mike Chen',
      dueDate: '2024-01-25T00:00:00Z',
      completedDate: '2024-01-20T15:45:00Z',
      comments: 12,
      type: 'Design Review',
    },
    {
      id: 'review-2', 
      title: 'Safety Compliance Check',
      description: 'Review safety protocols and regulatory compliance',
      status: 'In Progress',
      priority: 'Critical',
      assignee: 'David Wilson',
      reviewer: 'Lisa Rodriguez',
      dueDate: '2024-01-28T00:00:00Z',
      completedDate: null,
      comments: 5,
      type: 'Compliance Review',
    },
    {
      id: 'review-3',
      title: 'Cost Analysis Approval',
      description: 'Financial review and budget approval process',
      status: 'Pending',
      priority: 'Medium',
      assignee: 'Emma Taylor',
      reviewer: 'Robert Kim',
      dueDate: '2024-02-01T00:00:00Z',
      completedDate: null,
      comments: 2,
      type: 'Financial Review',
    },
    {
      id: 'review-4',
      title: 'Technical Specifications',
      description: 'Review of technical specifications and requirements',
      status: 'Approved',
      priority: 'High',
      assignee: 'Alex Brown',
      reviewer: 'Jennifer Wu',
      dueDate: '2024-01-22T00:00:00Z',
      completedDate: '2024-01-21T10:30:00Z',
      comments: 8,
      type: 'Technical Review',
    },
  ]

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Completed':
      case 'Approved':
        return 'bg-green-100 text-green-800 border-green-200'
      case 'In Progress':
        return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'Pending':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'Rejected':
        return 'bg-red-100 text-red-800 border-red-200'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'Critical':
        return 'bg-red-100 text-red-800 border-red-200'
      case 'High':
        return 'bg-orange-100 text-orange-800 border-orange-200'
      case 'Medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'Low':
        return 'bg-green-100 text-green-800 border-green-200'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'Completed':
      case 'Approved':
        return <CheckSquare className="h-5 w-5 text-green-600" />
      case 'In Progress':
        return <Clock className="h-5 w-5 text-blue-600" />
      default:
        return <CheckSquare className="h-5 w-5 text-gray-600" />
    }
  }

  if (projectLoading) {
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
          <h1 className="text-3xl font-bold tracking-tight">Reviews & Approvals</h1>
          <p className="text-muted-foreground">
            Review workflow and approval processes for {project?.project_name}
          </p>
        </div>
        <Button className="gap-2">
          <Plus className="h-4 w-4" />
          New Review
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

      {/* Project Lifecycle Journey */}
      <Card>
        <CardHeader>
          <CardTitle>Project Lifecycle</CardTitle>
          <CardDescription>
            Track the progress of your project through different phases
          </CardDescription>
        </CardHeader>
        <CardContent>
          <LifecycleJourney projectId={projectId} />
        </CardContent>
      </Card>

      {/* Reviews Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {reviews.map((review) => (
          <Card
            key={review.id}
            className="cursor-pointer hover:shadow-md transition-shadow"
          >
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-3">
                  <div className="p-2 rounded-lg bg-muted">
                    {getStatusIcon(review.status)}
                  </div>
                  <div className="flex-1">
                    <CardTitle className="text-lg">{review.title}</CardTitle>
                    <div className="flex items-center gap-2 mt-1">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${getStatusColor(review.status)}`}>
                        {review.status}
                      </span>
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${getPriorityColor(review.priority)}`}>
                        {review.priority}
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
                <p className="text-sm text-muted-foreground">
                  {review.description}
                </p>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Type</span>
                  <span>{review.type}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Assignee</span>
                  <span>{review.assignee}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Reviewer</span>
                  <span>{review.reviewer}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Due Date</span>
                  <span>{formatDate(review.dueDate)}</span>
                </div>
                {review.completedDate && (
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Completed</span>
                    <span>{formatDate(review.completedDate)}</span>
                  </div>
                )}
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Comments</span>
                  <span>{review.comments}</span>
                </div>
                <div className="flex gap-2 pt-2">
                  <Button size="sm" variant="outline" className="flex-1">
                    <Eye className="h-3 w-3 mr-1" />
                    View
                  </Button>
                  <Button size="sm" className="flex-1">
                    Review
                  </Button>
                </div>
                
                {/* Review Actions Component */}
                <ReviewActions 
                  projectId={projectId}
                  source={review.assignee}
                  target={review.reviewer}
                />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Empty state if no reviews */}
      {reviews.length === 0 && (
        <div className="text-center py-12">
          <div className="max-w-md mx-auto">
            <div className="text-muted-foreground mb-4">
              <CheckSquare className="h-12 w-12 mx-auto" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No reviews yet</h3>
            <p className="text-muted-foreground mb-4">
              Create your first review to start the approval process.
            </p>
            <Button className="gap-2">
              <Plus className="h-4 w-4" />
              New Review
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}