import type { NodeTypeInfo, NodeCategory, ConfigField } from '~/types/graph'

const MODEL_OPTIONS = [
  { label: 'GPT-4o Mini', value: 'gpt-4o-mini' },
  { label: 'GPT-4o', value: 'gpt-4o' },
]

const NODE_TYPES: NodeTypeInfo[] = [
  // --- Entry ---
  {
    type: 'router',
    category: 'entry',
    label: 'graph.router',
    icon: '🔀',
    color: '#6C5CE7',
    configSchema: [
      { key: 'model', label: 'config.model', type: 'select', options: MODEL_OPTIONS, default: 'gpt-4o-mini' },
    ],
    allowedSources: ['START'],
    allowedTargets: ['retriever', 'web_search', 'generator'],
    outputFields: ['route'],
  },
  {
    type: 'query_rewriter',
    category: 'entry',
    label: 'graph.query_rewriter',
    icon: '✏️',
    color: '#A29BFE',
    configSchema: [
      { key: 'model', label: 'config.model', type: 'select', options: MODEL_OPTIONS, default: 'gpt-4o-mini' },
    ],
    allowedSources: ['START', 'relevance_checker'],
    allowedTargets: ['router', 'retriever'],
    outputFields: ['question'],
  },

  // --- Retrieval ---
  {
    type: 'retriever',
    category: 'retrieval',
    label: 'graph.retriever',
    icon: '📚',
    color: '#0984E3',
    configSchema: [
      { key: 'knowledge_base', label: 'config.knowledge_base', type: 'select', options: [{ label: 'LangChain Docs', value: 'langchain_docs' }], default: 'langchain_docs' },
      { key: 'top_k', label: 'config.top_k', type: 'number', default: 5 },
    ],
    allowedSources: ['router', 'query_rewriter', 'relevance_checker'],
    allowedTargets: ['grader', 'generator', 'summarizer'],
    outputFields: ['documents'],
  },
  {
    type: 'web_search',
    category: 'retrieval',
    label: 'graph.web_search',
    icon: '🌐',
    color: '#00CEC9',
    configSchema: [
      { key: 'max_results', label: 'config.max_results', type: 'number', default: 3 },
    ],
    allowedSources: ['router', 'grader', 'relevance_checker'],
    allowedTargets: ['generator', 'grader', 'summarizer'],
    outputFields: ['web_results'],
  },

  // --- Filter ---
  {
    type: 'grader',
    category: 'filter',
    label: 'graph.grader',
    icon: '✅',
    color: '#6C5CE7',
    configSchema: [
      { key: 'model', label: 'config.model', type: 'select', options: MODEL_OPTIONS, default: 'gpt-4o-mini' },
    ],
    allowedSources: ['retriever'],
    allowedTargets: ['generator', 'web_search'],
    outputFields: ['grader_fallback', 'graded_documents'],
  },

  // --- Generation ---
  {
    type: 'generator',
    category: 'generation',
    label: 'graph.generator',
    icon: '⚡',
    color: '#FDCB6E',
    configSchema: [
      { key: 'model', label: 'config.model', type: 'select', options: MODEL_OPTIONS, default: 'gpt-4o-mini' },
      { key: 'temperature', label: 'config.temperature', type: 'number', default: 0 },
      { key: 'max_retries', label: 'config.max_retries', type: 'number', default: 3 },
    ],
    allowedSources: ['retriever', 'grader', 'web_search', 'summarizer'],
    allowedTargets: ['hallucination_checker', 'relevance_checker', 'report_builder'],
    outputFields: ['generation'],
  },

  // --- Quality ---
  {
    type: 'hallucination_checker',
    category: 'quality',
    label: 'graph.hallucination_checker',
    icon: '🔍',
    color: '#FF6B6B',
    configSchema: [
      { key: 'model', label: 'config.model', type: 'select', options: MODEL_OPTIONS, default: 'gpt-4o-mini' },
    ],
    allowedSources: ['generator'],
    allowedTargets: ['relevance_checker', 'generator', 'report_builder'],
    outputFields: ['hallucination_pass'],
  },
  {
    type: 'relevance_checker',
    category: 'quality',
    label: 'graph.relevance_checker',
    icon: '🎯',
    color: '#FF6B6B',
    configSchema: [
      { key: 'model', label: 'config.model', type: 'select', options: MODEL_OPTIONS, default: 'gpt-4o-mini' },
    ],
    allowedSources: ['hallucination_checker', 'generator'],
    allowedTargets: ['report_builder', 'web_search', 'query_rewriter', 'retriever'],
    outputFields: ['relevance_pass'],
  },

  // --- Output ---
  {
    type: 'report_builder',
    category: 'output',
    label: 'graph.report_builder',
    icon: '📋',
    color: '#00B894',
    configSchema: [],
    allowedSources: ['relevance_checker', 'generator', 'hallucination_checker'],
    allowedTargets: ['END'],
    outputFields: ['report'],
  },

  // --- Transform ---
  {
    type: 'summarizer',
    category: 'transform',
    label: 'graph.summarizer',
    icon: '📝',
    color: '#74B9FF',
    configSchema: [
      { key: 'model', label: 'config.model', type: 'select', options: MODEL_OPTIONS, default: 'gpt-4o-mini' },
      { key: 'max_length', label: 'config.max_length', type: 'number', default: 500 },
    ],
    allowedSources: ['retriever', 'web_search'],
    allowedTargets: ['generator'],
    outputFields: ['summary'],
  },
]

const NODE_TYPE_MAP = new Map(NODE_TYPES.map(n => [n.type, n]))

const CATEGORY_ORDER: NodeCategory[] = ['entry', 'retrieval', 'filter', 'generation', 'quality', 'output', 'transform']

const CATEGORY_LABELS: Record<NodeCategory, string> = {
  entry: 'category.entry',
  retrieval: 'category.retrieval',
  filter: 'category.filter',
  generation: 'category.generation',
  quality: 'category.quality',
  output: 'category.output',
  transform: 'category.transform',
}

export function useNodeRegistry() {
  function getNodeTypes(): NodeTypeInfo[] {
    return NODE_TYPES
  }

  function getNodeTypeInfo(type: string): NodeTypeInfo | undefined {
    return NODE_TYPE_MAP.get(type)
  }

  function getNodeTypesByCategory(): { category: NodeCategory; label: string; nodes: NodeTypeInfo[] }[] {
    return CATEGORY_ORDER
      .map(cat => ({
        category: cat,
        label: CATEGORY_LABELS[cat],
        nodes: NODE_TYPES.filter(n => n.category === cat),
      }))
      .filter(g => g.nodes.length > 0)
  }

  function isValidConnection(sourceType: string, targetType: string): boolean {
    const targetInfo = NODE_TYPE_MAP.get(targetType)
    if (!targetInfo) return false
    return targetInfo.allowedSources.includes(sourceType)
  }

  return {
    getNodeTypes,
    getNodeTypeInfo,
    getNodeTypesByCategory,
    isValidConnection,
  }
}
