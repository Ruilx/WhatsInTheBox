// 顶部导航（dev-plan v4 §3.3 全局页入口 + 主题切换 + 用户 + 登出）。
// 活动/联合物品/日志/搜索入口；右侧主题切换、当前用户、登出。
// 移动端使用汉堡菜单收起导航链接，避免窄屏下链接换行与标题/右侧图标重叠。

<template>
  <header class="topnav">
    <div class="topnav__inner">
      <RouterLink :to="activitiesUrl()" class="topnav__brand">箱子里面有什么</RouterLink>

      <!-- 桌面端导航 -->
      <nav class="topnav__links topnav__links--desktop" aria-label="桌面导航">
        <RouterLink :to="activitiesUrl()">
          <Icon name="box" /><span>活动</span>
        </RouterLink>
        <RouterLink :to="combosUrl()">
          <Icon name="combo" /><span>联合物品</span>
        </RouterLink>
        <RouterLink :to="logsUrl()">
          <Icon name="log" /><span>日志</span>
        </RouterLink>
        <RouterLink :to="searchUrl()">
          <Icon name="search" /><span>搜索</span>
        </RouterLink>
      </nav>

      <div class="topnav__right">
        <ThemeToggle />
        <span v-if="auth.username" class="topnav__user topnav__user--desktop">{{ auth.username }}</span>
        <IconButton
          v-if="auth.username"
          class="topnav__logout--desktop"
          variant="ghost"
          title="登出"
          @click="onLogout"
        >
          <template #icon><Icon name="logout" /></template>
        </IconButton>

        <!-- 移动端汉堡菜单按钮 -->
        <IconButton
          class="topnav__menu-btn"
          variant="ghost"
          :title="menuOpen ? '关闭菜单' : '打开菜单'"
          :aria-expanded="menuOpen"
          aria-controls="topnav-mobile-menu"
          aria-label="导航菜单"
          @click="toggleMenu"
        >
          <template #icon>
            <Icon :name="menuOpen ? 'close' : 'menu'" />
          </template>
        </IconButton>
      </div>
    </div>

    <!-- 移动端菜单打开时的点击外部遮罩（关闭菜单） -->
    <div
      v-if="menuOpen"
      class="topnav__backdrop"
      aria-hidden="true"
      @click="closeMenu"
    ></div>

    <!-- 移动端下拉导航面板 -->
    <nav
      v-show="menuOpen"
      id="topnav-mobile-menu"
      class="topnav__links topnav__links--mobile"
      aria-label="移动导航"
    >
      <RouterLink :to="activitiesUrl()" @click="closeMenu">
        <Icon name="box" /><span>活动</span>
      </RouterLink>
      <RouterLink :to="combosUrl()" @click="closeMenu">
        <Icon name="combo" /><span>联合物品</span>
      </RouterLink>
      <RouterLink :to="logsUrl()" @click="closeMenu">
        <Icon name="log" /><span>日志</span>
      </RouterLink>
      <RouterLink :to="searchUrl()" @click="closeMenu">
        <Icon name="search" /><span>搜索</span>
      </RouterLink>
      <div v-if="auth.username" class="topnav__mobile-meta">
        <span class="topnav__user">{{ auth.username }}</span>
        <IconButton variant="ghost" label="登出" @click="onLogout">
          <template #icon><Icon name="logout" /></template>
        </IconButton>
      </div>
    </nav>
  </header>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import ThemeToggle from './ThemeToggle.vue'
import IconButton from './IconButton.vue'
import Icon from './Icon.vue'
import { useAuthStore } from '@/store/auth'
import {
  GLOBAL_PREFIX,
  activitiesUrl,
  combosUrl,
  logsUrl,
  searchUrl,
} from '@/utils/url'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const menuOpen = ref(false)

function toggleMenu(): void {
  menuOpen.value = !menuOpen.value
}

function closeMenu(): void {
  menuOpen.value = false
}

// 视口从移动端拉宽到桌面时收起菜单，避免回到移动端时菜单以展开态出现
const desktopMql = window.matchMedia('(min-width: 769px)')
function onViewportChange(e: MediaQueryListEvent): void {
  if (e.matches) closeMenu()
}

// Esc 关闭菜单
function onKeydown(e: KeyboardEvent): void {
  if (e.key === 'Escape') closeMenu()
}

// 路由切换（含程序化跳转）自动收起菜单
watch(
  () => route.fullPath,
  () => closeMenu(),
)

onMounted(() => {
  desktopMql.addEventListener('change', onViewportChange)
  window.addEventListener('keydown', onKeydown)
})
onUnmounted(() => {
  desktopMql.removeEventListener('change', onViewportChange)
  window.removeEventListener('keydown', onKeydown)
})

async function onLogout(): Promise<void> {
  closeMenu()
  await auth.logout()
  message.success('已登出')
  router.replace(`/${GLOBAL_PREFIX}/login`)
}
</script>

<style scoped>
.topnav__links a {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.topnav__links a :deep(svg) {
  width: 15px;
  height: 15px;
}
.topnav__menu-btn {
  display: none;
}
.topnav__links--mobile {
  display: none;
}
.topnav__backdrop {
  position: fixed;
  inset: 0;
  z-index: 98;
  background: transparent;
}

@media (max-width: 768px) {
  /* 窄屏隐藏品牌标题：把空出的左侧位置让给桌面导航链接内联显示 */
  .topnav__brand {
    display: none;
  }
  /* 标题隐藏后右侧功能键保持靠右对齐 */
  .topnav__right {
    margin-left: auto;
  }

  /* 移动端隐藏汉堡按钮：链接已内联显示，不再需要下拉菜单 */
  .topnav__menu-btn {
    display: none !important;
  }

  /* 移动端隐藏下拉面板：导航链接直接内联到桌面导航块中 */
  .topnav__links--mobile {
    display: none !important;
  }

  /* 移动端直接内联显示桌面导航链接，占据标题空出的左侧位置；
     链接较多时允许横向滚动兜底（flex/nowrap/overflow 由 base 样式提供），不破坏布局 */
  .topnav__links--desktop {
    display: flex !important;
    gap: 2px;
  }
  .topnav__links--desktop a {
    white-space: nowrap;
    padding: 2px 6px;
    font-size: 13px;
  }

  .topnav__links--mobile a {
    padding: 8px 4px;
    border-radius: var(--radius-sm);
    color: var(--color-text-secondary);
    font-size: 14px;
  }
  .topnav__links--mobile a.router-link-active {
    color: var(--color-primary);
    font-weight: 600;
    background: var(--color-bg-hover);
  }
  .topnav__links--mobile a:hover {
    background: var(--color-bg-hover);
  }

  .topnav__mobile-meta {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: var(--space-xs);
    padding-top: var(--space-xs);
    border-top: 1px solid var(--color-border);
  }
}
</style>
