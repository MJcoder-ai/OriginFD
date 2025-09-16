'use client'

import * as React from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Plus,
  Search,
  Filter,
  MoreHorizontal,
  CheckCircle,
  Clock,
  XCircle,
  Building,
  Mail,
  Phone,
  MapPin,
  Award
} from 'lucide-react'

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

// Mock API for now - replace with real API client
const suppliersAPI = {
  async listSuppliers(params?: any) {
    // Mock data
    return {
      suppliers: [
        {
          id: '1',
          supplier_id: 'SUP-ABC123',
          name: 'Tesla Energy',
          contact: {
            email: 'procurement@tesla.com',
            phone: '+1-555-0123',
            address: 'Austin, TX, USA'
          },
          status: 'approved',
          capabilities: {
            categories: ['storage', 'conversion'],
            certifications: ['UL', 'CE', 'FCC']
          },
          created_at: '2024-01-15T10:00:00Z'
        },
        {
          id: '2',
          supplier_id: 'SUP-DEF456',
          name: 'JinkoSolar',
          contact: {
            email: 'sales@jinkosolar.com',
            phone: '+86-21-5180-8888',
            address: 'Shanghai, China'
          },
          status: 'approved',
          capabilities: {
            categories: ['generation'],
            certifications: ['IEC', 'UL', 'TUV']
          },
          created_at: '2024-01-10T14:30:00Z'
        },
        {
          id: '3',
          supplier_id: 'SUP-GHI789',
          name: 'SMA Solar Technology',
          contact: {
            email: 'info@sma.de',
            phone: '+49-561-9522-0',
            address: 'Niestetal, Germany'
          },
          status: 'draft',
          capabilities: {
            categories: ['conversion', 'monitoring'],
            certifications: ['CE', 'VDE', 'UL']
          },
          created_at: '2024-01-20T09:15:00Z'
        }
      ],
      total: 3,
      page: 1,
      page_size: 20
    }
  },

  async getStats() {
    return {
      total_suppliers: 15,
      approved_suppliers: 12,
      draft_suppliers: 3,
      active_rfqs: 2
    }
  }
}

const statusColors = {
  approved: 'bg-green-100 text-green-800 border-green-200',
  draft: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  inactive: 'bg-red-100 text-red-800 border-red-200'
}

const statusIcons = {
  approved: CheckCircle,
  draft: Clock,
  inactive: XCircle
}

