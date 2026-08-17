// 复制 URL 按钮（dev-plan v4 §7.11 / §1.1：仅复制完整 URL，不生成/展示二维码）。
// 默认复制当前页面完整链接；可传 url 覆盖（如复制活动/箱子 URL）。
// 复用 utils/url.ts 的 copyToClipboard（含 execCommand 降级）。

<template>
  <IconButton :variant="variant" :label="label" :title="title" @click="onCopy">
    <template #icon>
      <Icon name="link" />
    </template>
  </IconButton>
</template>

<script setup lang="ts">
import { message } from 'ant-design-vue'
import IconButton from './IconButton.vue'
import Icon from './Icon.vue'
import { copyToClipboard } from '@/utils/url'

const props = withDefaults(
  defineProps<{
    url?: string
    label?: string
    title?: string
    variant?: 'default' | 'primary' | 'danger' | 'ghost'
  }>(),
  {
    label: '复制 URL',
    title: '复制当前页面链接',
    variant: 'default',
  },
)

async function onCopy(): Promise<void> {
  const target = props.url || window.location.href
  const ok = await copyToClipboard(target)
  if (ok) message.success('已复制链接')
  else message.error('复制失败，请手动复制')
}
</script>
