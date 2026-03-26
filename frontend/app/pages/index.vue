<script setup lang="ts">
const { t, locale } = useI18n()

const query = ref('')
const mode = ref<'editing' | 'running'>('editing')

const exampleQueries = [
  { label: 'LangGraph', query: 'What is LangGraph and how does it work?' },
  { label: 'RAG', query: 'How does Retrieval Augmented Generation work?' },
  { label: 'Agents', query: 'How to build AI agents with LangChain?' },
  { label: 'Streaming', query: 'How does streaming work in LangGraph?' },
]
</script>

<template>
  <div class="page">
    <LayoutAppHeader />

    <IndexContent
      v-model:query="query"
      v-model:mode="mode"
      :locale="locale"
      :example-queries="exampleQueries"
    />
  </div>
</template>

<style scoped>
.page {
  min-height: 100vh;
  background: var(--color-bg);
}
</style>
