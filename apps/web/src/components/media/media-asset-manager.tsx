'use client'

import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
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
  Separator,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger
} from '@originfd/ui'
import {
  FileText,
  Image,
  Video,
  Award,
  Upload,
  Download,
  Eye,
  Edit2,
  Trash2,
  Search,
  Filter,
  FileIcon,
  Calendar,
  User,
  HardDrive,
  Tag
} from 'lucide-react'

interface MediaAsset {
  id: string
  component_id: string
  type: 'datasheet' | 'warranty' | 'installation' | 'faq' | 'certificate' | 'test_report' | 'image' | 'video' | 'other'
  name: string
  description?: string
  file_url: string
  file_size: number
  file_type: string
  checksum: string
  uploaded_by: string
  uploaded_at: string
  version: number
  is_active: boolean
  tags: string[]
  metadata: Record<string, any>
}

interface MediaAssetManagerProps {
  componentId?: string
  readonly?: boolean
}

const getAssetTypeIcon = (type: string) => {
  switch (type) {
    case 'datasheet': return FileText
    case 'certificate': return Award
    case 'image': return Image
    case 'video': return Video
    case 'installation': return FileText
    case 'warranty': return FileIcon
    case 'test_report': return FileText
    case 'faq': return FileText
    default: return FileIcon
  }
}

const getAssetTypeBadgeVariant = (type: string) => {
  switch (type) {
    case 'datasheet': return 'default'
    case 'certificate': return 'default'
    case 'image': return 'secondary'
    case 'video': return 'secondary'
    case 'warranty': return 'outline'
    case 'installation': return 'outline'
    default: return 'outline'
  }
}

