import dagre from '@dagrejs/dagre'
import { useVueFlow } from '@vue-flow/core'
import { FLOW_ID } from './useGraphEditor'

const NODE_WIDTH = 160
const NODE_HEIGHT = 60

export function useAutoLayout() {
  const { getNodes, getEdges, setNodes } = useVueFlow({ id: FLOW_ID })

  function applyAutoLayout(direction: 'TB' | 'LR' = 'TB') {
    const nodes = getNodes.value
    const edges = getEdges.value

    if (nodes.length === 0) return

    const g = new dagre.graphlib.Graph()
    g.setDefaultEdgeLabel(() => ({}))
    g.setGraph({ rankdir: direction, ranksep: 80, nodesep: 60 })

    for (const node of nodes) {
      g.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT })
    }

    for (const edge of edges) {
      g.setEdge(edge.source, edge.target)
    }

    dagre.layout(g)

    const updatedNodes = nodes.map(node => {
      const pos = g.node(node.id)
      return {
        ...node,
        position: {
          x: pos.x - NODE_WIDTH / 2,
          y: pos.y - NODE_HEIGHT / 2,
        },
      }
    })

    setNodes(updatedNodes)
  }

  return { applyAutoLayout }
}
