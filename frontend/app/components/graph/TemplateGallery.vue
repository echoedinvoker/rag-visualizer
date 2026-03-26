<script setup lang="ts">
import { AppstoreOutlined } from '@ant-design/icons-vue'
import type { GraphConfig, TemplateInfo } from '~/types/graph'

const props = defineProps<{
  open: boolean
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  select: [config: GraphConfig]
}>()

const { t } = useI18n()

const templates = ref<TemplateInfo[]>([])
const loading = ref(false)
const loadingId = ref<string | null>(null)

onMounted(async () => {
  const config = useRuntimeConfig()
  try {
    loading.value = true
    const res = await $fetch<{ templates: TemplateInfo[] }>(`${config.public.apiBase}/api/templates`)
    templates.value = res.templates
  } finally {
    loading.value = false
  }
})

async function handleSelect(id: string) {
  const config = useRuntimeConfig()
  try {
    loadingId.value = id
    const detail = await $fetch<{ config: GraphConfig }>(`${config.public.apiBase}/api/templates/${id}`)
    emit('select', detail.config)
    emit('update:open', false)
  } finally {
    loadingId.value = null
  }
}

const templateIcons: Record<string, string> = {
  'simple-rag': '🟢',
  'crag': '🔵',
  'self-rag': '🟣',
  'full-agentic': '🔴',
}

const templateNodeCount: Record<string, number> = {
  'simple-rag': 5,
  'crag': 6,
  'self-rag': 7,
  'full-agentic': 8,
}
</script>

<template>
  <a-modal
    :open="props.open"
    :title="t('gallery.title')"
    :footer="null"
    width="640px"
    @cancel="$emit('update:open', false)"
  >
    <div class="gallery-subtitle">{{ t('gallery.subtitle') }}</div>

    <div v-if="loading" class="gallery-loading">
      <a-spin />
    </div>

    <div v-else class="gallery-grid">
      <div
        v-for="tmpl in templates"
        :key="tmpl.id"
        class="template-card"
        :class="{ loading: loadingId === tmpl.id }"
        @click="handleSelect(tmpl.id)"
      >
        <div class="template-header">
          <span class="template-icon">{{ templateIcons[tmpl.id] || '📋' }}</span>
          <span class="template-name">{{ tmpl.name }}</span>
          <a-tag size="small" color="default" class="node-count">
            {{ templateNodeCount[tmpl.id] || '?' }} nodes
          </a-tag>
        </div>
        <div class="template-desc">{{ tmpl.description }}</div>
        <a-spin v-if="loadingId === tmpl.id" size="small" class="loading-spin" />
      </div>
    </div>
  </a-modal>
</template>

<style scoped>
.gallery-subtitle {
  font-size: 13px;
  color: var(--color-text-muted);
  margin-bottom: var(--space-4);
}

.gallery-loading {
  display: flex;
  justify-content: center;
  padding: var(--space-8) 0;
}

.gallery-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-3);
}

.template-card {
  position: relative;
  padding: var(--space-4);
  border-radius: var(--radius);
  background: var(--color-bg-well);
  outline: 1px solid var(--color-border);
  outline-offset: -1px;
  cursor: pointer;
  transition: background 0.15s, transform 0.15s, box-shadow 0.15s;
}

.template-card:hover {
  background: var(--slate-50);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.template-card.loading {
  opacity: 0.7;
  pointer-events: none;
}

.template-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}

.template-icon {
  font-size: 16px;
}

.template-name {
  font-weight: 700;
  font-size: 14px;
  color: var(--slate-700);
  flex: 1;
}

.node-count {
  font-size: 10px;
}

.template-desc {
  font-size: 12px;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

.loading-spin {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

@media (max-width: 640px) {
  .gallery-grid {
    grid-template-columns: 1fr;
  }
}
</style>