export default function SuppliersPage() {
  const [searchQuery, setSearchQuery] = React.useState('')
  const [statusFilter, setStatusFilter] = React.useState<string>('')
  const [page, setPage] = React.useState(1)

  // Fetch suppliers
  const {
    data: suppliersData,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['suppliers', page, searchQuery, statusFilter],
    queryFn: () => suppliersAPI.listSuppliers({
      page,
      page_size: 20,
      search: searchQuery || undefined,
      status: statusFilter || undefined
    }),
  })

  // Fetch supplier stats
  const { data: stats } = useQuery({
    queryKey: ['supplier-stats'],
    queryFn: () => suppliersAPI.getStats(),
  })

  const suppliers = suppliersData?.suppliers || []
  const totalSuppliers = suppliersData?.total || 0

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  const getStatusIcon = (status: string) => {
    const Icon = statusIcons[status as keyof typeof statusIcons] || Clock
    return Icon
  }

  const getStatusColor = (status: string) => {
    return statusColors[status as keyof typeof statusColors] || statusColors.draft
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Supplier Management</h1>
          <p className="text-muted-foreground">
            Manage your supplier network and procurement relationships
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm">
            <Filter className="h-4 w-4 mr-2" />
            Import
          </Button>
          <Button className="gap-2">
            <Plus className="h-4 w-4" />
            Add Supplier
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Suppliers</CardTitle>
              <Building className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_suppliers}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Approved Suppliers</CardTitle>
              <CheckCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.approved_suppliers}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Pending Approval</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.draft_suppliers}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active RFQs</CardTitle>
              <Award className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.active_rfqs}</div>
            </CardContent>
          </Card>
        </div>
      )}

      <Tabs defaultValue="suppliers" className="space-y-6">
        <TabsList>
          <TabsTrigger value="suppliers">Suppliers</TabsTrigger>
          <TabsTrigger value="rfqs">RFQs</TabsTrigger>
          <TabsTrigger value="orders">Purchase Orders</TabsTrigger>
        </TabsList>

        <TabsContent value="suppliers" className="space-y-6">
          {/* Filters and Search */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="relative">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search suppliers..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-8 w-[300px]"
                />
              </div>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[140px]">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Status</SelectItem>
                  <SelectItem value="approved">Approved</SelectItem>
                  <SelectItem value="draft">Draft</SelectItem>
                  <SelectItem value="inactive">Inactive</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Suppliers List */}
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <p className="text-muted-foreground">Error loading suppliers. Please try again.</p>
            </div>
          ) : suppliers.length === 0 ? (
            <div className="text-center py-12">
              <Building className="mx-auto h-12 w-12 text-muted-foreground" />
              <h3 className="mt-2 text-sm font-semibold text-gray-900">No suppliers</h3>
              <p className="mt-1 text-sm text-muted-foreground">
                Get started by adding your first supplier.
              </p>
              <div className="mt-6">
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  Add Supplier
                </Button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {suppliers.map((supplier) => {
                const StatusIcon = getStatusIcon(supplier.status)

                return (
                  <Card key={supplier.id} className="cursor-pointer hover:shadow-md transition-shadow">
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                          <div className="p-3 rounded-lg bg-muted">
                            <Building className="h-6 w-6" />
                          </div>
                          <div>
                            <div className="flex items-center space-x-2">
                              <h3 className="font-semibold text-lg">{supplier.name}</h3>
                              <Badge variant="outline" className={getStatusColor(supplier.status)}>
                                <StatusIcon className="h-3 w-3 mr-1" />
                                {supplier.status}
                              </Badge>
                            </div>
                            <p className="text-sm text-muted-foreground font-mono">
                              {supplier.supplier_id}
                            </p>
                            <div className="flex items-center space-x-4 mt-2">
                              {supplier.contact.email && (
                                <div className="flex items-center text-sm text-muted-foreground">
                                  <Mail className="h-3 w-3 mr-1" />
                                  {supplier.contact.email}
                                </div>
                              )}
                              {supplier.contact.phone && (
                                <div className="flex items-center text-sm text-muted-foreground">
                                  <Phone className="h-3 w-3 mr-1" />
                                  {supplier.contact.phone}
                                </div>
                              )}
                              {supplier.contact.address && (
                                <div className="flex items-center text-sm text-muted-foreground">
                                  <MapPin className="h-3 w-3 mr-1" />
                                  {supplier.contact.address}
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center space-x-4">
                          <div className="text-right">
                            <div className="text-sm text-muted-foreground">Capabilities</div>
                            <div className="flex flex-wrap gap-1 mt-1">
                              {supplier.capabilities?.categories?.map((category: string) => (
                                <Badge key={category} variant="secondary" className="text-xs">
                                  {category}
                                </Badge>
                              ))}
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-sm text-muted-foreground">Added</div>
                            <div className="text-sm">{formatDate(supplier.created_at)}</div>
                          </div>
                          <Button variant="ghost" size="sm">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          )}

          {/* Pagination */}
          {totalSuppliers > 20 && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                Showing {((page - 1) * 20) + 1} to {Math.min(page * 20, totalSuppliers)} of {totalSuppliers} suppliers
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
                  disabled={page * 20 >= totalSuppliers}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </TabsContent>

        <TabsContent value="rfqs" className="space-y-6">
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <Award className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">RFQ Management</h3>
              <p className="text-sm text-muted-foreground text-center mb-4">
                Create and manage Request for Quotations
              </p>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Create RFQ
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="orders" className="space-y-6">
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <Building className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">Purchase Orders</h3>
              <p className="text-sm text-muted-foreground text-center mb-4">
                Track and manage purchase orders
              </p>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Create Purchase Order
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
