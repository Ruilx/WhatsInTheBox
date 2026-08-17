// 图标按钮（无 emoji，禁止图标用 SVG/Icon 组件）。
// hover 提升亮度以示可交互；禁用态降透明度并禁点击。
// 用法：图标放 #icon 插槽，文字用 label 或默认插槽。

<template>
  <button
    class="wb-icon-btn"
    :class="[
      `wb-icon-btn--${variant}`,
      { 'is-block': block, 'is-disabled': disabled },
    ]"
    :type="nativeType"
    :disabled="disabled"
    :title="title"
    @click="handleClick"
  >
    <span v-if="$slots.icon" class="wb-icon-btn__icon"><slot name="icon" /></span>
    <span v-if="label" class="wb-icon-btn__label">{{ label }}</span>
    <slot v-else />
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    label?: string
    variant?: 'default' | 'primary' | 'danger' | 'ghost'
    block?: boolean
    disabled?: boolean
    title?: string
    nativeType?: 'button' | 'submit' | 'reset'
  }>(),
  {
    variant: 'default',
    block: false,
    disabled: false,
    nativeType: 'button',
  },
)

const emit = defineEmits<{ (e: 'click', ev: MouseEvent): void }>()

const cls = computed(() => [
  'wb-icon-btn',
  `wb-icon-btn--${props.variant}`,
  { 'is-block': props.block, 'is-disabled': props.disabled },
])

function handleClick(ev: MouseEvent): void {
  if (props.disabled) return
  emit('click', ev)
}
</script>

<style scoped>
.wb-icon-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  background: var(--color-bg-elevated);
  color: var(--color-text);
  font-size: 14px;
  font-family: inherit;
  cursor: pointer;
  line-height: 1.4;
  white-space: nowrap;
  transition: filter var(--transition), background var(--transition),
    border-color var(--transition), opacity var(--transition);
}
.wb-icon-btn:hover:not(.is-disabled) {
  filter: brightness(1.12);
}
.wb-icon-btn:active:not(.is-disabled) {
  filter: brightness(0.92);
}
.wb-icon-btn.is-disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.wb-icon-btn.is-block {
  width: 100%;
  justify-content: center;
}
.wb-icon-btn--primary {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: #fff;
}
.wb-icon-btn--danger {
  background: var(--color-danger);
  border-color: var(--color-danger);
  color: #fff;
}
.wb-icon-btn--ghost {
  background: transparent;
  border-color: transparent;
}
.wb-icon-btn--ghost:hover:not(.is-disabled) {
  background: var(--color-bg-hover);
}
.wb-icon-btn__icon {
  display: inline-flex;
  align-items: center;
}
.wb-icon-btn__icon :deep(svg) {
  width: 16px;
  height: 16px;
}
</style>
