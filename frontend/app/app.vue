<script setup lang="ts">
import { ConfigProvider, theme } from 'ant-design-vue'

const antTheme = {
  token: {
    colorPrimary: '#6C5CE7',
    borderRadius: 12,
    colorBgContainer: '#FAFAFE',
    fontFamily: '"Nunito", "Noto Sans TC", sans-serif',
  },
}
</script>

<template>
  <ConfigProvider :theme="antTheme">
    <NuxtRouteAnnouncer />
    <NuxtPage />
  </ConfigProvider>
</template>
