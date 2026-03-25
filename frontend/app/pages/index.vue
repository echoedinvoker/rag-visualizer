<script setup lang="ts">
const { t, locale } = useI18n()

const { nodes, edges, updateNode, resetAll } = useGraphState()
const { isResearching, logs, report, error, startResearch, abort } = useResearchStream(updateNode, resetAll)

const query = ref('')

const exampleQueries = [
  { label: 'LangGraph', query: 'What is LangGraph and how does it work?' },
  { label: 'RAG', query: 'How does Retrieval Augmented Generation work?' },
  { label: 'Agents', query: 'How to build AI agents with LangChain?' },
  { label: 'Streaming', query: 'How does streaming work in LangGraph?' },
]

function handleSearch(value: string) {
  if (!value.trim() || isResearching.value) return
  startResearch(value.trim(), locale.value)
}

function handleExample(q: string) {
  query.value = q
  handleSearch(q)
}
</script>

<template>
  <div class="page">
    <LayoutAppHeader />

    <main class="main-content">
      <!-- Query Input -->
      <section class="section">
        <a-card :bordered="false" class="card">
          <a-input-search
            v-model:value="query"
            size="large"
            :placeholder="t('research.placeholder')"
            :enter-button="isResearching ? t('research.abort') : t('research.start')"
            :loading="isResearching"
            @search="isResearching ? abort() : handleSearch(query)"
          />
          <div class="examples">
            <span class="examples-label">{{ t('research.examples') }}</span>
            <a-tag
              v-for="ex in exampleQueries"
              :key="ex.label"
              color="purple"
              class="example-tag"
              @click="handleExample(ex.query)"
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

      <!-- Graph + Log side by side -->
      <section class="section graph-log-row">
        <a-card :bordered="false" class="card graph-card">
          <GraphFlowCanvas :nodes="nodes" :edges="edges" />
        </a-card>
        <a-card :bordered="false" class="card log-card">
          <PanelLogPanel :logs="logs" />
        </a-card>
      </section>

      <!-- Report below -->
      <section v-if="report" class="section">
        <a-card :bordered="false" class="card">
          <PanelReportView :report="report" />
        </a-card>
      </section>
    </main>
  </div>
</template>

<style scoped>
.page {
  min-height: 100vh;
  background: var(--color-bg);
}

.main-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--space-6) var(--space-6);
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

/* 陰影分層 + 半透明外框: layered shadow + ring instead of solid border */
.card {
  border-radius: var(--radius-lg) !important;
  box-shadow: var(--shadow-md);
  outline: 1px solid var(--color-border);
  outline-offset: -1px;
  border: none !important;
  background: var(--color-bg-card);
}

.graph-log-row {
  display: flex;
  gap: var(--space-4);
  align-items: stretch;
}

.graph-card {
  flex: 3;
  min-width: 0;
}

/* 深度與層次: log card 用 well container 凹陷感 */
.log-card {
  flex: 2;
  min-width: 0;
  max-height: 500px;
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

/* 間距系統: examples 用 space tokens */
.examples {
  margin-top: var(--space-3);
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
}

/* 視覺層級: 弱化次要 label */
.examples-label {
  font-size: 12px;
  color: var(--color-text-muted);
  font-weight: 500;
}

/* 按鈕微互動 */
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

  .graph-log-row {
    flex-direction: column;
  }

  .log-card {
    max-height: 300px;
  }
}
</style>
