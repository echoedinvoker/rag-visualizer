<script setup lang="ts">
import { CloseOutlined, BranchesOutlined } from '@ant-design/icons-vue'
import { useVueFlow } from '@vue-flow/core'
import type { Node } from '@vue-flow/core'
import type { NodeData, ConfigField } from '~/types/graph'
import { FLOW_ID } from '~/composables/useGraphEditor'

const props = defineProps<{
  node: Node
}>()

const emit = defineEmits<{
  close: []
}>()

const { t } = useI18n()
const { getNodeTypeInfo } = useNodeRegistry()
const { getNodes, getEdges, addEdges, setEdges } = useVueFlow({ id: FLOW_ID })

const { collectionName: sessionCollection, files: sessionFiles } = useSession()

const data = computed(() => props.node.data as NodeData)
const nodeInfo = computed(() => getNodeTypeInfo(data.value.nodeType))
const configSchema = computed(() => {
  const schema = nodeInfo.value?.configSchema || []
  // Dynamically add session collection to knowledge_base options
  if (data.value.nodeType === 'retriever' && sessionCollection.value && sessionFiles.value.length > 0) {
    return schema.map(field => {
      if (field.key !== 'knowledge_base') return field
      const sessionOption = { label: `Uploaded (${sessionFiles.value.length} files)`, value: sessionCollection.value! }
      const hasSession = field.options?.some(o => o.value === sessionCollection.value)
      if (hasSession) return field
      return {
        ...field,
        options: [...(field.options || []), sessionOption],
      }
    })
  }
  return schema
})

// --- Conditional edge support ---
const CONDITIONAL_TYPES = new Set(['router', 'grader', 'hallucination_checker', 'relevance_checker'])
const hasConditionalEdges = computed(() => CONDITIONAL_TYPES.has(data.value.nodeType))
const outputFields = computed(() => nodeInfo.value?.outputFields || [])

// Get outgoing edges from this node
const outgoingEdges = computed(() => {
  return getEdges.value.filter(e => e.source === props.node.id)
})

// Available target nodes (all nodes except this one)
const availableTargets = computed(() => {
  return getNodes.value
    .filter(n => n.id !== props.node.id)
    .map(n => ({
      id: n.id,
      label: `${(n.data as NodeData).icon} ${t((n.data as NodeData).i18nKey)} (${n.id})`,
    }))
})

// Pre-defined value options for each node type's output field
const routingOptions = computed<{ value: string; label: string }[]>(() => {
  switch (data.value.nodeType) {
    case 'router':
      return [
        { value: 'vector_store', label: 'vector_store' },
        { value: 'web_search', label: 'web_search' },
      ]
    case 'grader':
      return [
        { value: 'True', label: 'Fallback (all filtered)' },
        { value: 'False', label: 'Pass (has results)' },
      ]
    case 'hallucination_checker':
      return [
        { value: 'True', label: 'Pass (grounded)' },
        { value: 'False', label: 'Fail (hallucination)' },
      ]
    case 'relevance_checker':
      return [
        { value: 'True', label: 'Pass (relevant)' },
        { value: 'False', label: 'Fail (not relevant)' },
      ]
    default:
      return []
  }
})

// Current mapping: value → target node ID
const currentMapping = computed(() => {
  const map: Record<string, string> = {}
  for (const edge of outgoingEdges.value) {
    if (edge.label) {
      map[edge.label as string] = edge.target
    }
  }
  return map
})

function updateRouteTarget(routeValue: string, targetNodeId: string) {
  // Remove existing edge for this route value
  const newEdges = getEdges.value.filter(e => {
    if (e.source !== props.node.id) return true
    if (e.label === routeValue) return false
    return true
  })

  // Add new edge
  if (targetNodeId) {
    newEdges.push({
      id: `e-${props.node.id}-${targetNodeId}-${routeValue}`,
      source: props.node.id,
      target: targetNodeId,
      label: routeValue,
    })
  }

  setEdges(newEdges)
}

function updateConfig(key: string, value: any) {
  data.value.config[key] = value
}
</script>

<template>
  <div class="config-panel">
    <div class="panel-header">
      <div class="panel-title">
        <span class="panel-icon">{{ data.icon }}</span>
        <span>{{ t(data.i18nKey) }}</span>
      </div>
      <a-button type="text" size="small" @click="$emit('close')">
        <template #icon><CloseOutlined /></template>
      </a-button>
    </div>

    <div class="panel-id">{{ node.id }}</div>

    <a-divider style="margin: 8px 0" />

    <!-- Config fields -->
    <div v-if="configSchema.length > 0" class="config-fields">
      <div v-for="field in configSchema" :key="field.key" class="config-field">
        <label class="field-label">{{ t(field.label) }}</label>

        <a-select
          v-if="field.type === 'select'"
          :value="data.config[field.key] ?? field.default"
          size="small"
          style="width: 100%"
          @update:value="updateConfig(field.key, $event)"
        >
          <a-select-option
            v-for="opt in field.options"
            :key="opt.value"
            :value="opt.value"
          >
            {{ opt.label }}
          </a-select-option>
        </a-select>

        <a-input-number
          v-else-if="field.type === 'number'"
          :value="data.config[field.key] ?? field.default"
          size="small"
          style="width: 100%"
          :min="0"
          @update:value="updateConfig(field.key, $event)"
        />

        <a-input
          v-else
          :value="data.config[field.key] ?? field.default"
          size="small"
          @update:value="updateConfig(field.key, $event)"
        />
      </div>
    </div>

    <div v-else class="no-config">
      {{ t('config.no_settings') }}
    </div>

    <!-- Conditional routing -->
    <template v-if="hasConditionalEdges">
      <a-divider style="margin: 12px 0 8px" />

      <div class="section-header">
        <BranchesOutlined />
        <span>{{ t('config.routing') }}</span>
      </div>

      <div class="routing-field">
        <div class="field-label">{{ t('config.router_field') }}: <code>{{ outputFields[0] }}</code></div>
      </div>

      <div class="routing-mappings">
        <div v-for="opt in routingOptions" :key="opt.value" class="routing-row">
          <div class="route-value">{{ opt.label }}</div>
          <a-select
            :value="currentMapping[opt.value] || undefined"
            size="small"
            style="width: 100%"
            :placeholder="t('config.select_target')"
            allow-clear
            @update:value="updateRouteTarget(opt.value, $event)"
          >
            <a-select-option
              v-for="target in availableTargets"
              :key="target.id"
              :value="target.id"
            >
              {{ target.label }}
            </a-select-option>
          </a-select>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.config-panel {
  padding: var(--space-2);
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 700;
  font-size: 14px;
  color: var(--slate-700);
}

.panel-icon {
  font-size: 16px;
}

.panel-id {
  font-size: 11px;
  color: var(--color-text-muted);
  font-family: monospace;
  margin-top: 2px;
}

.no-config {
  font-size: 12px;
  color: var(--color-text-muted);
  text-align: center;
  padding: var(--space-4) 0;
}

.config-fields {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.config-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.field-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.field-label code {
  text-transform: none;
  font-size: 11px;
  color: var(--primary);
  background: var(--slate-50);
  padding: 1px 4px;
  border-radius: 3px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 700;
  color: var(--slate-600);
  margin-bottom: var(--space-2);
}

.routing-field {
  margin-bottom: var(--space-2);
}

.routing-mappings {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.routing-row {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.route-value {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-secondary);
}
</style>
