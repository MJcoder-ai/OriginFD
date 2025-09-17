import dagre from 'dagre'
import ELK from 'elkjs/lib/elk.bundled.js'

export type NodeLike = { id: string; width?: number; height?: number; type?: string }
export type EdgeLike = { id: string; from_instance_id: string; to_instance_id: string; connection_type?: string }

export function computeDagreLayout(nodes: NodeLike[], edges: EdgeLike[], {
  rankdir = 'LR', nodeSep = 60, rankSep = 100, marginX = 40, marginY = 40,
}: Partial<{ rankdir: 'LR'|'TB'; nodeSep: number; rankSep: number; marginX: number; marginY: number }> = {}) {
  const g = new dagre.graphlib.Graph()
  g.setGraph({ rankdir, nodesep: nodeSep, ranksep: rankSep, marginx: marginX, marginy: marginY })
  g.setDefaultEdgeLabel(() => ({}))
  nodes.forEach(n => g.setNode(n.id, { width: n.width ?? 140, height: n.height ?? 56 }))
  edges.forEach(e => g.setEdge(e.from_instance_id, e.to_instance_id))
  dagre.layout(g)
  const positions: Record<string, { x: number; y: number }> = {}
  g.nodes().forEach(id => { const { x, y } = g.node(id); positions[id] = { x, y } })
  return positions
}

export async function computeELKLayout(nodes: NodeLike[], edges: EdgeLike[], {
  direction = 'RIGHT', // RIGHT|DOWN
  nodeSep = 60,
  rankSep = 100,
}: Partial<{ direction: 'RIGHT'|'DOWN'; nodeSep: number; rankSep: number }> = {}) {
  const elk = new ELK()
  const g = {
    id: 'root',
    layoutOptions: {
      'elk.direction': direction,
      'elk.layered.spacing.nodeNodeBetweenLayers': String(rankSep),
      'elk.spacing.nodeNode': String(nodeSep),
    },
    children: nodes.map(n => ({ id: n.id, width: n.width ?? 140, height: n.height ?? 56 })),
    edges: edges.map(e => ({ id: e.id, sources: [e.from_instance_id], targets: [e.to_instance_id] })),
  } as any
  const r = await elk.layout(g)
  const pos: Record<string, { x: number; y: number }> = {}
  for (const c of r.children ?? []) pos[c.id] = { x: c.x ?? 0, y: c.y ?? 0 }
  return pos
}

export async function computeLayout(nodes: NodeLike[], edges: EdgeLike[], engine: 'elk'|'dagre' = 'elk') {
  try {
    if (engine === 'elk') return await computeELKLayout(nodes, edges, {})
  } catch (e) {
    // fall through to dagre on any ELK error
  }
  return computeDagreLayout(nodes, edges, {})
}