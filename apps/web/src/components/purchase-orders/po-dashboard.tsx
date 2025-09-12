'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { PurchaseOrder, POStatus, ApprovalStep } from '@/lib/types'
import { 
  Card, 
  CardContent, 
  CardHeader, 
  CardTitle,
  Button,
  Badge,
  Input,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  Textarea,
  Label,
  Progress,
  Separator,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger
} from '@originfd/ui'
import {
  Search,
  Filter,
  FileText,
  CheckCircle,
  Clock,
  XCircle,
  DollarSign,
  Truck,
  Package,
  AlertCircle,
  Eye,
  Edit,
  Download,
  Send,
  User,
  Calendar,
  MapPin
} from 'lucide-react'

interface PODashboardProps {
  userRole?: 'procurement' | 'finance' | 'supplier' | 'admin'
}

const getStatusBadgeVariant = (status: POStatus) => {
  switch (status) {
    case 'draft': return 'secondary'
    case 'pending_approval': return 'secondary'
    case 'approved': return 'default'
    case 'sent_to_supplier': return 'default'
    case 'acknowledged': return 'default'
    case 'in_production': return 'default'
    case 'shipped': return 'default'
    case 'delivered': return 'default'
    case 'completed': return 'default'
    case 'cancelled': return 'destructive'
    case 'on_hold': return 'secondary'
    default: return 'outline'
  }
}

const getApprovalStepIcon = (status: ApprovalStep['status']) => {
  switch (status) {
    case 'approved': return CheckCircle
    case 'rejected': return XCircle
    case 'pending': return Clock
    default: return AlertCircle
  }
}

