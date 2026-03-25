<script setup lang="ts">
const { locale, locales, setLocale } = useI18n()
const { t } = useI18n()

const availableLocales = computed(() =>
  locales.value.filter((l: any) => l.code !== locale.value)
)
</script>

<template>
  <header class="app-header">
    <div class="header-left">
      <div class="logo-mark">
          <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="16" cy="8" r="3" fill="white" opacity="0.9"/>
            <circle cx="8" cy="20" r="3" fill="white" opacity="0.9"/>
            <circle cx="24" cy="20" r="3" fill="white" opacity="0.9"/>
            <circle cx="16" cy="28" r="2.5" fill="white" opacity="0.7"/>
            <line x1="16" y1="11" x2="9.5" y2="17.5" stroke="white" stroke-width="1.5" opacity="0.6"/>
            <line x1="16" y1="11" x2="22.5" y2="17.5" stroke="white" stroke-width="1.5" opacity="0.6"/>
            <line x1="8" y1="23" x2="16" y2="26" stroke="white" stroke-width="1.5" opacity="0.5"/>
            <line x1="24" y1="23" x2="16" y2="26" stroke="white" stroke-width="1.5" opacity="0.5"/>
            <line x1="10.5" y1="19" x2="21.5" y2="19" stroke="white" stroke-width="1.2" opacity="0.4"/>
          </svg>
        </div>
      <div>
        <!-- 排版: 標題收緊字距 -->
        <h1 class="title">{{ t('app.title') }}</h1>
        <!-- 視覺層級: subtitle 用 muted 色弱化 -->
        <p class="subtitle">{{ t('app.subtitle') }}</p>
      </div>
    </div>
    <div class="header-right">
      <a-button
        v-for="loc in availableLocales"
        :key="loc.code"
        size="small"
        type="text"
        class="locale-btn"
        @click="setLocale(loc.code)"
      >
        {{ loc.name }}
      </a-button>
    </div>
  </header>
</template>

<style scoped>
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-3) var(--space-6);
  background: var(--color-bg-card);
  /* 半透明外框取代實色邊框 */
  border-bottom: none;
  box-shadow: 0 1px 0 var(--color-border);
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.logo-mark {
  width: 34px;
  height: 34px;
  border-radius: var(--radius-sm);
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-400) 100%);
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 3px;
}

/* 排版微調: 標題收緊字距、用 semibold 而非 extra-bold */
.title {
  font-size: 17px;
  font-weight: 700;
  color: var(--slate-800);
  margin: 0;
  line-height: 1.2;
  letter-spacing: -0.02em;
}

/* 視覺層級: subtitle 用 muted 色 + regular weight 退後 */
.subtitle {
  font-size: 11.5px;
  color: var(--color-text-muted);
  margin: 0;
  font-weight: 500;
}

.locale-btn {
  color: var(--color-text-secondary);
  font-weight: 600;
  font-size: 12px;
}
</style>
