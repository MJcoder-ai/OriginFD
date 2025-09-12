'use client'
import * as React from 'react'
import { SystemDiagram } from '@/components/odl-sd'
import type { OdlDocument, ComponentInstance, Connection } from '@/lib/types'
import { computeLayout } from './layout'
import { useCanvasBus } from './bus'

function deriveFromLibraries(document?: any): { instances: ComponentInstance[]; connections: Connection[] } {
  // Fallback for current mocks where document.instances are empty
  const libs = document?.libraries?.components || []
  const instances: ComponentInstance[] = libs.map((c: any, idx: number) => ({
    id: c.id || `lib-${idx}`,
    component_id: c.part_number ?? c.id ?? `cmp-${idx}`,
    name: c.name ?? c.part_number ?? c.id,
    parameters: { capacity_kw: (c.rating_w ?? 0) / 1000 },
    status: c.status ?? 'selected',
    // simple type mapping
    // @ts-ignore — extend base type at runtime
    type: String(c.category || '').toLowerCase() === 'pv_module' ? 'pv_array'
      : String(c.category || '').toLowerCase() === 'inverter' ? 'inverter'
      : String(c.category || '').toLowerCase() === 'battery' ? 'battery'
      : 'power_conversion_system',
  }))
  // naïve connection chain for visualization purposes
  const connections: Connection[] = []
  for (let i = 0; i < instances.length - 1; i++) {
    connections.push({
      id: `e-${i}`,
      from_instance_id: instances[i].id,
      to_instance_id: instances[i + 1].id,
      from_port: 'out',
      to_port: 'in',
      connection_type: i === 0 ? 'dc_electrical' : 'ac_electrical',
    })
    // Hints for the SystemDiagram extended props
    // @ts-ignore
    connections[connections.length - 1].from_component = instances[i].id
    // @ts-ignore
    connections[connections.length - 1].to_component = instances[i + 1].id
  }
  return { instances, connections }
}

export function SLDCanvas({
  projectId,
  document,
  scope = 'mv',
  activeLayers = ['ac','dc'],
  layoutEngine = 'elk',
}: { projectId: string; document?: OdlDocument; scope?: string; activeLayers?: ('ac'|'dc')[]; layoutEngine?: 'elk'|'dagre' }) {
  const bus = useCanvasBus()
  const { instances, connections } =
    (document?.instances?.length ? { instances: document.instances, connections: (document.connections ?? []) } : deriveFromLibraries(document))

  // Filter by AC/DC layer selections
  const filtered = connections.filter(c => (c.connection_type?.startsWith('ac') ? activeLayers.includes('ac') : true)
    && (c.connection_type?.startsWith('dc') ? activeLayers.includes('dc') : true))

  // Compute layout positions
  const [positions, setPositions] = React.useState<Record<string, { x: number; y: number }>>({})
  React.useEffect(() => {
    computeLayout(
      instances.map(i => ({ id: i.id, width: 140, height: 56, type: (i as any).type })),
      filtered.map(e => ({ id: e.id, from_instance_id: e.from_instance_id, to_instance_id: e.to_instance_id, connection_type: (e as any).connection_type })),
      layoutEngine
    ).then(setPositions)
  }, [instances, filtered, layoutEngine])

  return (
    <div className="w-full" data-canvas-root>
      {/** Pass positions and click handler opportunistically (adapter tolerates unknown props) */}
      {React.createElement(SystemDiagram as unknown as any, {
        instances,
        connections: filtered,
        positions,
        compact: true,
        onNodeClick: (node: any) => bus.select(node?.id),
        onPositionChange: async (posMap: Record<string, { x: number; y: number }>) => {
          try { await (await import('@/lib/api-client')).apiClient.patchViewOverrides(`sld-${scope}`, posMap) } catch {}
        },
      })}
    </div>
  )
}

export default SLDCanvas