export default function PODashboard({ userRole = 'procurement' }: PODashboardProps) {
  const queryClient = useQueryClient()
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<POStatus | 'all'>('all')
  const [selectedPO, setSelectedPO] = useState<PurchaseOrder | null>(null)
  const [approvalDialogOpen, setApprovalDialogOpen] = useState(false)
  const [approvalAction, setApprovalAction] = useState<'approve' | 'reject'>('approve')
  const [approvalNotes, setApprovalNotes] = useState('')

  // Fetch Purchase Orders
  const { data: purchaseOrders = [], isLoading, error } = useQuery({
    queryKey: ['purchase-orders', statusFilter, searchTerm],
    queryFn: async () => {
      let url = '/api/bridge/purchase-orders'
      const params = new URLSearchParams()
      
      if (statusFilter !== 'all') params.append('status', statusFilter)
      if (searchTerm) params.append('search', searchTerm)
      
      if (params.toString()) url += `?${params.toString()}`
      
      const response = await fetch(url)
      if (!response.ok) throw new Error('Failed to fetch purchase orders')
      return response.json()
    }
  })

  // Approval mutation
  const approvalMutation = useMutation({
    mutationFn: async (data: {
      poId: string
      action: 'approve' | 'reject'
      notes: string
    }) => {
      const response = await fetch(`/api/bridge/purchase-orders/${data.poId}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          approver_id: 'current_user',
          approver_role: userRole,
          action: data.action,
          notes: data.notes
        })
      })
      if (!response.ok) throw new Error('Failed to process approval')
      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['purchase-orders'] })
      setApprovalDialogOpen(false)
      setSelectedPO(null)
      setApprovalNotes('')
    }
  })

  // Status update mutation
  const statusUpdateMutation = useMutation({
    mutationFn: async (data: {
      poId: string
      newStatus: POStatus
      notes: string
    }) => {
      const response = await fetch(`/api/bridge/purchase-orders/${data.poId}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          new_status: data.newStatus,
          updated_by: 'current_user',
          notes: data.notes
        })
      })
      if (!response.ok) throw new Error('Failed to update status')
      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['purchase-orders'] })
    }
  })

  const handleApproval = () => {
    if (!selectedPO) return
    
    approvalMutation.mutate({
      poId: selectedPO.id,
      action: approvalAction,
      notes: approvalNotes
    })
  }

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

  const getStatusStats = () => {
    return {
      total: purchaseOrders.length,
      draft: purchaseOrders.filter((po: PurchaseOrder) => po.status === 'draft').length,
      pending_approval: purchaseOrders.filter((po: PurchaseOrder) => po.status === 'pending_approval').length,
      approved: purchaseOrders.filter((po: PurchaseOrder) => po.status === 'approved').length,
      in_production: purchaseOrders.filter((po: PurchaseOrder) => po.status === 'in_production').length,
      shipped: purchaseOrders.filter((po: PurchaseOrder) => po.status === 'shipped').length,
      delivered: purchaseOrders.filter((po: PurchaseOrder) => po.status === 'delivered').length,
      total_value: purchaseOrders.reduce((sum: number, po: PurchaseOrder) => sum + po.pricing.total_amount, 0)
    }
  }

  const stats = getStatusStats()

  const getPendingApprovals = () => {
    return purchaseOrders.filter((po: PurchaseOrder) => 
      po.status === 'pending_approval' && 
      po.approval_workflow.current_step <= po.approval_workflow.required_approvals.length
    )
  }

  const filteredPurchaseOrders = purchaseOrders.filter((po: PurchaseOrder) => {
    if (statusFilter !== 'all' && po.status !== statusFilter) return false
    if (searchTerm && !po.po_number.toLowerCase().includes(searchTerm.toLowerCase()) &&
        !po.supplier.name.toLowerCase().includes(searchTerm.toLowerCase())) return false
    return true
  })

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
          <h1 className="text-3xl font-bold tracking-tight">Purchase Orders</h1>
          <p className="text-muted-foreground">
            Manage purchase orders and approval workflows
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
          {userRole === 'procurement' && (
            <Button size="sm">
              <FileText className="h-4 w-4 mr-2" />
              Create PO
            </Button>
          )}
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total POs</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Approval</CardTitle>
            <Clock className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">{stats.pending_approval}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">In Production</CardTitle>
            <Package className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{stats.in_production}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Shipped</CardTitle>
            <Truck className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-600">{stats.shipped}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Delivered</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{stats.delivered}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Value</CardTitle>
            <DollarSign className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {formatCurrency(stats.total_value)}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs defaultValue="all" className="space-y-4">
        <TabsList>
          <TabsTrigger value="all">All POs</TabsTrigger>
          <TabsTrigger value="pending">Pending Approval</TabsTrigger>
          <TabsTrigger value="active">Active Orders</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="all" className="space-y-4">
          {/* Filters */}
          <div className="flex items-center space-x-4">
            <div className="relative">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search POs..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-8 w-[300px]"
              />
            </div>
            <Select value={statusFilter} onValueChange={(value) => setStatusFilter(value as POStatus | 'all')}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="draft">Draft</SelectItem>
                <SelectItem value="pending_approval">Pending Approval</SelectItem>
                <SelectItem value="approved">Approved</SelectItem>
                <SelectItem value="sent_to_supplier">Sent to Supplier</SelectItem>
                <SelectItem value="acknowledged">Acknowledged</SelectItem>
                <SelectItem value="in_production">In Production</SelectItem>
                <SelectItem value="shipped">Shipped</SelectItem>
                <SelectItem value="delivered">Delivered</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline" size="sm">
              <Filter className="h-4 w-4 mr-2" />
              More Filters
            </Button>
          </div>

          {/* Purchase Orders Table */}
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>PO Number</TableHead>
                    <TableHead>Supplier</TableHead>
                    <TableHead>Component</TableHead>
                    <TableHead>Amount</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Delivery Date</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredPurchaseOrders.map((po: PurchaseOrder) => (
                    <TableRow key={po.id}>
                      <TableCell>
                        <div>
                          <div className="font-medium">{po.po_number}</div>
                          <div className="text-sm text-muted-foreground">
                            Created {formatDate(po.created_at)}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div>
                          <div className="font-medium">{po.supplier.name}</div>
                          <div className="text-sm text-muted-foreground">
                            {po.supplier.contact.email}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div>
                          <div className="font-medium">{po.component_details.component_name}</div>
                          <div className="text-sm text-muted-foreground">
                            {po.component_details.quantity_ordered.toLocaleString()} {po.component_details.unit_of_measure}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div>
                          <div className="font-medium">
                            {formatCurrency(po.pricing.total_amount, po.pricing.currency)}
                          </div>
                          <div className="text-sm text-muted-foreground">
                            {formatCurrency(po.component_details.unit_price, po.pricing.currency)}/unit
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant={getStatusBadgeVariant(po.status)}>
                          {po.status.replace('_', ' ')}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="text-sm">
                          {formatDate(po.order_details.requested_delivery_date)}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-2">
                          <Dialog>
                            <DialogTrigger asChild>
                              <Button variant="outline" size="sm">
                                <Eye className="h-4 w-4" />
                              </Button>
                            </DialogTrigger>
                            <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
                              <DialogHeader>
                                <DialogTitle>Purchase Order Details - {po.po_number}</DialogTitle>
                              </DialogHeader>
                              <div className="space-y-6">
                                {/* PO Overview */}
                                <div className="grid grid-cols-2 gap-6">
                                  <Card>
                                    <CardHeader>
                                      <CardTitle className="text-sm">Supplier Information</CardTitle>
                                    </CardHeader>
                                    <CardContent className="space-y-2 text-sm">
                                      <div><strong>Name:</strong> {po.supplier.name}</div>
                                      <div><strong>Contact:</strong> {po.supplier.contact.email}</div>
                                      <div><strong>Phone:</strong> {po.supplier.contact.phone}</div>
                                      <div><strong>Status:</strong> <Badge variant="outline">{po.supplier.status}</Badge></div>
                                    </CardContent>
                                  </Card>
                                  
                                  <Card>
                                    <CardHeader>
                                      <CardTitle className="text-sm">Order Details</CardTitle>
                                    </CardHeader>
                                    <CardContent className="space-y-2 text-sm">
                                      <div><strong>Order Date:</strong> {formatDate(po.order_details.order_date)}</div>
                                      <div><strong>Delivery Date:</strong> {formatDate(po.order_details.requested_delivery_date)}</div>
                                      <div><strong>Payment Terms:</strong> {po.pricing.payment_terms}</div>
                                      <div><strong>Shipping Terms:</strong> {po.order_details.shipping_terms}</div>
                                    </CardContent>
                                  </Card>
                                </div>

                                {/* Component Details */}
                                <Card>
                                  <CardHeader>
                                    <CardTitle className="text-sm">Component Details</CardTitle>
                                  </CardHeader>
                                  <CardContent>
                                    <div className="grid grid-cols-2 gap-4 text-sm">
                                      <div><strong>Component:</strong> {po.component_details.component_name}</div>
                                      <div><strong>Specification:</strong> {po.component_details.specification}</div>
                                      <div><strong>Quantity:</strong> {po.component_details.quantity_ordered.toLocaleString()} {po.component_details.unit_of_measure}</div>
                                      <div><strong>Unit Price:</strong> {formatCurrency(po.component_details.unit_price)}</div>
                                    </div>
                                  </CardContent>
                                </Card>

                                {/* Approval Workflow */}
                                <Card>
                                  <CardHeader>
                                    <CardTitle className="text-sm">Approval Workflow</CardTitle>
                                  </CardHeader>
                                  <CardContent>
                                    <div className="space-y-3">
                                      {po.approval_workflow.required_approvals.map((step, index) => {
                                        const StepIcon = getApprovalStepIcon(step.status)
                                        return (
                                          <div key={index} className="flex items-center space-x-3">
                                            <StepIcon className={`h-5 w-5 ${
                                              step.status === 'approved' ? 'text-green-600' :
                                              step.status === 'rejected' ? 'text-red-600' :
                                              step.status === 'pending' ? 'text-orange-500' :
                                              'text-gray-400'
                                            }`} />
                                            <div className="flex-1">
                                              <div className="text-sm font-medium">{step.approver_role}</div>
                                              {step.approved_at && (
                                                <div className="text-xs text-muted-foreground">
                                                  {step.status} on {formatDate(step.approved_at)}
                                                </div>
                                              )}
                                              {step.notes && (
                                                <div className="text-xs text-muted-foreground mt-1">
                                                  Note: {step.notes}
                                                </div>
                                              )}
                                            </div>
                                            <Badge variant={
                                              step.status === 'approved' ? 'default' :
                                              step.status === 'rejected' ? 'destructive' :
                                              step.status === 'pending' ? 'secondary' :
                                              'outline'
                                            }>
                                              {step.status}
                                            </Badge>
                                          </div>
                                        )
                                      })}
                                    </div>
                                  </CardContent>
                                </Card>

                                {/* Pricing Breakdown */}
                                <Card>
                                  <CardHeader>
                                    <CardTitle className="text-sm">Pricing Breakdown</CardTitle>
                                  </CardHeader>
                                  <CardContent className="space-y-2 text-sm">
                                    <div className="flex justify-between">
                                      <span>Subtotal:</span>
                                      <span>{formatCurrency(po.pricing.subtotal)}</span>
                                    </div>
                                    <div className="flex justify-between">
                                      <span>Tax:</span>
                                      <span>{formatCurrency(po.pricing.tax_amount)}</span>
                                    </div>
                                    <div className="flex justify-between">
                                      <span>Shipping:</span>
                                      <span>{formatCurrency(po.pricing.shipping_amount)}</span>
                                    </div>
                                    {po.pricing.discount_amount > 0 && (
                                      <div className="flex justify-between text-green-600">
                                        <span>Discount:</span>
                                        <span>-{formatCurrency(po.pricing.discount_amount)}</span>
                                      </div>
                                    )}
                                    <Separator />
                                    <div className="flex justify-between font-medium text-base">
                                      <span>Total:</span>
                                      <span>{formatCurrency(po.pricing.total_amount)}</span>
                                    </div>
                                  </CardContent>
                                </Card>
                              </div>
                            </DialogContent>
                          </Dialog>

                          {po.status === 'pending_approval' && (userRole === 'procurement' || userRole === 'finance') && (
                            <Dialog open={approvalDialogOpen && selectedPO?.id === po.id}>
                              <DialogTrigger asChild>
                                <Button
                                  size="sm"
                                  onClick={() => setSelectedPO(po)}
                                >
                                  Review
                                </Button>
                              </DialogTrigger>
                              <DialogContent>
                                <DialogHeader>
                                  <DialogTitle>Approve Purchase Order</DialogTitle>
                                </DialogHeader>
                                <div className="space-y-4">
                                  <div>
                                    <Label>PO Number</Label>
                                    <div className="text-sm text-muted-foreground">{po.po_number}</div>
                                  </div>
                                  
                                  <div>
                                    <Label>Action</Label>
                                    <Select value={approvalAction} onValueChange={(value) => setApprovalAction(value as 'approve' | 'reject')}>
                                      <SelectTrigger>
                                        <SelectValue />
                                      </SelectTrigger>
                                      <SelectContent>
                                        <SelectItem value="approve">Approve</SelectItem>
                                        <SelectItem value="reject">Reject</SelectItem>
                                      </SelectContent>
                                    </Select>
                                  </div>
                                  
                                  <div>
                                    <Label htmlFor="approvalNotes">Notes</Label>
                                    <Textarea
                                      id="approvalNotes"
                                      placeholder="Add your approval notes..."
                                      value={approvalNotes}
                                      onChange={(e) => setApprovalNotes(e.target.value)}
                                    />
                                  </div>
                                  
                                  <div className="flex justify-end space-x-2">
                                    <Button 
                                      variant="outline" 
                                      onClick={() => {
                                        setApprovalDialogOpen(false)
                                        setSelectedPO(null)
                                      }}
                                    >
                                      Cancel
                                    </Button>
                                    <Button 
                                      onClick={handleApproval}
                                      disabled={!approvalNotes.trim() || approvalMutation.isPending}
                                      variant={approvalAction === 'approve' ? 'default' : 'destructive'}
                                    >
                                      {approvalMutation.isPending ? 'Processing...' : 
                                       approvalAction === 'approve' ? 'Approve' : 'Reject'}
                                    </Button>
                                  </div>
                                </div>
                              </DialogContent>
                            </Dialog>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {filteredPurchaseOrders.length === 0 && (
                <div className="text-center py-8 text-muted-foreground">
                  <FileText className="mx-auto h-12 w-12 mb-4" />
                  <h3 className="text-lg font-medium">No Purchase Orders</h3>
                  <p>No purchase orders found matching your criteria.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="pending">
          <Card>
            <CardHeader>
              <CardTitle>Pending Approvals</CardTitle>
            </CardHeader>
            <CardContent>
              {getPendingApprovals().length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <CheckCircle className="mx-auto h-12 w-12 mb-4" />
                  <p>No pending approvals</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {getPendingApprovals().map((po: PurchaseOrder) => (
                    <div key={po.id} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-medium">{po.po_number}</h4>
                          <p className="text-sm text-muted-foreground">
                            {po.supplier.name} • {formatCurrency(po.pricing.total_amount)}
                          </p>
                        </div>
                        <Badge variant="secondary">
                          Step {po.approval_workflow.current_step} of {po.approval_workflow.required_approvals.length}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="active">
          <div className="text-center py-12 text-muted-foreground">
            <Package className="mx-auto h-12 w-12 mb-4" />
            <p>Active orders tracking coming soon...</p>
          </div>
        </TabsContent>

        <TabsContent value="analytics">
          <div className="text-center py-12 text-muted-foreground">
            <DollarSign className="mx-auto h-12 w-12 mb-4" />
            <p>Purchase order analytics coming soon...</p>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}