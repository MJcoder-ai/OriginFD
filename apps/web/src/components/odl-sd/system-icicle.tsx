'use client'

import * as React from 'react'
import * as d3 from 'd3'
import * as Tooltip from '@radix-ui/react-tooltip'
import { useVirtualizer } from '@tanstack/react-virtual'
import { InspectorContext } from '../ai/ai-copilot'

interface ComponentNode {
  id: string
  name: string
  type: string
  spec?: string
  costShare?: number
  children?: ComponentNode[]
}

interface SystemIcicleProps {
  data: ComponentNode
  size?: number
}

type ValidationStatus = 'valid' | 'invalid' | 'unknown'

export function SystemIcicle({ data, size = 500 }: SystemIcicleProps) {
  const { focusId, setFocusId } = React.useContext(InspectorContext)
  const [validation, setValidation] = React.useState<Record<string, ValidationStatus>>({})
  const radius = size / 2
  const containerRef = React.useRef<HTMLDivElement>(null)

  const root = React.useMemo(() => {
    return d3.hierarchy<ComponentNode>(data).sum(d => d.costShare || 1)
  }, [data])

  const nodes = React.useMemo(() => {
    return d3
      .partition<ComponentNode>()
      .size([2 * Math.PI, radius])
      (root)
      .descendants()
  }, [root, radius])

  const virtualizer = useVirtualizer({
    count: nodes.length,
    getScrollElement: () => containerRef.current,
    estimateSize: () => 20,
    overscan: 50
  })

  React.useEffect(() => {
    async function load() {
      try {
        const ids = nodes.map(n => n.data.id).join(',')
        const res = await fetch(`/api/validation?ids=${ids}`)
        if (res.ok) {
          const json = await res.json()
          setValidation(json)
        }
      } catch (e) {
        console.error('Failed to fetch validation status', e)
      }
    }
    load()
  }, [nodes])

  const colorForStatus = (status: ValidationStatus | undefined) => {
    switch (status) {
      case 'valid':
        return '#16a34a'
      case 'invalid':
        return '#dc2626'
      default:
        return '#9ca3af'
    }
  }

  const focusNode = focusId ? nodes.find(n => n.data.id === focusId) : null

  const arc = d3
    .arc<d3.HierarchyRectangularNode<ComponentNode>>()
    .startAngle(d => d.x0)
    .endAngle(d => d.x1)
    .innerRadius(d => d.y0)
    .outerRadius(d => d.y1)

  return (
    <div
      ref={containerRef}
      className="relative overflow-auto"
      style={{ width: size, height: size }}
    >
      <Tooltip.Provider delayDuration={100}>
        <div
          style={{
            height: virtualizer.getTotalSize(),
            width: size,
            position: 'relative'
          }}
        >
          <svg
            width={size}
            height={size}
            viewBox={`0 0 ${size} ${size}`}
            className="absolute top-0 left-0"
          >
            <g transform={`translate(${radius},${radius})`}>
              {virtualizer.getVirtualItems().map(item => {
                const node = nodes[item.index]
                const status = validation[node.data.id] || 'unknown'
                const path = arc(node) || undefined
                const isHighlighted =
                  !focusNode ||
                  node === focusNode ||
                  node.ancestors().includes(focusNode) ||
                  focusNode?.ancestors().includes(node)
                return (
                  <Tooltip.Root key={node.data.id}>
                    <Tooltip.Trigger asChild>
                      <path
                        d={path}
                        fill={colorForStatus(status)}
                        opacity={isHighlighted ? 1 : 0.2}
                        className="cursor-pointer"
                        onClick={() => setFocusId(node.data.id === focusId ? null : node.data.id)}
                      />
                    </Tooltip.Trigger>
                    <Tooltip.Content side="top" className="rounded bg-gray-800 px-2 py-1 text-xs text-white shadow">
                      <div className="font-medium">{node.data.name}</div>
                      <div>Type: {node.data.type}</div>
                      {node.data.spec && <div>Spec: {node.data.spec}</div>}
                      {node.data.costShare !== undefined && (
                        <div>Cost: {d3.format('.1%')(node.data.costShare)}</div>
                      )}
                      <Tooltip.Arrow className="fill-gray-800" />
                    </Tooltip.Content>
                  </Tooltip.Root>
                )
              })}
            </g>
          </svg>
        </div>
      </Tooltip.Provider>
    </div>
  )
}
