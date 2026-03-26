import { useVueFlow } from '@vue-flow/core'
import type { NodeData, NodeStatus } from '~/types/graph'
import { FLOW_ID } from './useGraphEditor'

export type { NodeStatus, NodeData }

export function useGraphState() {
  const { getNodes, getEdges, setNodes } = useVueFlow({ id: FLOW_ID })

  const nodes = computed(() => getNodes.value)
  const edges = computed(() => {
    return getEdges.value.map(edge => {
      const sourceNode = getNodes.value.find(n => n.id === edge.source)
      const sourceData = sourceNode?.data as NodeData | undefined
      const isRunning = sourceData?.status === 'running'

      return {
        ...edge,
        animated: isRunning,
        style: {
          stroke: isRunning ? sourceData?.color : '#ddd',
          strokeWidth: isRunning ? 2.5 : 1.5,
        },
        labelStyle: { fontSize: '11px', fill: '#999' },
      }
    })
  })

  function updateNode(nodeId: string, status: NodeStatus, details?: Record<string, any>) {
    const node = getNodes.value.find(n => n.id === nodeId)
    if (!node) return

    const data = node.data as NodeData
    data.status = status
    if (details) {
      data.details = { ...data.details, ...details }
    }
  }

  function resetAll() {
    for (const node of getNodes.value) {
      const data = node.data as NodeData
      data.status = 'idle'
      data.details = {}
    }
  }

  return { nodes, edges, updateNode, resetAll }
}
