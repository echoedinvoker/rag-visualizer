<script setup lang="ts">
const props = defineProps<{
  report: { content: string; sources: string[] } | null
}>()

const { t } = useI18n()
const copied = ref(false)

async function copyReport() {
  if (!props.report) return
  await navigator.clipboard.writeText(props.report.content)
  copied.value = true
  setTimeout(() => { copied.value = false }, 2000)
}
</script>

<template>
  <Transition name="slide">
    <div v-if="report" class="report-view">
      <div class="report-header">
        <h3>{{ t('report.title') }}</h3>
        <a-button size="small" @click="copyReport">
          {{ copied ? t('report.copied') : t('report.copy') }}
        </a-button>
      </div>
      <div class="report-content" v-html="renderMarkdown(report.content)" />
    </div>
  </Transition>
</template>

<script lang="ts">
// Simple markdown renderer (no external dep needed for basic formatting)
function renderMarkdown(md: string): string {
  return md
    .replace(/^### (.+)$/gm, '<h4>$1</h4>')
    .replace(/^## (.+)$/gm, '<h3>$1</h3>')
    .replace(/^# (.+)$/gm, '<h2>$1</h2>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`(.+?)`/g, '<code>$1</code>')
    .replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/^/, '<p>')
    .replace(/$/, '</p>')
}
</script>

<style scoped>
.report-view {
  padding-top: var(--space-2);
}

.report-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-4);
}

.report-header h3 {
  font-size: 13px;
  font-weight: 700;
  color: var(--color-text-secondary);
  letter-spacing: 0.02em;
  text-transform: uppercase;
  margin: 0;
}

/* 排版微調: 最佳閱讀寬度 + 行高 */
.report-content {
  font-size: 14px;
  line-height: 1.7;
  color: var(--color-text);
  max-width: 65ch;
}

/* 排版: heading 收緊字距 + 行高 */
.report-content :deep(h2) {
  font-size: 18px;
  font-weight: 700;
  margin: var(--space-6) 0 var(--space-2);
  color: var(--slate-800);
  letter-spacing: -0.02em;
  line-height: 1.25;
}

.report-content :deep(h3) {
  font-size: 15px;
  font-weight: 700;
  margin: var(--space-4) 0 var(--space-1);
  color: var(--slate-700);
  letter-spacing: -0.01em;
  line-height: 1.3;
}

.report-content :deep(h4) {
  font-size: 14px;
  font-weight: 600;
  margin: var(--space-3) 0 var(--space-1);
  color: var(--slate-700);
}

.report-content :deep(code) {
  background: var(--slate-100);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12.5px;
  color: var(--primary-700);
}

/* 按鈕層級: link 用品牌色（可互動元素） */
.report-content :deep(a) {
  color: var(--primary);
  text-decoration: none;
  font-weight: 600;
}

.report-content :deep(a:hover) {
  text-decoration: underline;
}

.report-content :deep(ul) {
  padding-left: var(--space-6);
  margin: var(--space-2) 0;
}

.report-content :deep(li) {
  margin-bottom: var(--space-1);
}

.report-content :deep(strong) {
  color: var(--slate-800);
  font-weight: 700;
}

/* Transition */
.slide-enter-active {
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.slide-enter-from {
  opacity: 0;
  transform: translateY(12px);
}
</style>
