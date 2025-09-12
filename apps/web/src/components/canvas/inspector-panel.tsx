"use client"
import * as React from 'react'
import { useSelection, useCanvasBus } from './bus'
import { Button } from '@originfd/ui'
import { MousePointer2, Layers, Map, ExternalLink } from 'lucide-react'
import { apiClient } from '@/lib/api-client'
import Link from 'next/link'

export function InspectorPanel({ projectId, currentCanvasId }: { projectId: string; currentCanvasId: string }) {
  const { instanceId } = useSelection()
  const bus = useCanvasBus()
  const [asset, setAsset] = React.useState<any>(null)

  React.useEffect(() => {
    let ignore = false
    async function run() {
      if (!instanceId) { setAsset(null); return }
      try {
        const a = await apiClient.getAsset(projectId, instanceId)
        if (!ignore) setAsset(a)
      } catch { if (!ignore) setAsset(null) }
    }
    run(); return () => { ignore = true }
  }, [projectId, instanceId])

  if (!instanceId) return (
    <div className="p-4 text-center text-sm text-gray-500">
      <MousePointer2 className="h-8 w-8 mx-auto mb-2 text-gray-400" />
      <p>Select an element to view details</p>
    </div>
  )

  return (
    <div className="p-4 space-y-4">
      {/* Selected Element */}
      <div className="space-y-3">
        <div className="font-medium text-gray-900 text-sm truncate" title={instanceId}>
          {asset?.name || instanceId}
        </div>
        
        {asset && (
          <div className="space-y-2 text-xs">
            <div className="grid grid-cols-3 gap-2">
              <span className="text-gray-500">Type:</span>
              <span className="col-span-2 text-gray-900">{asset.type ?? '—'}</span>
            </div>
            
            {asset.parameters && (
              <details className="group">
                <summary className="cursor-pointer text-gray-600 hover:text-gray-900 py-1">
                  Parameters
                </summary>
                <div className="mt-2 p-2 bg-gray-50 rounded text-xs overflow-auto max-h-32">
                  <pre>{JSON.stringify(asset.parameters, null, 2)}</pre>
                </div>
              </details>
            )}
          </div>
        )}
      </div>
      
      {/* Actions */}
      <div className="space-y-2 pt-2 border-t border-gray-200">
        <Button 
          size="sm" 
          variant="outline" 
          onClick={() => bus.select(instanceId)}
          className="w-full justify-start text-xs h-8"
        >
          <MousePointer2 className="h-3 w-3 mr-2" />
          Re-select
        </Button>
        
        {currentCanvasId?.startsWith('sld') ? (
          <Link href={`/projects/${projectId}/canvases/site-layout`} className="block">
            <Button size="sm" variant="outline" className="w-full justify-start text-xs h-8">
              <Map className="h-3 w-3 mr-2" />
              Open in Site
              <ExternalLink className="h-3 w-3 ml-auto" />
            </Button>
          </Link>
        ) : (
          <Link href={`/projects/${projectId}/canvases/sld-mv`} className="block">
            <Button size="sm" variant="outline" className="w-full justify-start text-xs h-8">
              <Layers className="h-3 w-3 mr-2" />
              Open in SLD
              <ExternalLink className="h-3 w-3 ml-auto" />
            </Button>
          </Link>
        )}
      </div>
    </div>
  )
}

export default InspectorPanel