<script setup lang="ts">
import {
  ClearOutlined,
  LayoutOutlined,
  ExportOutlined,
  ImportOutlined,
  AppstoreOutlined,
} from '@ant-design/icons-vue'
import type { GraphConfig } from '~/types/graph'

const emit = defineEmits<{
  clear: []
  autoLayout: []
  loadTemplate: [config: GraphConfig]
}>()

const props = defineProps<{
  disabled?: boolean
}>()

const { t } = useI18n()
const { toGraphConfig, loadGraphConfig } = useGraphEditor()

const galleryOpen = ref(false)

function handleTemplateSelect(config: GraphConfig) {
  emit('loadTemplate', config)
}

function handleExport() {
  const config = toGraphConfig()
  const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'pipeline.json'
  a.click()
  URL.revokeObjectURL(url)
}

function handleImport() {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.json'
  input.onchange = async (e) => {
    const file = (e.target as HTMLInputElement).files?.[0]
    if (!file) return
    const text = await file.text()
    try {
      const config = JSON.parse(text) as GraphConfig
      loadGraphConfig(config)
      emit('autoLayout')
    } catch {
      // invalid JSON
    }
  }
  input.click()
}
</script>

<template>
  <div class="graph-toolbar">
    <div class="toolbar-left">
      <a-button size="small" :disabled="props.disabled" @click="galleryOpen = true">
        <template #icon><AppstoreOutlined /></template>
        {{ t('toolbar.templates') }}
      </a-button>
    </div>

    <div class="toolbar-right">
      <a-tooltip :title="t('toolbar.auto_layout')">
        <a-button size="small" :disabled="props.disabled" @click="$emit('autoLayout')">
          <template #icon><LayoutOutlined /></template>
        </a-button>
      </a-tooltip>
      <a-tooltip :title="t('toolbar.export')">
        <a-button size="small" :disabled="props.disabled" @click="handleExport">
          <template #icon><ExportOutlined /></template>
        </a-button>
      </a-tooltip>
      <a-tooltip :title="t('toolbar.import')">
        <a-button size="small" :disabled="props.disabled" @click="handleImport">
          <template #icon><ImportOutlined /></template>
        </a-button>
      </a-tooltip>
      <a-tooltip :title="t('toolbar.clear')">
        <a-button size="small" danger :disabled="props.disabled" @click="$emit('clear')">
          <template #icon><ClearOutlined /></template>
        </a-button>
      </a-tooltip>
    </div>

    <GraphTemplateGallery
      v-model:open="galleryOpen"
      @select="handleTemplateSelect"
    />
  </div>
</template>

<style scoped>
.graph-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 12px;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-bg-card);
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 6px;
}
</style>
