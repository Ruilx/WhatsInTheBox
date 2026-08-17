// 根布局（dev-plan v4 §1.1 / §3.3）。
// 顶部导航 + 路由出口 + 深浅色主题切换 + 路由淡入淡出过渡。
// 登录页隐藏顶栏（全屏登录卡片）。
// 用 antd ConfigProvider 包裹根组件，按 themeState 响应式切换暗色算法，
// 让 a-input / a-table / a-tag / a-select 等组件随暗色适配（label、输入框、表格、标签等）。
// 页面级 CSS 变量（--color-text 等）仍由 utils/theme.ts 在 html.dark 上驱动，
// 二者叠加互不冲突：ConfigProvider 管 antd 组件 token，CSS 变量管页面级样式。

<template>
  <a-config-provider :theme="antdTheme">
    <div class="app-root">
      <TopNav v-if="showNav" />
      <main class="app-main" :class="{ 'app-main--full': !showNav }">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </a-config-provider>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { theme } from 'ant-design-vue'
import TopNav from '@/components/TopNav.vue'
import { themeState } from '@/utils/theme'

const route = useRoute()
// 登录页不显示顶栏；其余页面（含 404）均显示
const showNav = computed(() => route.name !== 'login')

// 按当前暗色状态响应式切换 antd 算法。themeState 为 reactive，切换时自动生效。
const antdTheme = computed(() => ({
  algorithm:
    themeState.mode === 'dark' ? theme.darkAlgorithm : theme.defaultAlgorithm,
}))
</script>
