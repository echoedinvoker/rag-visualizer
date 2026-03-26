/** Types shared between graph editor, execution, and serialization. */

// ---------------------------------------------------------------------------
// Graph Config (exchanged with backend)
// ---------------------------------------------------------------------------

export interface GraphConfig {
  nodes: Record<string, NodeConfig>
  edges: EdgeConfig[]
  conditional_edges: ConditionalEdgeConfig[]
}

export interface NodeConfig {
  type: string
  config: Record<string, any>
  position?: { x: number; y: number }
}

export interface EdgeConfig {
  source: string // node ID or "START"
  target: string // node ID or "END"
}

export interface ConditionalEdgeConfig {
  source: string
  router_field: string
  mapping: Record<string, string>
}

// ---------------------------------------------------------------------------
// Node type metadata (frontend registry)
// ---------------------------------------------------------------------------

export interface NodeTypeInfo {
  type: string
  category: NodeCategory
  label: string       // i18n key
  icon: string        // emoji
  color: string       // hex color
  configSchema: ConfigField[]
  allowedSources: string[]  // node types that can connect TO this node
  allowedTargets: string[]  // node types this node can connect TO
  outputFields: string[]    // state fields this node writes (for conditional edge UI)
}

export type NodeCategory = 'entry' | 'retrieval' | 'filter' | 'generation' | 'quality' | 'output' | 'transform'

export interface ConfigField {
  key: string
  label: string       // i18n key
  type: 'select' | 'number' | 'text'
  options?: { label: string; value: any }[]
  default: any
}

// ---------------------------------------------------------------------------
// Node / Edge state during execution
// ---------------------------------------------------------------------------

export type NodeStatus = 'idle' | 'running' | 'completed' | 'error' | 'skipped'

export interface NodeData {
  label: string
  nodeType: string     // registry type (router, retriever, etc.)
  status: NodeStatus
  details: Record<string, any>
  i18nKey: string
  color: string
  icon: string
  config: Record<string, any>
}

// ---------------------------------------------------------------------------
// Templates
// ---------------------------------------------------------------------------

export interface TemplateInfo {
  id: string
  name: string
  description: string
}

export interface TemplateDetail extends TemplateInfo {
  config: GraphConfig
}

// ---------------------------------------------------------------------------
// Log entries
// ---------------------------------------------------------------------------

export interface LogEntry {
  id: number
  node: string
  event: string
  message: string
  details?: Record<string, any>
  timestamp: number
}
