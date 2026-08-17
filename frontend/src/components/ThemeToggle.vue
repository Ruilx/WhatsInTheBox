<!-- 深浅色切换（dev-plan v4 §1.1）。 -->
<!-- 复用 utils/theme.ts 的响应式 themeState（<html class="dark"> 驱动 CSS 变量）。 -->
<!-- 跟随系统默认；手动切换后写入 localStorage，刷新后保持。 -->

<template>
  <IconButton
    variant="ghost"
    :title="themeState.mode === 'dark' ? '切换到浅色' : '切换到深色'"
    @click="onToggle"
  >
    <template #icon>
      <Icon :name="themeState.mode === 'dark' ? 'sun' : 'moon'" />
    </template>
    <span class="theme-toggle__text">
      {{ themeState.mode === 'dark' ? '浅色' : '深色' }}
    </span>
  </IconButton>
</template>

<script setup lang="ts">
import IconButton from './IconButton.vue'
import Icon from './Icon.vue'
import { themeState, toggleTheme } from '@/utils/theme'

function onToggle(): void {
  toggleTheme()
}
</script>

<style scoped>
.theme-toggle__text {
  font-size: 13px;
}
</style>
