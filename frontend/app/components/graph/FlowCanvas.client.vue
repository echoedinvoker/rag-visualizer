<script setup lang="ts">
import { VueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import '@vue-flow/controls/dist/style.css'
import CustomNode from './nodes/CustomNode.vue'

import type { Node, Edge } from '@vue-flow/core'

defineProps<{
  nodes: Node[]
  edges: Edge[]
}>()
</script>

<template>
  <div class="flow-wrapper">
    <VueFlow
      :nodes="nodes"
      :edges="edges"
      :default-viewport="{ x: 20, y: 10, zoom: 0.78 }"
      :nodes-draggable="false"
      :pan-on-drag="true"
      :zoom-on-scroll="true"
      fit-view-on-init
    >
      <template #node-custom="nodeProps">
        <CustomNode :data="nodeProps.data" />
      </template>

      <Background :gap="24" :size="1" pattern-color="#e8e8f0" />
      <Controls position="bottom-left" :show-fit-view="true" :show-interactive="false" />
    </VueFlow>
  </div>
</template>

<style scoped>
.flow-wrapper {
  width: 100%;
  height: 480px;
  border-radius: var(--radius, 12px);
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
</style>
