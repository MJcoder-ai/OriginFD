'use client'

import * as React from 'react'
import { useParams } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api-client'
import { Button, ErrorBoundary, LoadingSpinner } from '@originfd/ui'
import { Layers, Map, Download, Settings, ChevronLeft, ChevronRight, ZoomIn, ZoomOut, Grid3x3, Maximize2, RotateCcw, Keyboard, Navigation } from 'lucide-react'
import { SLDCanvas } from '@/components/canvas/sld-canvas'
import { SiteCanvas } from '@/components/canvas/site-canvas'
import { CanvasBusProvider } from '@/components/canvas/bus'
import { LayersPanel, LayerKey } from '@/components/canvas/layers-panel'
import { InspectorPanel } from '@/components/canvas/inspector-panel'
import { exportCanvasSVGToPDF } from '@/components/canvas/export-pdf'

export default function CanvasPage() {
  const params = useParams()
  const projectId = params.id as string
  const canvasId = params.canvasId as string

  const { data: doc, isLoading, error } = useQuery({
    queryKey: ['project-document', projectId],
    queryFn: () => apiClient.getPrimaryProjectDocument(projectId),
    enabled: !!projectId,
  })

  const type = canvasId?.startsWith('sld') ? 'sld' : 'site'
  const [layers, setLayers] = React.useState<LayerKey[]>(type === 'sld' ? ['ac', 'dc'] : ['equipment', 'routes', 'civil'])
  const [showInspector, setShowInspector] = React.useState(true)
  const [showGrid, setShowGrid] = React.useState(false)
  const [showShortcuts, setShowShortcuts] = React.useState(false)
  const [zoom, setZoom] = React.useState(100)
  const containerRef = React.useRef<HTMLDivElement | null>(null)
  // Keyboard shortcuts
  React.useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key.toLowerCase() === 'g') setShowGrid((v) => !v)
      if (e.key.toLowerCase() === 'i') setShowInspector((v) => !v)
      if ((e.ctrlKey || e.metaKey) && (e.key === '+' || e.key === '=')) {
        e.preventDefault()
        setZoom((z) => Math.min(200, z + 25))
      }
      if ((e.ctrlKey || e.metaKey) && e.key === '-') {
        e.preventDefault()
        setZoom((z) => Math.max(25, z - 25))
      }
      if ((e.ctrlKey || e.metaKey) && e.key === '0') {
        e.preventDefault()
        setZoom(100)
      }
      if (e.key === '?') setShowShortcuts((v) => !v)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  return (
    <div className="h-screen flex flex-col bg-background">
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center">
          <LoadingSpinner />
        </div>
      )}
      {!!error && (
        <div className="absolute inset-0 flex items-center justify-center text-muted-foreground">
          Failed to load project document.
        </div>
      )}
      {/* Compact Top Toolbar */}
      <div className="flex items-center justify-center px-4 py-1.5 bg-card border-b border-border shadow-sm relative">
        <div className="flex items-center gap-4">
          {type === 'sld' ? <Layers className="h-4 w-4 text-blue-600" /> : <Map className="h-4 w-4 text-green-600" />}
          <span className="text-sm font-medium text-foreground">
            {type === 'sld' ? 'Single Line Diagram' : 'Site Layout'}
          </span>
          <div className="h-4 w-px bg-border mx-3" />
          <LayersPanel active={layers} onChange={setLayers} />
        </div>
        
        <div className="absolute right-4 flex items-center gap-2">
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={() => setShowShortcuts(!showShortcuts)}
            title="Keyboard Shortcuts"
          >
            <Keyboard className="h-4 w-4" />
          </Button>
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={() => setShowInspector(!showInspector)}
            title="Toggle Inspector"
          >
            <Settings className="h-4 w-4" />
          </Button>
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={async () => {
              if (!containerRef.current) return
              await exportCanvasSVGToPDF(containerRef.current, `${type}-${canvasId}.pdf`)
            }}
            title="Export PDF"
          >
            <Download className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Main Canvas Area */}
      <div className="flex flex-1 overflow-hidden">
        {/* Canvas Container */}
        <div className="flex-1 relative bg-card" ref={containerRef}>
          {/* Canvas Grid Overlay */}
          {showGrid && (
            <div 
              className="absolute inset-0 pointer-events-none opacity-20"
              style={{
                backgroundImage: `url("data:image/svg+xml,%3csvg width='20' height='20' xmlns='http://www.w3.org/2000/svg'%3e%3cdefs%3e%3cpattern id='grid' width='20' height='20' patternUnits='userSpaceOnUse'%3e%3cpath d='M 20 0 L 0 0 0 20' fill='none' stroke='%23d1d5db' stroke-width='1'/%3e%3c/pattern%3e%3c/defs%3e%3crect width='100%25' height='100%25' fill='url(%23grid)' /%3e%3c/svg%3e")`,
              }}
            />
          )}

          <ErrorBoundary>
            <CanvasBusProvider>
              {type === 'sld' ? (
                <SLDCanvas 
                  projectId={projectId} 
                  document={doc} 
                  scope={canvasId.replace('sld-', '')} 
                  activeLayers={layers.filter((l): l is 'ac'|'dc' => l === 'ac' || l === 'dc')} 
                />
              ) : (
                <SiteCanvas projectId={projectId} document={doc} activeLayers={layers} />
              )}
            </CanvasBusProvider>
          </ErrorBoundary>

          {/* Floating Canvas Info */}
          <div className="absolute bottom-4 left-4 bg-card/95 backdrop-blur-sm rounded-lg border border-border px-3 py-2 text-xs text-muted-foreground shadow-md z-10">
            <div className="flex items-center gap-3">
              <span className="font-medium">Zoom: {zoom}%</span>
              <span className="text-muted-foreground/60">•</span>
              <span>Layers: {layers.length}</span>
              <span className="text-muted-foreground">•</span>
              <span className="text-primary font-medium">{type === 'sld' ? 'SLD' : 'Site'}</span>
            </div>
          </div>

          {/* Floating Zoom Controls */}
          <div className="absolute bottom-4 right-4 bg-card border border-border rounded-lg shadow-md flex flex-col z-10">
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={() => setZoom(Math.min(200, zoom + 25))}
              className="h-8 w-8 p-0 rounded-b-none border-b hover:bg-muted transition-colors"
              title="Zoom In (Ctrl + +)"
            >
              <ZoomIn className="h-4 w-4" />
            </Button>
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={() => setZoom(100)}
              className="h-8 w-8 p-0 rounded-none border-b text-xs font-medium hover:bg-muted transition-colors"
              title="Reset to 100% (Ctrl + 0)"
            >
              <span className="text-xs font-mono">{zoom}%</span>
            </Button>
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={() => setZoom(Math.max(25, zoom - 25))}
              className="h-8 w-8 p-0 rounded-t-none hover:bg-muted transition-colors"
              title="Zoom Out (Ctrl + -)"
            >
              <ZoomOut className="h-4 w-4" />
            </Button>
          </div>


          {/* Floating Mini-Map */}
          <div className="absolute top-16 right-4 bg-card border border-border rounded-lg shadow-md p-3 w-28 h-24 hover:shadow-lg transition-shadow z-10">
            <div className="text-xs font-medium text-foreground mb-2 flex items-center justify-between">
              <span>Navigator</span>
              <div className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse" title="Live view"></div>
            </div>
            <div className="w-full h-14 bg-gradient-to-br from-background to-muted rounded border border-border relative overflow-hidden cursor-pointer hover:border-primary transition-colors">
              {/* Grid pattern background */}
              <div 
                className="absolute inset-0 opacity-30"
                style={{
                  backgroundImage: `url("data:image/svg+xml,%3csvg width='8' height='8' xmlns='http://www.w3.org/2000/svg'%3e%3cdefs%3e%3cpattern id='grid' width='8' height='8' patternUnits='userSpaceOnUse'%3e%3cpath d='M 8 0 L 0 0 0 8' fill='none' stroke='%23a8a8a8' stroke-width='0.5'/%3e%3c/pattern%3e%3c/defs%3e%3crect width='100%25' height='100%25' fill='url(%23grid)' /%3e%3c/svg%3e")`,
                }}
              />
              
              {/* Current view indicator */}
              <div 
                className="absolute bg-primary/20 border border-primary rounded-sm"
                style={{
                  left: '20%',
                  top: '20%',
                  width: '60%',
                  height: '60%',
                }}
                title="Current View"
              />
              
              {/* Component indicators */}
              <div className="absolute w-1 h-1 bg-blue-600 rounded-full shadow-sm" style={{left: '35%', top: '40%'}} />
              <div className="absolute w-1 h-1 bg-green-600 rounded-full shadow-sm" style={{left: '55%', top: '35%'}} />
              <div className="absolute w-1 h-1 bg-orange-600 rounded-full shadow-sm" style={{left: '45%', top: '55%'}} />
            </div>
          </div>

          {/* Keyboard Shortcuts Overlay */}
          {showShortcuts && (
            <div className="absolute inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
              <div className="bg-card rounded-lg shadow-xl border border-border p-6 max-w-md w-full mx-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-foreground">Keyboard Shortcuts</h3>
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    onClick={() => setShowShortcuts(false)}
                    className="h-6 w-6 p-0"
                  >
                    ×
                  </Button>
                </div>
                <div className="space-y-3 text-sm">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="font-medium text-foreground mb-2">Navigation</div>
                      <div className="space-y-1 text-xs">
                        <div className="flex justify-between">
                          <span>Pan Canvas</span>
                          <kbd className="bg-muted px-1 rounded">Space + Drag</kbd>
                        </div>
                        <div className="flex justify-between">
                          <span>Zoom In</span>
                          <kbd className="bg-gray-100 px-1 rounded">Ctrl + +</kbd>
                        </div>
                        <div className="flex justify-between">
                          <span>Zoom Out</span>
                          <kbd className="bg-gray-100 px-1 rounded">Ctrl + -</kbd>
                        </div>
                        <div className="flex justify-between">
                          <span>Reset Zoom</span>
                          <kbd className="bg-gray-100 px-1 rounded">Ctrl + 0</kbd>
                        </div>
                      </div>
                    </div>
                    <div>
                      <div className="font-medium text-foreground mb-2">Tools</div>
                      <div className="space-y-1 text-xs">
                        <div className="flex justify-between">
                          <span>Toggle Grid</span>
                          <kbd className="bg-gray-100 px-1 rounded">G</kbd>
                        </div>
                        <div className="flex justify-between">
                          <span>Toggle Inspector</span>
                          <kbd className="bg-gray-100 px-1 rounded">I</kbd>
                        </div>
                        <div className="flex justify-between">
                          <span>Export PDF</span>
                          <kbd className="bg-gray-100 px-1 rounded">Ctrl + E</kbd>
                        </div>
                        <div className="flex justify-between">
                          <span>Show Shortcuts</span>
                          <kbd className="bg-gray-100 px-1 rounded">?</kbd>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Collapsible Inspector Panel */}
        {showInspector && (
          <div className="w-80 border-l border-border bg-card flex flex-col">
            <div className="flex items-center justify-between p-3 border-b border-border">
              <h3 className="text-sm font-medium text-foreground">Inspector</h3>
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={() => setShowInspector(false)}
                className="h-6 w-6 p-0"
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
            <div className="flex-1 overflow-hidden">
              <InspectorPanel projectId={projectId} currentCanvasId={canvasId} />
            </div>
          </div>
        )}
        
        {/* Inspector Toggle Button (when hidden) */}
        {!showInspector && (
          <Button 
            variant="ghost" 
            size="sm"
            onClick={() => setShowInspector(true)}
            className="absolute top-4 right-4 h-8 w-8 p-0 bg-card border border-border shadow-sm z-10"
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
        )}
      </div>
    </div>
  )
}