export default function MediaAssetManager({ componentId, readonly = false }: MediaAssetManagerProps) {
  const queryClient = useQueryClient()
  const [searchTerm, setSearchTerm] = useState('')
  const [typeFilter, setTypeFilter] = useState<string>('all')
  const [selectedAsset, setSelectedAsset] = useState<MediaAsset | null>(null)
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false)
  const [uploadForm, setUploadForm] = useState({
    type: 'datasheet',
    name: '',
    description: '',
    tags: '',
    component_id: componentId || ''
  })

  // Fetch media assets
  const { data: assetsData, isLoading, error } = useQuery({
    queryKey: ['media-assets', componentId, typeFilter],
    queryFn: async () => {
      let url = '/api/bridge/media'
      const params = new URLSearchParams()
      
      if (componentId) params.append('component_id', componentId)
      if (typeFilter !== 'all') params.append('type', typeFilter)
      params.append('active_only', 'true')
      
      if (params.toString()) url += `?${params.toString()}`
      
      const response = await fetch(url)
      if (!response.ok) throw new Error('Failed to fetch media assets')
      return response.json()
    }
  })

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: async (assetData: any) => {
      const response = await fetch('/api/bridge/media', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(assetData)
      })
      if (!response.ok) throw new Error('Failed to upload asset')
      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['media-assets'] })
      setUploadDialogOpen(false)
      setUploadForm({
        type: 'datasheet',
        name: '',
        description: '',
        tags: '',
        component_id: componentId || ''
      })
    }
  })

  const assets = assetsData?.assets || []
  const statistics = assetsData?.statistics || {}

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const filteredAssets = assets.filter((asset: MediaAsset) => {
    const matchesSearch = asset.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         asset.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         asset.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()))
    return matchesSearch
  })

  const handleUpload = () => {
    const tagsArray = uploadForm.tags.split(',').map(tag => tag.trim()).filter(Boolean)
    
    uploadMutation.mutate({
      ...uploadForm,
      tags: tagsArray,
      file_size: 1000000, // Mock file size
      file_type: uploadForm.type === 'image' ? 'image/jpeg' : 'application/pdf',
      uploaded_by: 'current_user'
    })
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p>Loading media assets...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Media Assets</h2>
          <p className="text-muted-foreground">
            Manage documents, images, and other media files
          </p>
        </div>
        {!readonly && (
          <Button onClick={() => setUploadDialogOpen(true)}>
            <Upload className="h-4 w-4 mr-2" />
            Upload Asset
          </Button>
        )}
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <FileIcon className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium">Total Assets</p>
                <p className="text-2xl font-bold">{statistics.active_assets || 0}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <HardDrive className="h-4 w-4 text-blue-500" />
              <div>
                <p className="text-sm font-medium">Total Size</p>
                <p className="text-2xl font-bold text-blue-600">
                  {formatFileSize(statistics.total_size || 0)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Image className="h-4 w-4 text-green-500" />
              <div>
                <p className="text-sm font-medium">Images</p>
                <p className="text-2xl font-bold text-green-600">
                  {statistics.by_type?.image || 0}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <FileText className="h-4 w-4 text-purple-500" />
              <div>
                <p className="text-sm font-medium">Documents</p>
                <p className="text-2xl font-bold text-purple-600">
                  {(statistics.by_type?.datasheet || 0) + 
                   (statistics.by_type?.certificate || 0) + 
                   (statistics.by_type?.installation || 0)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Media Library</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col md:flex-row gap-4 mb-6">
            <div className="relative flex-1">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search assets..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-8"
              />
            </div>
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Filter by type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="datasheet">Datasheets</SelectItem>
                <SelectItem value="certificate">Certificates</SelectItem>
                <SelectItem value="image">Images</SelectItem>
                <SelectItem value="video">Videos</SelectItem>
                <SelectItem value="installation">Installation</SelectItem>
                <SelectItem value="warranty">Warranty</SelectItem>
                <SelectItem value="test_report">Test Reports</SelectItem>
                <SelectItem value="other">Other</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Asset</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Size</TableHead>
                <TableHead>Version</TableHead>
                <TableHead>Uploaded</TableHead>
                <TableHead>Tags</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredAssets.map((asset: MediaAsset) => {
                const Icon = getAssetTypeIcon(asset.type)
                
                return (
                  <TableRow key={asset.id}>
                    <TableCell>
                      <div className="flex items-center space-x-3">
                        <Icon className="h-5 w-5 text-muted-foreground" />
                        <div>
                          <p className="font-medium">{asset.name}</p>
                          {asset.description && (
                            <p className="text-sm text-muted-foreground truncate max-w-xs">
                              {asset.description}
                            </p>
                          )}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={getAssetTypeBadgeVariant(asset.type)}>
                        {asset.type}
                      </Badge>
                    </TableCell>
                    <TableCell>{formatFileSize(asset.file_size)}</TableCell>
                    <TableCell>
                      <Badge variant="outline">v{asset.version}</Badge>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm">
                        <p>{formatDate(asset.uploaded_at)}</p>
                        <p className="text-muted-foreground">by {asset.uploaded_by}</p>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {asset.tags.slice(0, 2).map((tag, index) => (
                          <Badge key={index} variant="secondary" className="text-xs">
                            {tag}
                          </Badge>
                        ))}
                        {asset.tags.length > 2 && (
                          <Badge variant="secondary" className="text-xs">
                            +{asset.tags.length - 2}
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => setSelectedAsset(asset)}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => window.open(asset.file_url, '_blank')}
                        >
                          <Download className="h-4 w-4" />
                        </Button>
                        {!readonly && (
                          <Button variant="outline" size="sm">
                            <Edit2 className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>

          {filteredAssets.length === 0 && (
            <div className="text-center py-8 text-muted-foreground">
              <FileIcon className="h-16 w-16 mx-auto mb-4 text-muted-foreground/50" />
              <p>No media assets found matching your criteria.</p>
              {!readonly && (
                <Button onClick={() => setUploadDialogOpen(true)} className="mt-4">
                  <Upload className="h-4 w-4 mr-2" />
                  Upload First Asset
                </Button>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Upload Dialog */}
      <Dialog open={uploadDialogOpen} onOpenChange={setUploadDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Upload Media Asset</DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            <div>
              <Label htmlFor="asset_type">Asset Type</Label>
              <Select value={uploadForm.type} onValueChange={(value) => setUploadForm(prev => ({ ...prev, type: value }))}>
                <SelectTrigger>
                  <SelectValue placeholder="Select asset type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="datasheet">Datasheet</SelectItem>
                  <SelectItem value="certificate">Certificate</SelectItem>
                  <SelectItem value="image">Image</SelectItem>
                  <SelectItem value="video">Video</SelectItem>
                  <SelectItem value="installation">Installation Guide</SelectItem>
                  <SelectItem value="warranty">Warranty Document</SelectItem>
                  <SelectItem value="test_report">Test Report</SelectItem>
                  <SelectItem value="other">Other</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="asset_name">File Name</Label>
              <Input
                id="asset_name"
                value={uploadForm.name}
                onChange={(e) => setUploadForm(prev => ({ ...prev, name: e.target.value }))}
                placeholder="Example_Datasheet.pdf"
              />
            </div>

            <div>
              <Label htmlFor="asset_description">Description</Label>
              <Textarea
                id="asset_description"
                value={uploadForm.description}
                onChange={(e) => setUploadForm(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Brief description of the asset..."
                rows={3}
              />
            </div>

            <div>
              <Label htmlFor="asset_tags">Tags (comma-separated)</Label>
              <Input
                id="asset_tags"
                value={uploadForm.tags}
                onChange={(e) => setUploadForm(prev => ({ ...prev, tags: e.target.value }))}
                placeholder="datasheet, technical-specs, v2.1"
              />
            </div>

            {!componentId && (
              <div>
                <Label htmlFor="component_id">Component ID</Label>
                <Input
                  id="component_id"
                  value={uploadForm.component_id}
                  onChange={(e) => setUploadForm(prev => ({ ...prev, component_id: e.target.value }))}
                  placeholder="comp_001"
                />
              </div>
            )}
          </div>

          <div className="flex justify-end gap-4 mt-6">
            <Button 
              variant="outline" 
              onClick={() => setUploadDialogOpen(false)}
              disabled={uploadMutation.isPending}
            >
              Cancel
            </Button>
            <Button 
              onClick={handleUpload}
              disabled={uploadMutation.isPending || !uploadForm.name || !uploadForm.component_id}
            >
              {uploadMutation.isPending ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4 mr-2" />
                  Upload Asset
                </>
              )}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Asset Detail Dialog */}
      {selectedAsset && (
        <Dialog open={!!selectedAsset} onOpenChange={() => setSelectedAsset(null)}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>{selectedAsset.name}</DialogTitle>
            </DialogHeader>
            
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-sm font-medium text-muted-foreground">Type</Label>
                  <p>{selectedAsset.type}</p>
                </div>
                <div>
                  <Label className="text-sm font-medium text-muted-foreground">Size</Label>
                  <p>{formatFileSize(selectedAsset.file_size)}</p>
                </div>
                <div>
                  <Label className="text-sm font-medium text-muted-foreground">Version</Label>
                  <p>v{selectedAsset.version}</p>
                </div>
                <div>
                  <Label className="text-sm font-medium text-muted-foreground">Component</Label>
                  <p>{selectedAsset.component_id}</p>
                </div>
              </div>
              
              {selectedAsset.description && (
                <div>
                  <Label className="text-sm font-medium text-muted-foreground">Description</Label>
                  <p>{selectedAsset.description}</p>
                </div>
              )}

              {selectedAsset.tags.length > 0 && (
                <div>
                  <Label className="text-sm font-medium text-muted-foreground">Tags</Label>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {selectedAsset.tags.map((tag, index) => (
                      <Badge key={index} variant="secondary">{tag}</Badge>
                    ))}
                  </div>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-sm font-medium text-muted-foreground">Uploaded</Label>
                  <p>{formatDate(selectedAsset.uploaded_at)}</p>
                </div>
                <div>
                  <Label className="text-sm font-medium text-muted-foreground">Uploaded by</Label>
                  <p>{selectedAsset.uploaded_by}</p>
                </div>
              </div>

              <div className="flex justify-end gap-4">
                <Button variant="outline" onClick={() => setSelectedAsset(null)}>
                  Close
                </Button>
                <Button onClick={() => window.open(selectedAsset.file_url, '_blank')}>
                  <Download className="h-4 w-4 mr-2" />
                  Download
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  )
}