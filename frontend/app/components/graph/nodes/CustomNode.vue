<script setup lang="ts">
import { Handle, Position } from '@vue-flow/core'
import type { NodeData } from '~/types/graph'

const props = defineProps<{
  data: NodeData
}>()

const { t } = useI18n()

// Bounce on status change
const justChanged = ref(false)
watch(() => props.data.status, () => {
  justChanged.value = true
  setTimeout(() => { justChanged.value = false }, 400)
})

const statusStyles = computed(() => {
  const c = props.data.color
  switch (props.data.status) {
    case 'running':
      return {
        background: c + '12',
        outlineColor: c,
        outlineStyle: 'solid',
        boxShadow: `0 1px 2px ${c}15, 0 4px 12px ${c}12`,
      }
    case 'completed':
      return {
        background: 'var(--success-50)',
        outlineColor: 'var(--success)',
        outlineStyle: 'solid',
        boxShadow: 'var(--shadow-sm)',
      }
    case 'error':
      return {
        background: 'var(--error-50)',
        outlineColor: 'var(--error)',
        outlineStyle: 'solid',
        boxShadow: 'var(--shadow-sm)',
      }
    default:
      return {
        background: 'var(--slate-50)',
        outlineColor: 'var(--slate-200)',
        outlineStyle: 'dashed',
        boxShadow: 'none',
      }
  }
})

const detailText = computed(() => {
  const d = props.data.details
  if (!d || Object.keys(d).length === 0) return ''
  if (d.decision) return d.decision === 'vector_store' ? '→ Vector Store' : '→ Web Search'
  if (d.count !== undefined) return `${d.count} docs`
  if (d.passed !== undefined) return `${d.passed}✓ ${d.failed}✗`
  if (d.grounded !== undefined) return d.grounded ? 'Grounded' : 'Not grounded'
  if (d.useful !== undefined) return d.useful ? 'Useful' : 'Not useful'
  if (d.rewritten) return `→ ${d.rewritten.substring(0, 30)}...`
  return ''
})
</script>

<template>
  <div
    class="custom-node"
    :class="{
      'is-running': data.status === 'running',
      'is-bounce': justChanged && data.status !== 'idle',
    }"
    :style="{
      background: statusStyles.background,
      outlineColor: statusStyles.outlineColor,
      outlineStyle: statusStyles.outlineStyle,
      boxShadow: statusStyles.boxShadow,
    }"
  >
    <Handle type="target" :position="Position.Top" />

    <div class="node-header">
      <span class="node-icon">{{ data.icon || '' }}</span>
      <span class="status-dot" :class="data.status" />
      <span class="node-label">{{ t(data.i18nKey) }}</span>
    </div>

    <Transition name="detail">
      <div v-if="detailText" class="node-detail">
        {{ detailText }}
      </div>
    </Transition>

    <Handle type="source" :position="Position.Bottom" />
  </div>
</template>

<style scoped>
.custom-node {
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-node);
  outline-width: 1.5px;
  outline-offset: -1.5px;
  min-width: 124px;
  text-align: center;
  font-family: 'Nunito', 'Noto Sans TC', sans-serif;
  transition: background 0.4s ease, outline-color 0.4s ease, box-shadow 0.5s ease;
}

.custom-node.is-running {
  animation: pulse 2s ease-in-out infinite;
}

.custom-node.is-bounce {
  animation: bounce-in 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.node-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  font-weight: 700;
  font-size: 12px;
  letter-spacing: -0.01em;
  white-space: nowrap;
  color: var(--slate-700);
}

.node-icon {
  font-size: 13px;
  flex-shrink: 0;
}

.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
  background: var(--slate-300);
  transition: background 0.3s ease, box-shadow 0.3s ease;
}

.status-dot.running {
  background: var(--primary);
  box-shadow: 0 0 6px 2px hsl(252 80% 65% / 0.4);
  animation: dot-pulse 1.5s ease-in-out infinite;
}

.status-dot.completed {
  background: var(--success);
}

.status-dot.error {
  background: var(--error);
}

.node-detail {
  margin-top: 2px;
  font-size: 10px;
  color: var(--color-text-secondary);
  font-weight: 600;
  letter-spacing: 0.01em;
}

.detail-enter-active { transition: all 0.3s ease; }
.detail-enter-from { opacity: 0; transform: translateY(-3px); }

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.025); }
}

@keyframes bounce-in {
  0% { transform: scale(0.93); }
  50% { transform: scale(1.06); }
  100% { transform: scale(1); }
}

@keyframes dot-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>
