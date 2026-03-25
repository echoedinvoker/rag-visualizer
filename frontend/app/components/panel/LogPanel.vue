<script setup lang="ts">
import type { LogEntry } from '~/composables/useResearchStream'

const props = defineProps<{
  logs: LogEntry[]
}>()

const { t } = useI18n()

const logListRef = ref<HTMLElement>()

watch(() => props.logs.length, () => {
  nextTick(() => {
    if (logListRef.value) {
      logListRef.value.scrollTop = logListRef.value.scrollHeight
    }
  })
})

const NODE_COLORS: Record<string, string> = {
  router: '#6C5CE7',
  retriever: '#0984E3',
  web_search: '#00CEC9',
  grader: '#6C5CE7',
  generator: '#FDCB6E',
  hallucination_checker: '#FF6B6B',
  relevance_checker: '#FF6B6B',
  report_builder: '#00B894',
  system: '#94a3b8',
}

function formatMessage(log: LogEntry): string {
  if (log.message.startsWith('log.')) {
    return t(log.message, log.details || {})
  }
  return log.message
}

function isSuccess(log: LogEntry): boolean {
  return log.event.includes('complete') || log.event.includes('pass')
}

function isFailure(log: LogEntry): boolean {
  return log.event.includes('fail') || log.event === 'error'
}
</script>

<template>
  <div class="log-panel">
    <!-- 視覺層級: title 用 secondary 色 + semibold -->
    <h3 class="log-title">{{ t('log.title') }}</h3>
    <div ref="logListRef" class="log-list">
      <div v-if="logs.length === 0" class="log-empty">
        <span class="log-empty-dot" />
        <span>Waiting for research...</span>
      </div>
      <TransitionGroup name="log" tag="div" class="log-items">
        <div
          v-for="log in logs"
          :key="log.id"
          class="log-entry"
          :class="{
            'log-success': isSuccess(log),
            'log-failure': isFailure(log),
          }"
        >
          <!-- 質感一致性: CSS dot 取代 emoji -->
          <span
            class="log-dot"
            :style="{ backgroundColor: NODE_COLORS[log.node] || '#94a3b8' }"
          />
          <span class="log-message">{{ formatMessage(log) }}</span>
        </div>
      </TransitionGroup>
    </div>
  </div>
</template>

<style scoped>
.log-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}

.log-title {
  font-size: 13px;
  font-weight: 700;
  margin-bottom: var(--space-3);
  color: var(--color-text-secondary);
  letter-spacing: 0.02em;
  text-transform: uppercase;
  flex-shrink: 0;
}

.log-list {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
  scrollbar-width: thin;
  scrollbar-color: var(--slate-200) transparent;
}

.log-items {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.log-empty {
  color: var(--color-text-muted);
  font-size: 13px;
  text-align: center;
  padding: var(--space-8) var(--space-4);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
}

.log-empty-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--slate-200);
}

.log-entry {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: 12px;
  line-height: 1.4;
  /* 間距: button-like padding ratio */
  padding: 5px var(--space-3);
  border-radius: var(--radius-sm);
  transition: background 0.2s ease;
}

.log-entry:hover {
  background: hsl(215 25% 15% / 0.03);
}

.log-entry.log-success {
  background: hsl(160 84% 39% / 0.04);
}

.log-entry.log-failure {
  background: hsl(0 100% 64% / 0.04);
}

.log-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.log-message {
  /* 視覺層級: log text 用 secondary 不搶主角 */
  color: var(--color-text-secondary);
  font-weight: 500;
}

/* Transition: 彈性進場 */
.log-enter-active {
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.log-enter-from {
  opacity: 0;
  transform: translateX(-6px) scale(0.97);
}
</style>
