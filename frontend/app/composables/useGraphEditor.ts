import { useVueFlow } from '@vue-flow/core'
import type { Connection, Node } from '@vue-flow/core'
import type { GraphConfig, NodeData } from '~/types/graph'

export const FLOW_ID = 'rag-pipeline'

let idCounter = 0
function nextId(type: string): string {
  return `${type}_${++idCounter}`
}

export function useGraphEditor() {
  const { screenToFlowCoordinate, addNodes, addEdges, findNode, getNodes, getEdges, removeNodes, removeEdges, setNodes, setEdges } = useVueFlow({ id: FLOW_ID })
  const { getNodeTypeInfo, isValidConnection: checkConnection } = useNodeRegistry()

  // -----------------------------------------------------------------------
  // Drag & Drop
  // -----------------------------------------------------------------------

  function onDragOver(event: DragEvent) {
    event.preventDefault()
    if (event.dataTransfer) {
      event.dataTransfer.dropEffect = 'move'
    }
  }

  function onDrop(event: DragEvent) {
    const nodeType = event.dataTransfer?.getData('application/rag-node-type')
    if (!nodeType) return

    const info = getNodeTypeInfo(nodeType)
    if (!info) return

    const position = screenToFlowCoordinate({
      x: event.clientX,
      y: event.clientY,
    })

    const nodeId = nextId(nodeType)
    const newNode: Node<NodeData> = {
      id: nodeId,
      type: 'custom',
      position,
      data: {
        label: nodeId,
        nodeType: info.type,
        status: 'idle',
        details: {},
        i18nKey: info.label,
        color: info.color,
        icon: info.icon,
        config: Object.fromEntries(info.configSchema.map(f => [f.key, f.default])),
      },
    }

    addNodes([newNode])
  }

  // -----------------------------------------------------------------------
  // Connection validation
  // -----------------------------------------------------------------------

  function isValidConnection(connection: Connection): boolean {
    const sourceNode = findNode(connection.source)
    const targetNode = findNode(connection.target)
    if (!sourceNode || !targetNode) return false

    const sourceType = (sourceNode.data as NodeData).nodeType
    const targetType = (targetNode.data as NodeData).nodeType
    return checkConnection(sourceType, targetType)
  }

  function onConnect(params: Connection) {
    if (isValidConnection(params)) {
      addEdges([{
        id: `e-${params.source}-${params.target}`,
        source: params.source,
        target: params.target,
      }])
    }
  }

  // -----------------------------------------------------------------------
  // Serialization: Vue Flow → GraphConfig
  // -----------------------------------------------------------------------

  function toGraphConfig(): GraphConfig {
    const nodes: GraphConfig['nodes'] = {}
    const edges: GraphConfig['edges'] = []
    const conditionalEdges: GraphConfig['conditional_edges'] = []

    for (const node of getNodes.value) {
      const data = node.data as NodeData
      nodes[node.id] = {
        type: data.nodeType,
        config: { ...data.config },
        position: { x: node.position.x, y: node.position.y },
      }
    }

    // Group edges by source, separating labeled (conditional) from unlabeled (regular)
    const labeledBySource = new Map<string, { label: string; target: string }[]>()
    const unlabeledBySource = new Map<string, string[]>()

    for (const edge of getEdges.value) {
      if (edge.label) {
        const list = labeledBySource.get(edge.source) || []
        list.push({ label: edge.label as string, target: edge.target })
        labeledBySource.set(edge.source, list)
      } else {
        const list = unlabeledBySource.get(edge.source) || []
        list.push(edge.target)
        unlabeledBySource.set(edge.source, list)
      }
    }

    // Labeled edges → conditional edges
    for (const [source, entries] of labeledBySource) {
      const sourceNode = findNode(source)
      const sourceType = sourceNode ? (sourceNode.data as NodeData).nodeType : ''
      const info = getNodeTypeInfo(sourceType)
      const routerField = info?.outputFields[0] || 'route'
      const mapping: Record<string, string> = {}
      for (const { label, target } of entries) {
        mapping[label] = target
      }
      conditionalEdges.push({ source, router_field: routerField, mapping })
    }

    // Unlabeled edges → regular edges
    for (const [source, targets] of unlabeledBySource) {
      for (const target of targets) {
        edges.push({ source, target })
      }
    }

    // Find START and END
    // Nodes with no incoming edges from other nodes = connected from START
    const allTargets = new Set(getEdges.value.map(e => e.target))
    const startNodes = getNodes.value.filter(n => !allTargets.has(n.id))
    for (const n of startNodes) {
      edges.unshift({ source: 'START', target: n.id })
    }

    // Nodes with no outgoing edges = connected to END
    const allSources = new Set(getEdges.value.map(e => e.source))
    const endNodes = getNodes.value.filter(n => !allSources.has(n.id))
    for (const n of endNodes) {
      edges.push({ source: n.id, target: 'END' })
    }

    return { nodes, edges, conditional_edges: conditionalEdges }
  }

  // -----------------------------------------------------------------------
  // Load from GraphConfig (template or import)
  // -----------------------------------------------------------------------

  function loadGraphConfig(config: GraphConfig) {
    const newNodes: Node<NodeData>[] = []

    for (const [nodeId, nodeCfg] of Object.entries(config.nodes)) {
      const info = getNodeTypeInfo(nodeCfg.type)
      if (!info) continue

      newNodes.push({
        id: nodeId,
        type: 'custom',
        position: nodeCfg.position || { x: 0, y: 0 },
        data: {
          label: nodeId,
          nodeType: info.type,
          status: 'idle',
          details: {},
          i18nKey: info.label,
          color: info.color,
          icon: info.icon,
          config: { ...Object.fromEntries(info.configSchema.map(f => [f.key, f.default])), ...nodeCfg.config },
        },
      })
    }

    // Build edges from both regular and conditional
    const newEdges: { id: string; source: string; target: string; label?: string }[] = []

    for (const edge of config.edges) {
      if (edge.source === 'START' || edge.target === 'END') continue
      newEdges.push({
        id: `e-${edge.source}-${edge.target}`,
        source: edge.source,
        target: edge.target,
      })
    }

    for (const cond of config.conditional_edges) {
      for (const [value, target] of Object.entries(cond.mapping)) {
        if (target === 'END') continue
        newEdges.push({
          id: `e-${cond.source}-${target}-${value}`,
          source: cond.source,
          target,
          label: value,
        })
      }
    }

    setNodes(newNodes)
    setEdges(newEdges)

    // Update id counter
    const maxId = newNodes.reduce((max, n) => {
      const match = n.id.match(/_(\d+)$/)
      return match ? Math.max(max, parseInt(match[1])) : max
    }, idCounter)
    idCounter = maxId
  }

  function clearGraph() {
    setNodes([])
    setEdges([])
  }

  return {
    onDragOver,
    onDrop,
    isValidConnection,
    onConnect,
    toGraphConfig,
    loadGraphConfig,
    clearGraph,
    getNodes,
    getEdges,
  }
}
