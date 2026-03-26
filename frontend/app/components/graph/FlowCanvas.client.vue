<script setup lang="ts">
import { VueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { MiniMap } from '@vue-flow/minimap'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import '@vue-flow/controls/dist/style.css'
import '@vue-flow/minimap/dist/style.css'
import CustomNode from './nodes/CustomNode.vue'
import { FLOW_ID } from '~/composables/useGraphEditor'

import type { Node, Edge } from '@vue-flow/core'

const props = defineProps<{
  nodes: Node[]
  edges: Edge[]
  mode?: 'editing' | 'running'
}>()

const isEditing = computed(() => props.mode !== 'running')

const { onDragOver, onDrop, isValidConnection, onConnect } = useGraphEditor()
</script>

<template>
  <div
    class="flow-wrapper"
    @dragover="isEditing ? onDragOver($event) : undefined"
    @drop="isEditing ? onDrop($event) : undefined"
  >
    <VueFlow
      :id="FLOW_ID"
      :nodes="nodes"
      :edges="edges"
      :default-viewport="{ x: 20, y: 10, zoom: 0.78 }"
      :nodes-draggable="isEditing"
      :nodes-connectable="isEditing"
      :elements-selectable="isEditing"
      :delete-key-code="isEditing ? 'Backspace' : null"
      :pan-on-drag="true"
      :zoom-on-scroll="true"
      :is-valid-connection="isValidConnection"
      fit-view-on-init
      @connect="onConnect"
    >
      <template #node-custom="nodeProps">
        <CustomNode :data="nodeProps.data" />
      </template>

      <Background :gap="24" :size="1" pattern-color="#e8e8f0" />
      <Controls position="bottom-left" :show-fit-view="true" :show-interactive="false" />
      <MiniMap position="bottom-right" />
    </VueFlow>
  </div>
</template>

<style scoped>
.flow-wrapper {
  width: 100%;
  height: 520px;
  border-radius: 0 0 var(--radius-lg) var(--radius-lg);
  overflow: hidden;
}

/* Soften Vue Flow default edge labels */
.flow-wrapper :deep(.vue-flow__edge-text) {
  font-size: 10px;
  fill: #bbb;
}

/* Hide edge label backgrounds */
.flow-wrapper :deep(.vue-flow__edge-textbg) {
  fill: var(--color-bg-card, #fafafe);
  fill-opacity: 0.9;
}

/* Animated edges: flowing dashes */
.flow-wrapper :deep(.vue-flow__edge.animated path) {
  stroke-dasharray: 6 4;
  animation: edge-flow 0.6s linear infinite;
}

@keyframes edge-flow {
  to { stroke-dashoffset: -10; }
}

/* MiniMap styling */
.flow-wrapper :deep(.vue-flow__minimap) {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}
</style>
