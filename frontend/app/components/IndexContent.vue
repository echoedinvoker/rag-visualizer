<script setup lang="ts">
import type { GraphConfig } from '~/types/graph'

const props = defineProps<{
  locale: string
  exampleQueries: { label: string; query: string }[]
}>()

const emit = defineEmits<{
  example: [query: string]
}>()

const query = defineModel<string>('query', { required: true })
const mode = defineModel<'editing' | 'running'>('mode', { required: true })

const { t } = useI18n()

// Graph editor (DnD, serialization, templates)
const { toGraphConfig, loadGraphConfig, clearGraph } = useGraphEditor()
const { applyAutoLayout } = useAutoLayout()

// Graph state (node status tracking for execution animations)
const { nodes, edges, updateNode, resetAll } = useGraphState()

// Graph execution (SSE streaming)
const { isRunning, logs, report, error, runPipeline, abort } = useGraphExecution(updateNode, resetAll)

// Sync mode with isRunning
watch(isRunning, (running) => {
  mode.value = running ? 'running' : 'editing'
})

// Selected node for config panel
const selectedNodeId = ref<string | null>(null)
const selectedNode = computed(() => {
  if (!selectedNodeId.value) return null
  return nodes.value.find(n => n.id === selectedNodeId.value) || null
})

function onNodeClick(_event: any, node: any) {
  selectedNodeId.value = node.id
}

function handleSearch(value: string) {
  if (!value.trim() || isRunning.value) return
  const config = toGraphConfig()
  runPipeline(config, value.trim(), props.locale)
}

function handleLoadTemplate(config: GraphConfig) {
  loadGraphConfig(config)
  nextTick(() => applyAutoLayout())
}

function handleAutoLayout() {
  applyAutoLayout()
}

function handleClear() {
  clearGraph()
  selectedNodeId.value = null
}
</script>

<template>
  <main class="main-content">
    <!-- Query Input -->
    <section class="section">
      <a-card :bordered="false" class="card">
        <a-input-search
          v-model:value="query"
          size="large"
          :placeholder="t('research.placeholder')"
          :enter-button="isRunning ? t('research.abort') : t('research.start')"
          :loading="isRunning"
          @search="isRunning ? abort() : handleSearch(query)"
        />
        <div class="examples">
          <span class="examples-label">{{ t('research.examples') }}</span>
          <a-tag
            v-for="ex in exampleQueries"
            :key="ex.label"
            color="purple"
            class="example-tag"
            @click="query = ex.query"
          >
            {{ ex.label }}
          </a-tag>
        </div>
        <a-alert
          v-if="error"
          type="error"
          :message="error"
          show-icon
          closable
          style="margin-top: 12px"
          @close="error = null"
        />
      </a-card>
    </section>

    <!-- Three-column layout: Sidebar + Canvas + Config -->
    <section class="section studio-row">
      <!-- Left: Node Sidebar + File Upload -->
      <div class="sidebar-col" :class="{ collapsed: mode === 'running' }">
        <a-card :bordered="false" class="card sidebar-card">
          <GraphNodeSidebar />
          <div class="sidebar-divider" />
          <div class="sidebar-section">
            <UploadFileUpload />
          </div>
        </a-card>
      </div>

      <!-- Center: Toolbar + Canvas + Log -->
      <div class="center-col">
        <a-card :bordered="false" class="card graph-card">
          <GraphGraphToolbar
            :disabled="isRunning"
            @clear="handleClear"
            @auto-layout="handleAutoLayout"
            @load-template="handleLoadTemplate"
          />
          <GraphFlowCanvas
            :nodes="nodes"
            :edges="edges"
            :mode="mode"
            @node-click="onNodeClick"
          />
        </a-card>

        <a-card :bordered="false" class="card log-card">
          <PanelLogPanel :logs="logs" />
        </a-card>
      </div>

      <!-- Right: Node Config Panel (shown when a node is selected) -->
      <div v-if="selectedNode && mode === 'editing'" class="config-col">
        <a-card :bordered="false" class="card config-card">
          <GraphNodeConfigPanel
            :node="selectedNode"
            @close="selectedNodeId = null"
          />
        </a-card>
      </div>
    </section>

    <!-- Report below -->
    <section v-if="report" class="section">
      <a-card :bordered="false" class="card">
        <PanelReportView :report="report" />
      </a-card>
    </section>
  </main>
</template>

<style scoped>
.main-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: var(--space-6) var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.card {
  border-radius: var(--radius-lg) !important;
  box-shadow: var(--shadow-md);
  outline: 1px solid var(--color-border);
  outline-offset: -1px;
  border: none !important;
  background: var(--color-bg-card);
}

.studio-row {
  display: flex;
  gap: var(--space-3);
  align-items: flex-start;
}

.sidebar-col {
  flex-shrink: 0;
  transition: width 0.3s ease, opacity 0.3s ease;
}

.sidebar-col.collapsed {
  width: 0;
  opacity: 0;
  overflow: hidden;
}

.sidebar-card {
  height: fit-content;
}

.sidebar-card :deep(.ant-card-body) {
  padding: 0;
}

.sidebar-divider {
  height: 1px;
  background: var(--color-border);
  margin: var(--space-2) var(--space-3);
}

.sidebar-section {
  padding: 0 var(--space-3) var(--space-3);
}

.center-col {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.graph-card :deep(.ant-card-body) {
  padding: 0;
}

.log-card {
  max-height: 280px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-well) !important;
  box-shadow: var(--shadow-sm) !important;
  outline-color: hsl(215 25% 15% / 0.05);
}

.log-card :deep(.ant-card-body) {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: transparent;
}

.config-col {
  width: 260px;
  flex-shrink: 0;
}

.config-card {
  position: sticky;
  top: var(--space-4);
}

.examples {
  margin-top: var(--space-3);
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
}

.examples-label {
  font-size: 12px;
  color: var(--color-text-muted);
  font-weight: 500;
}

.example-tag {
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.example-tag:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
}

/* Mobile */
@media (max-width: 768px) {
  .main-content {
    padding: var(--space-3);
  }

  .studio-row {
    flex-direction: column;
  }

  .sidebar-col {
    width: 100% !important;
  }

  .config-col {
    width: 100%;
  }

  .log-card {
    max-height: 200px;
  }
}
</style>
