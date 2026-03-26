<script setup lang="ts">
const { t } = useI18n()
const { getNodeTypesByCategory } = useNodeRegistry()

const categories = getNodeTypesByCategory()

function onDragStart(event: DragEvent, nodeType: string) {
  if (!event.dataTransfer) return
  event.dataTransfer.setData('application/rag-node-type', nodeType)
  event.dataTransfer.effectAllowed = 'move'
}
</script>

<template>
  <div class="node-sidebar">
    <div class="sidebar-title">{{ t('sidebar.title') }}</div>

    <div v-for="group in categories" :key="group.category" class="category-group">
      <div class="category-label">{{ t(group.label) }}</div>
      <div
        v-for="nodeInfo in group.nodes"
        :key="nodeInfo.type"
        class="node-item"
        draggable="true"
        @dragstart="onDragStart($event, nodeInfo.type)"
      >
        <span class="node-icon">{{ nodeInfo.icon }}</span>
        <span class="node-name">{{ t(nodeInfo.label) }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.node-sidebar {
  width: 180px;
  flex-shrink: 0;
  padding: var(--space-3);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  overflow-y: auto;
}

.sidebar-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--color-text-secondary);
  letter-spacing: -0.01em;
  margin-bottom: var(--space-1);
}

.category-group {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.category-label {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-muted);
  margin-top: var(--space-1);
  margin-bottom: 2px;
}

.node-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: var(--radius-sm);
  cursor: grab;
  font-size: 12px;
  font-weight: 600;
  color: var(--slate-700);
  background: var(--color-bg-card);
  outline: 1px solid var(--color-border);
  outline-offset: -1px;
  transition: background 0.15s, transform 0.15s, box-shadow 0.15s;
  user-select: none;
}

.node-item:hover {
  background: var(--slate-50);
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
}

.node-item:active {
  cursor: grabbing;
  transform: scale(0.97);
}

.node-icon {
  font-size: 14px;
  flex-shrink: 0;
}

.node-name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
