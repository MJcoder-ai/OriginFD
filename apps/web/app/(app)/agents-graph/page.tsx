'use client'

import React, { useCallback, useEffect, useState } from 'react'
import ReactFlow, { Edge, Node, Background, Controls } from 'reactflow'
import 'reactflow/dist/style.css'

interface NodeMeta {
  id: string
  label?: string
  scopes?: string[]
  guard_budget?: number
  autonomy?: string
  region?: string
}

export default function AgentsGraphPage() {
  const [nodes, setNodes] = useState<Node[]>([])
  const [edges, setEdges] = useState<Edge[]>([])
  const [selected, setSelected] = useState<NodeMeta | null>(null)

  useEffect(() => {
    fetch('/api/graph')
      .then((res) => res.json())
      .then((data) => {
        const graphs = Object.values(data) as any[]
        if (graphs.length > 0) {
          const graph = graphs[0]
          setNodes((graph as any).nodes || [])
          setEdges((graph as any).edges || [])
        }
      })
      .catch(() => {
        // ignore fetch errors in mock environment
      })
  }, [])

  const onNodeClick = useCallback((_evt: any, node: Node) => {
    fetch(`/api/graph/nodes/${node.id}`)
      .then((res) => res.json())
      .then((meta) => setSelected(meta))
      .catch(() => setSelected(null))
  }, [])

  return (
    <div className="flex h-full">
      <div className="flex-1 h-full">
        <ReactFlow nodes={nodes} edges={edges} onNodeClick={onNodeClick} fitView>
          <Background />
          <Controls />
        </ReactFlow>
      </div>
      <aside className="w-64 border-l p-4 text-sm">
        {selected ? (
          <div>
            <h2 className="font-semibold mb-2">{selected.label || selected.id}</h2>
            {selected.scopes && (
              <p className="mb-1">Scopes: {selected.scopes.join(', ')}</p>
            )}
            {selected.guard_budget !== undefined && (
              <p className="mb-1">Guard Budget: {selected.guard_budget}</p>
            )}
            {selected.autonomy && (
              <p className="mb-1">Autonomy: {selected.autonomy}</p>
            )}
            {selected.region && <p className="mb-1">Region: {selected.region}</p>}
          </div>
        ) : (
          <p>Select a node to inspect</p>
        )}
      </aside>
    </div>
  )
}
