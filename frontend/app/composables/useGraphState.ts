import { ref, computed } from 'vue'
import type { Node, Edge } from '@vue-flow/core'

export type NodeStatus = 'idle' | 'running' | 'completed' | 'error' | 'skipped'

export interface NodeData {
  label: string
  status: NodeStatus
  details: Record<string, any>
  i18nKey: string
  color: string
}

const NODE_DEFS = [
  { id: 'router', i18nKey: 'graph.router', color: '#6C5CE7', x: 400, y: 0 },
  { id: 'retriever', i18nKey: 'graph.retriever', color: '#0984E3', x: 200, y: 120 },
  { id: 'web_search', i18nKey: 'graph.web_search', color: '#00CEC9', x: 600, y: 120 },
  { id: 'grader', i18nKey: 'graph.grader', color: '#6C5CE7', x: 200, y: 240 },
  { id: 'generator', i18nKey: 'graph.generator', color: '#FDCB6E', x: 400, y: 360 },
  { id: 'hallucination_checker', i18nKey: 'graph.hallucination_checker', color: '#FF6B6B', x: 250, y: 480 },
  { id: 'relevance_checker', i18nKey: 'graph.relevance_checker', color: '#FF6B6B', x: 550, y: 480 },
  { id: 'report_builder', i18nKey: 'graph.report_builder', color: '#00B894', x: 400, y: 600 },
] as const

const EDGE_DEFS = [
  { source: 'router', target: 'retriever', label: 'vector_store' },
  { source: 'router', target: 'web_search', label: 'web_search' },
  { source: 'retriever', target: 'grader' },
  { source: 'grader', target: 'generator', label: 'pass' },
  { source: 'grader', target: 'web_search', label: 'fallback' },
  { source: 'web_search', target: 'generator' },
  { source: 'generator', target: 'hallucination_checker' },
  { source: 'hallucination_checker', target: 'relevance_checker', label: 'pass' },
  { source: 'hallucination_checker', target: 'generator', label: 'retry' },
  { source: 'hallucination_checker', target: 'report_builder', label: 'max retry' },
  { source: 'relevance_checker', target: 'report_builder', label: 'pass' },
  { source: 'relevance_checker', target: 'web_search', label: 'retry' },
] as const

export function useGraphState() {
  const nodeStates = ref<Record<string, { status: NodeStatus; details: Record<string, any> }>>(
    Object.fromEntries(NODE_DEFS.map(n => [n.id, { status: 'idle' as NodeStatus, details: {} }]))
  )

  const nodes = computed<Node<NodeData>[]>(() =>
    NODE_DEFS.map(def => ({
      id: def.id,
      type: 'custom',
      position: { x: def.x, y: def.y },
      data: {
        label: def.id,
        status: nodeStates.value[def.id].status,
        details: nodeStates.value[def.id].details,
        i18nKey: def.i18nKey,
        color: def.color,
      },
    }))
  )

  const edges = computed<Edge[]>(() =>
    EDGE_DEFS.map((def, i) => ({
      id: `e-${def.source}-${def.target}-${i}`,
      source: def.source,
      target: def.target,
      animated: nodeStates.value[def.source]?.status === 'running',
      style: {
        stroke: nodeStates.value[def.source]?.status === 'running'
          ? NODE_DEFS.find(n => n.id === def.source)?.color
          : '#ddd',
        strokeWidth: nodeStates.value[def.source]?.status === 'running' ? 2.5 : 1.5,
      },
      label: def.label || undefined,
      labelStyle: { fontSize: '11px', fill: '#999' },
    }))
  )

  function updateNode(nodeId: string, status: NodeStatus, details?: Record<string, any>) {
    if (nodeStates.value[nodeId]) {
      nodeStates.value[nodeId].status = status
      if (details) {
        nodeStates.value[nodeId].details = {
          ...nodeStates.value[nodeId].details,
          ...details,
        }
      }
    }
  }

  function resetAll() {
    for (const id of Object.keys(nodeStates.value)) {
      nodeStates.value[id] = { status: 'idle', details: {} }
    }
  }

  return { nodes, edges, nodeStates, updateNode, resetAll }
}
