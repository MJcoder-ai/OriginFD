'use client'

import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { RFQRequest, RFQStatus, BidStatus } from '@/lib/types'
import RFQCreationWizard from './rfq-creation-wizard'
import { Card, CardContent, CardHeader, CardTitle, Badge, Button, Input, Select, SelectContent, SelectItem, SelectTrigger, SelectValue, Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@originfd/ui'
import {
  CalendarIcon,
  DollarSignIcon,
  PackageIcon,
  TruckIcon,
  BarChart3,
  AwardIcon
} from 'lucide-react'

const getStatusBadgeVariant = (status: RFQStatus) => {
  switch (status) {
    case 'draft': return 'secondary'
    case 'published': return 'outline'
    case 'receiving_bids': return 'default'
    case 'evaluation': return 'secondary'
    case 'awarded': return 'default'
    case 'completed': return 'default'
    case 'cancelled': return 'destructive'
    default: return 'outline'
  }
}

const getBidStatusBadgeVariant = (status: BidStatus) => {
  switch (status) {
    case 'submitted': return 'default'
    case 'shortlisted': return 'secondary'
    case 'awarded': return 'default'
    case 'rejected': return 'destructive'
    case 'withdrawn': return 'outline'
    default: return 'outline'
  }
}

interface RFQDashboardProps {
  userRole?: 'procurement' | 'supplier' | 'admin'
}

export default function RFQDashboard({ userRole = 'procurement' }: RFQDashboardProps) {
  const [filteredRFQs, setFilteredRFQs] = useState<RFQRequest[]>([])
  const [statusFilter, setStatusFilter] = useState<RFQStatus | 'all'>('all')
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedRFQ, setSelectedRFQ] = useState<RFQRequest | null>(null)
  const [createRFQOpen, setCreateRFQOpen] = useState(false)

  // Fetch RFQs using React Query
  const { data: rfqs = [], isLoading: loading, error } = useQuery({
    queryKey: ['rfqs', statusFilter],
    queryFn: async () => {
      const response = await fetch('/api/bridge/rfq')
      if (!response.ok) throw new Error('Failed to fetch RFQs')
      return response.json()
    }
  })

  useEffect(() => {
    let filtered = rfqs

    if (statusFilter !== 'all') {
      filtered = filtered.filter((rfq: any) => rfq.status === statusFilter)
    }

    if (searchTerm) {
      filtered = filtered.filter((rfq: any) =>
        rfq.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        rfq.description.toLowerCase().includes(searchTerm.toLowerCase())
      )
    }

    setFilteredRFQs(filtered)
  }, [rfqs, statusFilter, searchTerm])


  const getStatusStats = () => {
    return {
      total: rfqs.length,
      draft: rfqs.filter((r: any) => r.status === 'draft').length,
      receiving_bids: rfqs.filter((r: any) => r.status === 'receiving_bids').length,
      evaluation: rfqs.filter((r: any) => r.status === 'evaluation').length,
      awarded: rfqs.filter((r: any) => r.status === 'awarded').length,
      completed: rfqs.filter((r: any) => r.status === 'completed').length
    }
  }

  const stats = getStatusStats()

  const formatCurrency = (amount: number, currency: string = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency
    }).format(amount)
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  const getBestBid = (rfq: RFQRequest) => {
    if (rfq.bids.length === 0) return null
    return rfq.bids.reduce((best, current) =>
      current.evaluation_score && best.evaluation_score
        ? current.evaluation_score > best.evaluation_score ? current : best
        : current.total_price < best.total_price ? current : best
    )
  }

  if (loading) {
    return <div className="flex items-center justify-center h-64">Loading RFQs...</div>
  }

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <PackageIcon className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium">Total RFQs</p>
                <p className="text-2xl font-bold">{stats.total}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <CalendarIcon className="h-4 w-4 text-blue-500" />
              <div>
                <p className="text-sm font-medium">Receiving Bids</p>
                <p className="text-2xl font-bold text-blue-600">{stats.receiving_bids}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <BarChart3 className="h-4 w-4 text-yellow-500" />
              <div>
                <p className="text-sm font-medium">Under Evaluation</p>
                <p className="text-2xl font-bold text-yellow-600">{stats.evaluation}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <AwardIcon className="h-4 w-4 text-green-500" />
              <div>
                <p className="text-sm font-medium">Awarded</p>
                <p className="text-2xl font-bold text-green-600">{stats.awarded}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <TruckIcon className="h-4 w-4 text-purple-500" />
              <div>
                <p className="text-sm font-medium">Completed</p>
                <p className="text-2xl font-bold text-purple-600">{stats.completed}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <DollarSignIcon className="h-4 w-4 text-gray-500" />
              <div>
                <p className="text-sm font-medium">Draft</p>
                <p className="text-2xl font-bold text-gray-600">{stats.draft}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters and Actions */}
      <Card>
        <CardHeader>
          <CardTitle>RFQ Management</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col md:flex-row gap-4 mb-6">
            <Input
              placeholder="Search RFQs..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="md:max-w-sm"
            />
            <Select value={statusFilter} onValueChange={(value) => setStatusFilter(value as RFQStatus | 'all')}>
              <SelectTrigger className="md:max-w-sm">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="draft">Draft</SelectItem>
                <SelectItem value="published">Published</SelectItem>
                <SelectItem value="receiving_bids">Receiving Bids</SelectItem>
                <SelectItem value="evaluation">Under Evaluation</SelectItem>
                <SelectItem value="awarded">Awarded</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="cancelled">Cancelled</SelectItem>
              </SelectContent>
            </Select>
            {userRole === 'procurement' && (
              <Button onClick={() => setCreateRFQOpen(true)} className="ml-auto">
                Create New RFQ
              </Button>
            )}
          </div>

          {/* RFQ Table */}
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Title</TableHead>
                <TableHead>Component</TableHead>
                <TableHead>Quantity</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Deadline</TableHead>
                <TableHead>Bids</TableHead>
                <TableHead>Best Bid</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredRFQs.map((rfq) => {
                const bestBid = getBestBid(rfq)
                return (
                  <TableRow key={rfq.id}>
                    <TableCell>
                      <div>
                        <p className="font-medium">{rfq.title}</p>
                        <p className="text-sm text-muted-foreground truncate max-w-xs">
                          {rfq.description}
                        </p>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{rfq.component_id}</Badge>
                    </TableCell>
                    <TableCell>
                      {rfq.quantity.toLocaleString()} {rfq.unit_of_measure}
                    </TableCell>
                    <TableCell>
                      <Badge variant={getStatusBadgeVariant(rfq.status)}>
                        {rfq.status.replace('_', ' ')}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {formatDate(rfq.response_deadline)}
                    </TableCell>
                    <TableCell>
                      <span className="font-medium">{rfq.bids.length}</span>
                      {rfq.bids.length > 0 && (
                        <div className="text-xs text-muted-foreground">
                          {rfq.bids.filter(b => b.status === 'submitted').length} submitted
                        </div>
                      )}
                    </TableCell>
                    <TableCell>
                      {bestBid ? (
                        <div>
                          <p className="font-medium">
                            {formatCurrency(bestBid.unit_price)}
                          </p>
                          <p className="text-sm text-muted-foreground">
                            {bestBid.supplier_name}
                          </p>
                        </div>
                      ) : (
                        <span className="text-muted-foreground">No bids</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        <Button variant="outline" size="sm">
                          View
                        </Button>
                        {rfq.status === 'evaluation' && (
                          <Button size="sm">
                            Evaluate
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>

          {filteredRFQs.length === 0 && (
            <div className="text-center py-8 text-muted-foreground">
              No RFQs found matching your criteria.
            </div>
          )}
        </CardContent>
      </Card>

      {/* RFQ Creation Wizard */}
      <RFQCreationWizard
        open={createRFQOpen}
        onOpenChange={setCreateRFQOpen}
      />
    </div>
  )
}